"""
Schedule Helper - A MonkeyType-inspired schedule tracking app
"""
import pandas as pd
import streamlit as st
import altair as alt
from datetime import datetime, date, timedelta
import json
import os

# ---------------- CONSTANTS ----------------
TOTAL_MINUTES = 12 * 60  # 12-hour baseline
DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="Schedule Helper", page_icon="⏱️", layout="wide")

# ---------------- THEMES / CSS ----------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&display=swap');
    
    :root {
        --primary: #ff8f1f;
        --bg: #181818;
        --text: #e0e0e0;
        --row-bg: #1e1e1e;
        --row-hover: #252525;
        --header-bg: #232323;
        --border: #2b2b2b;
    }
    
    html, body, [class*="st-"] {
        background-color: var(--bg) !important;
        color: var(--text) !important;
        font-family: 'JetBrains Mono', monospace !important;
    }
    
    .stApp { 
        background-color: var(--bg) !important;
        padding-top: 0.5rem; 
    }
    
    .accent { 
        color: var(--primary); 
        font-weight: 600; 
    }
    
    /* Table styling */
    .stDataFrame table {
        background-color: var(--row-bg) !important;
        border-color: var(--border) !important;
    }
    
    .stDataFrame th {
        background-color: var(--header-bg) !important;
        color: var(--text) !important;
        font-weight: 600;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 150px;
    }
    
    .stDataFrame th:hover {
        overflow: visible;
        white-space: normal;
        height: auto;
    }
    
    .stDataFrame tr:nth-child(even) {
        background-color: var(--row-bg) !important;
    }
    
    .stDataFrame tr {
        transition: all 0.2s ease;
    }
    
    .stDataFrame tr:hover {
        background-color: var(--row-hover) !important;
    }
    
    /* Drag handle styling */
    .drag-handle {
        display: inline-block;
        width: 16px;
        height: 16px;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23e0e0e0' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='3' y1='12' x2='21' y2='12'%3E%3C/line%3E%3Cline x1='3' y1='6' x2='21' y2='6'%3E%3C/line%3E%3Cline x1='3' y1='18' x2='21' y2='18'%3E%3C/line%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: center;
        opacity: 0.5;
        cursor: move;
        margin-right: 8px;
        vertical-align: middle;
    }
    
    .drag-handle:hover {
        opacity: 1;
    }
    
    /* Delete button styling */
    .delete-btn {
        color: #ff5c5c !important;
        cursor: pointer;
        font-weight: bold;
        transition: all 0.2s ease;
    }
    
    .delete-btn:hover {
        color: #ff2e2e !important;
        transform: scale(1.1);
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: var(--bg);
    }
    
    ::-webkit-scrollbar-thumb {
        background: var(--primary);
        border-radius: 4px;
    }
    
    /* Animation for drag and drop */
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(255, 143, 31, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(255, 143, 31, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 143, 31, 0); }
    }
    
    .dragging {
        animation: pulse 1.5s infinite;
        position: relative;
        z-index: 10;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- HELPERS ----------------
def get_file_path(d):
    return os.path.join(DATA_DIR, f"{d.strftime('%Y-%m-%d')}.json")

def load_data(d):
    file_path = get_file_path(d)
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try:
                return pd.DataFrame(json.load(f))
            except:
                return create_empty_df()
    return create_empty_df()

def create_empty_df():
    return pd.DataFrame({
        "Start": pd.Series(dtype='str'),
        "End": pd.Series(dtype='str'),
        "Category": pd.Series(dtype='str'),
        "Activity": pd.Series(dtype='str'),
        "Comment": pd.Series(dtype='str'),
        "Duration (min)": pd.Series(dtype='float'),
        "% of 12h": pd.Series(dtype='float')
    })

def save_data(d, df):
    file_path = get_file_path(d)
    with open(file_path, 'w') as f:
        json.dump(df.to_dict('records'), f)

def calculate_metrics(df):
    if df is None or len(df) == 0:
        return create_empty_df()
    
    result_df = df.copy()
    
    for i, row in result_df.iterrows():
        try:
            start_time = str(row.get("Start", ""))
            end_time = str(row.get("End", ""))
            
            if start_time and end_time and start_time != "nan" and end_time != "nan":
                try:
                    start = datetime.strptime(start_time.strip(), "%H:%M")
                    end = datetime.strptime(end_time.strip(), "%H:%M")
                    
                    if end < start:
                        end += timedelta(days=1)
                    
                    duration_min = (end - start).seconds // 60
                    percent = round(duration_min / TOTAL_MINUTES * 100, 1)
                    
                    result_df.at[i, "Duration (min)"] = duration_min
                    result_df.at[i, "% of 12h"] = percent
                except:
                    result_df.at[i, "Duration (min)"] = 0.0
                    result_df.at[i, "% of 12h"] = 0.0
        except:
            result_df.at[i, "Duration (min)"] = 0.0
            result_df.at[i, "% of 12h"] = 0.0
    
    return result_df

# ---------------- INITIALIZE SESSION STATE ----------------
if "current_date" not in st.session_state:
    st.session_state.current_date = date.today()

if "chart_group" not in st.session_state:
    st.session_state.chart_group = "Category"

if "data" not in st.session_state:
    st.session_state.data = create_empty_df()

if "deleted_rows" not in st.session_state:
    st.session_state.deleted_rows = []

# ---------------- UI COMPONENTS ----------------
def date_navigation():
    col1, col2, col3 = st.columns([1, 5, 1])
    with col1:
        if st.button("⬅️", key="prev_day"):
            st.session_state.current_date -= timedelta(days=1)
            st.session_state.data = load_data(st.session_state.current_date)
    with col2:
        st.markdown(
            f"## <span class='accent'>{st.session_state.current_date.strftime('%d %B %Y')}</span>",
            unsafe_allow_html=True,
        )
    with col3:
        if st.button("➡️", key="next_day"):
            st.session_state.current_date += timedelta(days=1)
            st.session_state.data = load_data(st.session_state.current_date)
    st.divider()

def schedule_editor():
    st.markdown("### Schedule")
    
    # Add drag and drop functionality
    st.markdown("""
    <script src="https://cdn.jsdelivr.net/npm/sortablejs@1.14.0/Sortable.min.js"></script>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        const table = document.querySelector('.stDataFrame table tbody');
        if (table) {
            new Sortable(table, {
                animation: 150,
                handle: '.drag-handle',
                ghostClass: 'dragging',
                onEnd: function(evt) {
                    const rows = Array.from(table.querySelectorAll('tr'));
                    const oldIndex = evt.oldIndex;
                    const newIndex = evt.newIndex;
                    
                    // Send message to Streamlit with new order
                    const rowOrder = rows.map((_, idx) => idx);
                    [rowOrder[oldIndex], rowOrder[newIndex]] = [rowOrder[newIndex], rowOrder[oldIndex]];
                    
                    window.parent.postMessage({
                        isStreamlitMessage: true,
                        type: 'reorder_rows',
                        order: rowOrder
                    }, '*');
                }
            });
        }
    });
    </script>
    """, unsafe_allow_html=True)
    
    # Prepare data for editing
    edit_df = st.session_state.data.copy()
    if len(edit_df) == 0:
        edit_df = pd.DataFrame([{
            "Start": "", "End": "", "Category": "", "Activity": "", 
            "Comment": "", "Duration (min)": 0.0, "% of 12h": 0.0
        }])
    
    # Add drag handle column
    edit_df[''] = "⋮"
    
    # Configure columns
    column_config = {
        "": st.column_config.TextColumn("", disabled=True),
        "Start": st.column_config.TextColumn("Start", required=True),
        "End": st.column_config.TextColumn("End", required=True),
        "Category": st.column_config.TextColumn("Category", required=True),
        "Activity": st.column_config.TextColumn("Activity", required=True),
        "Comment": st.column_config.TextColumn("Comment"),
        "Duration (min)": st.column_config.NumberColumn("Duration (min)", disabled=True),
        "% of 12h": st.column_config.NumberColumn("% of 12h", disabled=True, format="%.1f%%")
    }
    
    # Display editor
    edited_df = st.data_editor(
        edit_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config=column_config,
        hide_index=True,
        key="data_editor"
    )
    
    # Remove drag handle column
    if '' in edited_df.columns:
        edited_df = edited_df.drop('', axis=1)
    
    # Update data if changed
    if not edited_df.equals(st.session_state.data):
        st.session_state.data = calculate_metrics(edited_df)
        st.rerun()

def action_buttons():
    col1, col2, col3 = st.columns([6, 1, 1])
    with col2:
        if st.button("🔄 Recalculate", key="recalc_btn"):
            st.session_state.data = calculate_metrics(st.session_state.data)
            st.rerun()
    with col3:
        if st.button("💾 Save", type="primary", key="save_btn"):
            save_data(st.session_state.current_date, st.session_state.data)
            st.success("Saved successfully!")

# ---------------- MAIN APP ----------------
date_navigation()
schedule_editor()
action_buttons()
st.divider()

# Charts and other components would go here...

# Handle row reordering from JavaScript
if st.session_state.get('reorder_rows'):
    new_order = st.session_state.reorder_rows.order
    df = st.session_state.data.copy()
    st.session_state.data = df.iloc[new_order].reset_index(drop=True)
    st.session_state.reorder_rows = None
    st.rerun()
