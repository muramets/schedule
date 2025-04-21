"""
Schedule Helper - обновлённая версия
------------------------------------
Python ≥3.9 | streamlit ≥1.31 | streamlit‑aggrid ≥0.3.4
"""

import os
import json
from datetime import datetime, date, timedelta

import altair as alt
import pandas as pd
import streamlit as st
from st_aggrid import (
    AgGrid,
    GridOptionsBuilder,
    GridUpdateMode,
    DataReturnMode,
)

# ---------- КОНСТАНТЫ ----------
TOTAL_MINUTES = 12 * 60          # 12‑часовой базовый интервал
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ---------- НАСТРОЙКА СТРАНИЦЫ ----------
st.set_page_config("Schedule Helper", "⏱️", layout="wide")

# ---------- CSS (убрали tooltip заголовков) ----------
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap');

html, body, [class*="st-"] {background:#181818 !important;color:#e0e0e0 !important;font-family:'JetBrains Mono',monospace !important;}
.stApp {padding-top:.5rem}
.accent {color:#ff8f1f;font-weight:600}

/* Ag‑Grid dark */
.ag-theme-balham-dark {--ag-foreground-color:#e0e0e0;--ag-background-color:#1e1e1e;--ag-header-background-color:#232323;--ag-header-foreground-color:#e0e0e0;}
.ag-header-cell-label {font-weight:600}
.ag-row-hover {background:#252525!important}

/* убираем стандартный tooltip Glide DataGrid */
div[role="columnheader"] > div[title] {pointer-events:none}
</style>
    """,
    unsafe_allow_html=True,
)

# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
def _file_path(d: date) -> str:
    return os.path.join(DATA_DIR, f"{d:%Y-%m-%d}.json")

def _empty_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Start": pd.Series(dtype=str),
            "End": pd.Series(dtype=str),
            "Category": pd.Series(dtype=str),
            "Activity": pd.Series(dtype=str),
            "Comment": pd.Series(dtype=str),
            "Duration (min)": pd.Series(dtype=float),
            "% of 12h": pd.Series(dtype=float),
        }
    )

def load_data(d: date) -> pd.DataFrame:
    f = _file_path(d)
    if not os.path.exists(f):
        return _empty_df()

    try:
        df = pd.DataFrame(json.load(open(f)))
    except Exception:
        return _empty_df()

    # приведение типов + отсутствующие столбцы
    need = {
        "Start": str,
        "End": str,
        "Category": str,
        "Activity": str,
        "Comment": str,
        "Duration (min)": float,
        "% of 12h": float,
    }
    for col, typ in need.items():
        if col not in df:
            df[col] = pd.Series(dtype=typ)
        else:
            df[col] = df[col].astype(typ)

    return df

def save_data(d: date, df: pd.DataFrame):
    df.to_json(_file_path(d), orient="records", indent=2)

def calc_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    for i, row in df.iterrows():
        try:
            s, e = row["Start"].strip(), row["End"].strip()
            if not s or not e:
                continue

            start = datetime.strptime(s, "%H:%M")
            end = datetime.strptime(e, "%H:%M")
            if end < start:
                end += timedelta(days=1)

            mins = (end - start).seconds // 60
            df.at[i, "Duration (min)"] = mins
            df.at[i, "% of 12h"] = round(mins / TOTAL_MINUTES * 100, 1)
        except Exception:
            df.at[i, "Duration (min)"] = 0.0
            df.at[i, "% of 12h"] = 0.0
    return df

def pie(df: pd.DataFrame, group: str):
    if df.empty:
        return alt.Chart(pd.DataFrame({"v":[1],"l":["Нет данных"]})
        ).mark_arc().encode(theta="v",color=alt.value("#333")).properties(width=400,height=400,background="#181818")

    tmp = df.groupby(group)["Duration (min)"].sum().reset_index()
    tmp["Percent"] = (tmp["Duration (min)"] / TOTAL_MINUTES * 100).round(1)
    return (
        alt.Chart(tmp)
        .mark_arc()
        .encode(
            theta="Duration (min)",
            color=alt.Color(group, scale=alt.Scale(scheme="tableau20")),
            tooltip=[group, "Duration (min)", alt.Tooltip("Percent", format=".1f")],
        )
        .properties(width=400, height=400, background="#181818")
    )

# ---------- СЕССИЯ ----------
ss = st.session_state
ss.setdefault("current_date", date.today())
ss.setdefault("chart_group", "Category")

# ---------- НАВИГАЦИЯ ПО ДНЯМ ----------
l, c, r = st.columns([1, 5, 1])
with l:
    if st.button("⬅️"):
        ss.current_date -= timedelta(days=1)
with c:
    st.markdown(f"## <span class='accent'>{ss.current_date:%d %B %Y}</span>", unsafe_allow_html=True)
with r:
    if st.button("➡️"):
        ss.current_date += timedelta(days=1)

st.divider()

# ---------- ЗАГРУЗКА ДАННЫХ ----------
if "data" not in ss or ss.get("reload", True):
    ss.data = calc_metrics(load_data(ss.current_date))
    ss.reload = False

df = ss.data.copy()          # рабочая копия
df.reset_index(drop=True, inplace=True)

# ----- Ag‑Grid: настройка -----
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(editable=True, sortable=True, filter=True, resizable=True)

# столбцы, которые нельзя править
for col in ("Duration (min)", "% of 12h"):
    gb.configure_column(col, editable=False)

# drag‑handle для строк
gb.configure_grid_options(rowDragManaged=True, animateRows=True)
gb.configure_column(
    "Drag",  # искусственный столбец
    header_name="⇅",
    width=40,
    rowDrag=True,
    editable=False,
    suppressSizeToFit=True,
)
# добавляем сам столбец‑пустышку
df.insert(0, "Drag", [""] * len(df))

# выбор строк чекбоксами для удаления
gb.configure_selection("multiple", use_checkbox=True)
grid_opt = gb.build()

# ----- отображаем таблицу -----
grid = AgGrid(
    df,
    gridOptions=grid_opt,
    theme="balham-dark",
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    update_mode=GridUpdateMode.MODEL_CHANGED,
    fit_columns_on_grid_load=True,
    allow_unsafe_jscode=True,
)

edited = grid["data"].drop(columns=["Drag"])
selected = pd.DataFrame(grid["selected_rows"]).drop(columns=["Drag"], errors="ignore")

# ----- кнопки действий ----------
actions_col1, actions_col2, actions_col3 = st.columns([4, 1, 1])
with actions_col2:
    if st.button("➕ Добавить строку"):
        edited.loc[len(edited)] = [""] * 5 + [0.0, 0.0]  # 5 текстовых + 2 числовых
with actions_col3:
    if st.button("🗑️ Удалить выбранные", disabled=selected.empty):
        edited = edited.merge(selected.drop_duplicates(), how="left", indicator=True)
        edited = edited[edited["_merge"] == "left_only"].drop(columns="_merge")

# ----- если что‑то поменялось – пересчёт -----
if not edited.equals(ss.data):
    ss.data = calc_metrics(edited)
    st.experimental_rerun()

# ----- сохранить -----
if st.button("💾 Сохранить", type="primary"):
    save_data(ss.current_date, ss.data)
    st.success("Сохранено!")

st.divider()

# ---------- график ----------
tog1, tog2, tog3 = st.columns([1, 3, 1])
with tog2:
    if st.button(
        f"Переключить: «{ss.chart_group}»",
        help="Нажмите, чтобы показать процент по Activity / Category",
    ):
        ss.chart_group = "Activity" if ss.chart_group == "Category" else "Category"

st.altair_chart(pie(ss.data, ss.chart_group), use_container_width=True)
