"""
Streamlit app: Daily schedule planner in Monkeytype‑inspired dark theme.
Save this file as **app.py** and push to your Streamlit Cloud repo.
Run locally:  streamlit run app.py

Requires:
    pip install streamlit pandas streamlit-aggrid
"""
from __future__ import annotations

import pandas as pd
import streamlit as st
from datetime import datetime, date
from pathlib import Path
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ---------- CONFIG ----------
TOTAL_MINUTES = 12 * 60  # 12‑hour baseline for % column
DATA_DIR = Path("data")  # folder where CSVs are stored (auto‑created)
DATA_DIR.mkdir(exist_ok=True)

st.set_page_config(
    page_title="Расписание (Monkeytype style)",
    page_icon="⏱️",
    layout="wide",
)

# ---------- GLOBAL CSS (Monkeytype dark) ----------
st.markdown(
    """
    <style>
    /* Import JetBrains Mono */
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap');

    html, body, [class*="st-"], .ag-theme-streamlit {
        background-color: #181818 !important;
        color: #e0e0e0 !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    .stApp { padding: 0 1rem; }

    /* Accent color */
    .accent { color: #ff8f1f; }
    .ag-header, .ag-root-wrapper, .ag-theme-streamlit {
        background-color: #1e1e1e !important;
        border-color: #2b2b2b !important;
    }
    .ag-row-even { background-color: #202020 !important; }
    .ag-row-hover { background-color: #252525 !important; }
    .ag-header-cell-label { color: #e0e0e0 !important; font-weight: 600; }
    .ag-header-cell-label:hover { color: #ff8f1f !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- HELPERS ----------

def load_today_df() -> pd.DataFrame:
    """Load today's CSV or blank DataFrame."""
    today_file = DATA_DIR / f"{date.today()}.csv"
    if today_file.exists():
        return pd.read_csv(today_file)
    cols = [
        "Start", "End", "Activity", "Comment", "Duration (min)", "% of 12h",
    ]
    return pd.DataFrame(columns=cols)


def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate Duration + % columns from Start / End."""
    def _calc(row):
        try:
            start = datetime.strptime(row["Start"], "%H:%M")
            end = datetime.strptime(row["End"], "%H:%M")
            dur = (end - start).seconds // 60  # in minutes
            perc = round(dur / TOTAL_MINUTES * 100, 1)
            return pd.Series({"Duration (min)": dur, "% of 12h": perc})
        except Exception:
            return pd.Series({"Duration (min)": None, "% of 12h": None})

    metrics = df.apply(_calc, axis=1)
    df.update(metrics)
    return df


def save_df(df: pd.DataFrame) -> None:
    """Persist today's schedule to a dated CSV."""
    today_file = DATA_DIR / f"{date.today()}.csv"
    df.to_csv(today_file, index=False)


# ---------- UI ----------
st.markdown("# <span class='accent'>Сегодняшнее расписание</span>", unsafe_allow_html=True)

# Load / session state
if "df" not in st.session_state:
    st.session_state.df = load_today_df()

# Build AgGrid options for editable, sortable, draggable table
builder = GridOptionsBuilder.from_dataframe(st.session_state.df)
# enable features
builder.configure_default_column(editable=True, sortable=True, resizable=True)
builder.configure_grid_options(enableRowDragging=True)
builder.configure_grid_options(enableRangeSelection=True)
# allow column reorder by drag (default true in AgGrid)

grid_options = builder.build()

# Display editable grid
ag_ret = AgGrid(
    st.session_state.df,
    gridOptions=grid_options,
    theme="streamlit",  # inherits our custom CSS overrides
    update_mode=GridUpdateMode.VALUE_CHANGED,
    allow_unsafe_jscode=True,
    fit_columns_on_grid_load=True,
)

edited_df = ag_ret["data"]

# Auto‑recalculate Duration / % after edits
edited_df = compute_metrics(edited_df)

# Save button + instant feedback
cols = st.columns([1, 4, 1])
if cols[1].button("💾 Сохранить изменения", type="primary"):
    save_df(edited_df)
    st.session_state.df = edited_df
    st.success("Данные сохранены!")

# Optionally show raw dataframe below
with st.expander("🔍 Посмотреть данные как DataFrame"):
    st.dataframe(edited_df, use_container_width=True)
