*(На Streamlit Cloud добавь `runtime.txt` → `python-3.11` при необходимости)*
"""
from __future__ import annotations

import pandas as pd
import streamlit as st
import altair as alt
from datetime import datetime, date, timedelta
from pathlib import Path
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

# ---------------- CONSTANTS ----------------
TOTAL_MINUTES = 12 * 60  # 12-hour baseline
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Schedule Helper", 
    page_icon="⏱️", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------- THEMES / CSS ----------------
# Monkeytype-dark global styles
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap');
    html, body, [class*="st-"] {
        background-color: #181818 !important;
        color: #e0e0e0 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .stApp { 
        background-color: #181818;
        padding-top: 0.5rem; 
    }
    .accent { color: #ff8f1f; font-weight: 600; }
    /* Ag-Grid */
    .ag-theme-streamlit, .ag-root-wrapper { 
        background-color: #1e1e1e !important; 
        border-color: #2b2b2b !important; 
    }
    .ag-header, .ag-header-cell-label { 
        color: #e0e0e0 !important; 
        font-weight: 600; 
    }
    .ag-header-cell-label:hover { 
        color: #ff8f1f !important; 
    }
    .ag-row-even { 
        background-color: #202020 !important; 
    }
    .ag-row-hover { 
        background-color: #252525 !important; 
    }
    /* Radio buttons */
    .st-eb {
        background-color: #252525 !important;
    }
    .st-bh {
        background-color: #ff8f1f !important;
    }
    /* Charts */
    .vega-embed {
        background-color: #181818 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Altair dark theme
def dark_theme():
    return {
        "config": {
            "view": {"stroke": "transparent"},
            "background": "#181818",
            "title": {
                "color": "#e0e0e0",
                "font": "JetBrains Mono",
                "fontWeight": 600
            },
            "legend": {
                "labelColor": "#e0e0e0",
                "titleColor": "#e0e0e0",
                "font": "JetBrains Mono"
            }
        }
    }

alt.themes.register('dark', dark_theme)
alt.themes.enable('dark')

# ---------------- HELPERS ----------------

def _file_for(d: date) -> Path:
    return DATA_DIR / f"{d}.csv"


def load_df(d: date) -> pd.DataFrame:
    if _file_for(d).exists():
        df = pd.read_csv(_file_for(d))
        # Ensure all required columns exist
        for col in ["Start", "End", "Category", "Activity", "Comment"]:
            if col not in df.columns:
                df[col] = ""
        if "Duration (min)" not in df.columns:
            df["Duration (min)"] = 0
        if "% of 12h" not in df.columns:
            df["% of 12h"] = 0.0
        return df
    
    return pd.DataFrame(columns=[
        "Start", "End", "Category", "Activity", "Comment", 
        "Duration (min)", "% of 12h"
    ])


def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Recalculate duration + percent in-place and return df."""
    def _calc(row):
        try:
            start = datetime.strptime(str(row["Start"]).strip(), "%H:%M")
            end = datetime.strptime(str(row["End"]).strip(), "%H:%M")
            dur = (end - start).seconds // 60
            perc = round(dur / TOTAL_MINUTES * 100, 1)
            return pd.Series({"Duration (min)": dur, "% of 12h": perc})
        except Exception:
            return pd.Series({"Duration (min)": 0, "% of 12h": 0.0})

    metrics = df.apply(_calc, axis=1)
    df["Duration (min)"] = metrics["Duration (min)"]
    df["% of 12h"] = metrics["% of 12h"]
    return df


def save_df(d: date, df: pd.DataFrame):
    compute_metrics(df)
    df.to_csv(_file_for(d), index=False)


def make_pie(df: pd.DataFrame, group_field: str) -> alt.Chart:
    agg = (
        df.dropna(subset=[group_field, "Duration (min)"])
        .groupby(group_field)["Duration (min)"]
        .sum()
        .reset_index()
    )
    
    if agg.empty or agg["Duration (min)"].sum() == 0:
        agg = pd.DataFrame({group_field: ["No data"], "Duration (min)": [1]})
    
    agg["Percent"] = agg["Duration (min)"] / agg["Duration (min)"].sum() * 100
    
    base = alt.Chart(agg).encode(
        theta=alt.Theta("Percent:Q", stack=True),
        color=alt.Color(f"{group_field}:N", legend=alt.Legend(title=group_field)),
        tooltip=[
            alt.Tooltip(f"{group_field}:N", title="Category"),
            alt.Tooltip("Duration (min):Q", title="Minutes"),
            alt.Tooltip("Percent:Q", format=".1f", title="Percentage")
        ]
    )
    
    pie = base.mark_arc(outerRadius=120, innerRadius=50)
    text = base.mark_text(radius=180, size=12).encode(text=f"{group_field}:N")
    
    return (pie + text).properties(
        width=400,
        height=400,
        title=f"Time by {group_field}"
    )

