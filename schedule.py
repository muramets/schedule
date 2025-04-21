"""
Streamlit app: Daily schedule planner in Monkeytype‑style
Save as **app.py**.  Run with `streamlit run app.py` or deploy to Streamlit Cloud.
Dependencies (requirements.txt):
    streamlit==1.44.1
    streamlit-aggrid==0.3.4.post3
    pandas==2.2.3
Optionally add runtime.txt with `python‑3.11` for Cloud.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st
from datetime import datetime, date, timedelta
from pathlib import Path
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# ---------- CONSTANTS ----------
TOTAL_MINUTES = 12 * 60  # 12‑hour baseline for % column
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="Расписание — Monkeytype",
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
    cols = ["Start", "End", "Activity", "Comment", "Duration (min)", "% of 12h"]
    return pd.DataFrame(columns=cols)


def compute_metrics(df: pd.DataFrame) -> pd.DataFrame:
    def _calc(row):
        try:
            start = datetime.strptime(str(row["Start"]).strip(), "%H:%M")
            end = datetime.strptime(str(row["End"]).strip(), "%H:%M")
            dur = (end - start).seconds // 60
            perc = round(dur / TOTAL_MINUTES * 100, 1)
            return pd.Series({"Duration (min)": dur, "% of 12h": perc})
        except Exception:
            return pd.Series({"Duration (min)": None, "% of 12h": None})
    metrics = df.apply(_calc, axis=1)
    df.update(metrics)
    return df


def save_df(d: date, df: pd.DataFrame):
    compute_metrics(df)
    df.to_csv(_file_for(d), index=False)

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

# ---------- MAIN TABLE (AG‑GRID) ----------
# Button to add blank row
a_col, b_col = st.columns([1, 9])
if a_col.button("➕ Добавить строку"):
    blank = {c: "" for c in ["Start", "End", "Activity", "Comment"]}
    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([blank])], ignore_index=True)

builder = GridOptionsBuilder.from_dataframe(st.session_state.df)
builder.configure_default_column(editable=True, sortable=True, resizable=True)
# allow row drag + column reorder
builder.configure_grid_options(enableRowDragging=True)
# hide calc columns from editing
builder.configure_columns(["Duration (min)", "% of 12h"], editable=False)

grid = AgGrid(
    st.session_state.df,
    gridOptions=builder.build(),
    theme="streamlit",
    update_mode=GridUpdateMode.VALUE_CHANGED,
    allow_unsafe_jscode=True,
    fit_columns_on_grid_load=True,
)

# ---------- SAVE ----------
if b_col.button("💾 Сохранить", type="primary"):
    st.session_state.df = grid["data"]
    save_df(st.session_state.current_date, st.session_state.df)
    st.success("Сохранено!")
