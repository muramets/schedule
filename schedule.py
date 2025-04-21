"""
Schedule Helper — Streamlit app в стиле Monkeytype
===================================================
Сохрани как **app.py** и запусти `streamlit run app.py` или задеплой на Streamlit Cloud.

**requirements.txt**:
```
streamlit==1.44.1
streamlit‑aggrid==0.3.4.post3
pandas==2.2.3
altair==5.5.0
```
(в Cloud при желании добавь `runtime.txt` → `python-3.11`)
"""
from __future__ import annotations

import pandas as pd
import streamlit as st
import altair as alt
from datetime import datetime, date, timedelta
from pathlib import Path
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ---------- CONSTANTS ----------
TOTAL_MINUTES = 12 * 60  # 12‑hour baseline
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Schedule Helper",
    page_icon="⏱️",
    layout="wide",
)

# ---------- GLOBAL CSS (Monkeytype dark) ----------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap');
    html, body, [class*="st-"] {
        background-color: #181818 !important;
        color: #e0e0e0 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .stApp { padding-top: 0.5rem; }
    .accent { color: #ff8f1f; font-weight: 600; }
    /* Ag‑Grid overrides */
    .ag-theme-streamlit, .ag-root-wrapper { background-color: #1e1e1e !important; border-color: #2b2b2b !important; }
    .ag-header, .ag-header-cell-label { color: #e0e0e0 !important; font-weight: 600; }
    .ag-header-cell-label:hover { color: #ff8f1f !important; }
    .ag-row-even { background-color: #202020 !important; }
    .ag-row-hover { background-color: #252525 !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- HELPERS ----------

def _file_for(d: date) -> Path:
    return DATA_DIR / f"{d}.csv"


def load_df(d: date) -> pd.DataFrame:
    if _file_for(d).exists():
        return pd.read_csv(_file_for(d))
    cols = [
        "Start", "End", "Category", "Activity", "Comment", "Duration (min)", "% of 12h",
    ]
    return pd.DataFrame(columns=cols)


def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate *Duration (min)* and *% of 12h* for each row in‑place."""
    def _calc(row):
        try:
            start = datetime.strptime(str(row["Start"]).strip(), "%H:%M")
            end = datetime.strptime(str(row["End"]).strip(), "%H:%M")
            dur = (end - start).seconds // 60
            perc = round(dur / TOTAL_MINUTES * 100, 1)
            return pd.Series({"Duration (min)": dur, "% of 12h": perc})
        except Exception:
            return pd.Series({"Duration (min)": None, "% of 12h": None})

    df.update(df.apply(_calc, axis=1))
    return df


def save_df(d: date, df: pd.DataFrame):
    compute_metrics(df)
    df.to_csv(_file_for(d), index=False)


def make_pie(df: pd.DataFrame, group_field: str, title: str) -> alt.Chart:
    agg = df.dropna(subset=[group_field, "Duration (min)"]).groupby(group_field)["Duration (min)"].sum().reset_index()
    if agg.empty:
        agg = pd.DataFrame({group_field: [""], "Duration (min)": [0]})
    agg["Percent"] = agg["Duration (min)"] / TOTAL_MINUTES * 100
    return (
        alt.Chart(agg)
        .mark_arc()
        .encode(
            theta="Percent",
            color=f"{group_field}",
            tooltip=[group_field, "Percent"]
        )
        .properties(title=title)
    )

# ---------- SESSION STATE ----------
if "current_date" not in st.session_state:
    st.session_state.current_date = date.today()

if "df" not in st.session_state:
    st.session_state.df = load_df(st.session_state.current_date)

# ---------- HEADER WITH DATE NAVIGATION ----------
nav_cols = st.columns([1, 5, 1])
if nav_cols[0].button("←", key="prev_day"):
    st.session_state.current_date -= timedelta(days=1)
    st.session_state.df = load_df(st.session_state.current_date)

nav_cols[1].markdown(
    f"## <span class='accent'>{st.session_state.current_date.strftime('%d %B %Y')}</span>",
    unsafe_allow_html=True,
)

if nav_cols[2].button("→", key="next_day"):
    st.session_state.current_date += timedelta(days=1)
    st.session_state.df = load_df(st.session_state.current_date)

st.divider()

# ---------- MAIN TABLE ----------
compute_metrics(st.session_state.df)

builder = GridOptionsBuilder.from_dataframe(st.session_state.df)
builder.configure_default_column(editable=True, sortable=True, resizable=True)
builder.configure_grid_options(enableRowDragging=True, rowDragManaged=True)
# first column drag handle
builder.configure_column("Start", rowDrag=True)
# calc columns read‑only
builder.configure_columns(["Duration (min)", "% of 12h"], editable=False)

grid_response = AgGrid(
    st.session_state.df,
    gridOptions=builder.build(),
    theme="streamlit",
    update_mode=GridUpdateMode.VALUE_CHANGED,
    allow_unsafe_jscode=True,
    fit_columns_on_grid_load=True,
)

if grid_response["data"] is not None:
    st.session_state.df = compute_metrics(pd.DataFrame(grid_response["data"]))

# ---------- BUTTONS UNDER TABLE ----------
btn_cols = st.columns([8, 1, 2])
with btn_cols[1]:
    if st.button("➕ Добавить строку"):
        blank = {c: "" for c in ["Start", "End", "Category", "Activity", "Comment"]}
        st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([blank])], ignore_index=True)
        st.experimental_rerun()

with btn_cols[2]:
    if st.button("💾 Сохранить", type="primary"):
        save_df(st.session_state.current_date, st.session_state.df)
        st.success("Сохранено!")

# ---------- PIE CHARTS ----------
st.subheader("Разбивка времени")
chart_cols = st.columns(2)
with chart_cols[0]:
    st.altair_chart(make_pie(st.session_state.df, "Category", "По категориям"), use_container_width=True)
with chart_cols[1]:
    st.altair_chart(make_pie(st.session_state.df, "Activity", "По activity"), use_container_width=True)