# ---------------- SESSION STATE ----------------
if "current_date" not in st.session_state:
    st.session_state.current_date = date.today()

if "df" not in st.session_state:
    st.session_state.df = load_df(st.session_state.current_date)

# ---------------- HEADER (date nav) ----------------
nav_cols = st.columns([1, 5, 1])
with nav_cols[0]:
    if st.button("← Previous", use_container_width=True):
        st.session_state.current_date -= timedelta(days=1)
        st.session_state.df = load_df(st.session_state.current_date)
        st.rerun()

nav_cols[1].markdown(
    f"## <span class='accent'>{st.session_state.current_date.strftime('%d %B %Y')}</span>",
    unsafe_allow_html=True,
)

with nav_cols[2]:
    if st.button("Next →", use_container_width=True):
        st.session_state.current_date += timedelta(days=1)
        st.session_state.df = load_df(st.session_state.current_date)
        st.rerun()

st.divider()

# ---------------- TABLE ----------------
compute_metrics(st.session_state.df)

# Configure grid
builder = GridOptionsBuilder.from_dataframe(st.session_state.df)
builder.configure_default_column(
    editable=True, 
    sortable=True, 
    resizable=True,
    filterable=True
)

# Enable row dragging
builder.configure_grid_options(
    enableRowDrag=True,
    rowDragManaged=True,
    animateRows=True
)

# Make sure metrics columns are not editable
builder.configure_columns(["Duration (min)", "% of 12h"], editable=False)

# Add custom cell editor for time fields
time_editor = JsCode("""
    function(params) {
        if (!params.value) return '';
        return params.value.length === 5 ? params.value : '';
    }
""")

builder.configure_column("Start", cellEditor=time_editor)
builder.configure_column("End", cellEditor=time_editor)

grid = AgGrid(
    st.session_state.df,
    gridOptions=builder.build(),
    update_mode=GridUpdateMode.VALUE_CHANGED | GridUpdateMode.MODEL_CHANGED,
    theme="streamlit",
    allow_unsafe_jscode=True,
    fit_columns_on_grid_load=True,
    height=500,
    reload_data=True
)

# Update dataframe if changed
if grid["data"] is not None:
    st.session_state.df = compute_metrics(pd.DataFrame(grid["data"]))

# ---------------- BUTTONS ----------------
btn_cols = st.columns([8, 1, 2])
with btn_cols[1]:
    if st.button("➕ Add Row", use_container_width=True):
        blank_row = {
            "Start": "",
            "End": "",
            "Category": "",
            "Activity": "",
            "Comment": "",
            "Duration (min)": 0,
            "% of 12h": 0.0
        }
        st.session_state.df = pd.concat([
            st.session_state.df,
            pd.DataFrame([blank_row])
        ], ignore_index=True)
        st.rerun()

with btn_cols[2]:
    if st.button("💾 Save", type="primary", use_container_width=True):
        save_df(st.session_state.current_date, st.session_state.df)
        st.toast("Schedule saved!", icon="✅")

# ---------------- PIE CHART ----------------
st.subheader("Time Distribution")

# Filter out empty categories/activities
valid_df = st.session_state.df[
    (st.session_state.df["Category"].notna()) & 
    (st.session_state.df["Category"] != "") &
    (st.session_state.df["Duration (min)"] > 0)
]

if not valid_df.empty:
    tab1, tab2 = st.tabs(["By Category", "By Activity"])
    
    with tab1:
        st.altair_chart(
            make_pie(valid_df, "Category"), 
            use_container_width=True
        )
    
    with tab2:
        st.altair_chart(
            make_pie(valid_df, "Activity"), 
            use_container_width=True
        )
else:
    st.info("No activities with duration to display")
