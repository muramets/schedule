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
# MonkeyType-dark global styles
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
        background-color: #181818 !important;
        padding-top: 0.5rem; 
    }
    
    .accent { 
        color: #ff8f1f; 
        font-weight: 600; 
    }
    
    /* Table styling */
    .stDataFrame table {
        background-color: #1e1e1e !important;
        border-color: #2b2b2b !important;
    }
    
    .stDataFrame th {
        background-color: #232323 !important;
        color: #e0e0e0 !important;
        font-weight: 600;
    }
    
    .stDataFrame tr:nth-child(even) {
        background-color: #202020 !important;
    }
    
    .stDataFrame tr:hover {
        background-color: #252525 !important;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #232323 !important;
        color: #e0e0e0 !important;
        border: 1px solid #2b2b2b !important;
    }
    
    .stButton > button:hover {
        background-color: #2b2b2b !important;
        border-color: #ff8f1f !important;
    }
    
    .stButton > button[data-baseweb="button"][kind="primary"] {
        background-color: #ff8f1f !important;
        color: #181818 !important;
    }
    
    /* Radio button styling */
    .stRadio [role="radiogroup"] {
        background-color: #232323 !important;
        padding: 0.5rem !important;
        border-radius: 4px !important;
    }
    
    /* Fix for text color in data editor */
    .streamlit-table td div {
        color: #e0e0e0 !important;
    }
    
    /* Custom toggle switch styling */
    .toggle-container {
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 1rem;
        background-color: #232323;
        border-radius: 4px;
        padding: 0.5rem;
    }
    
    .toggle-option {
        padding: 0.5rem 1rem;
        cursor: pointer;
        border-radius: 4px;
        margin: 0 0.25rem;
        transition: all 0.3s ease;
    }
    
    .toggle-option.active {
        background-color: #ff8f1f;
        color: #181818;
        font-weight: 600;
    }
    
    /* Other elements */
    .stDivider {
        background-color: #2b2b2b !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------- HELPERS ----------------
def get_file_path(d):
    """Get the file path for a specific date."""
    return os.path.join(DATA_DIR, f"{d.strftime('%Y-%m-%d')}.json")

def load_data(d):
    """Load data for a specific date."""
    file_path = get_file_path(d)
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
                df = pd.DataFrame(data)
                # Ensure all columns exist
                for col in ["Start", "End", "Category", "Activity", "Comment", "Duration (min)", "% of 12h"]:
                    if col not in df.columns:
                        df[col] = ""
                return df
            except:
                return create_empty_df()
    return create_empty_df()

def create_empty_df():
    """Create an empty dataframe with the correct columns."""
    return pd.DataFrame({
        "Start": [],
        "End": [],
        "Category": [],
        "Activity": [],
        "Comment": [],
        "Duration (min)": [],
        "% of 12h": []
    })

def save_data(d, df):
    """Save data for a specific date."""
    file_path = get_file_path(d)
    # Convert to records for JSON serialization
    df_dict = df.to_dict('records')
    with open(file_path, 'w') as f:
        json.dump(df_dict, f)

def calculate_metrics(df):
    """Calculate duration and percentage for each activity."""
    # Handle empty dataframe case
    if df is None or df.empty:
        return create_empty_df()
    
    # Make a copy to avoid changing during iteration
    result_df = df.copy()
    
    # Process each row
    for i, row in result_df.iterrows():
        # Check for valid start and end times
        start_time = row.get("Start", "")
        end_time = row.get("End", "")
        
        if start_time and end_time:
            try:
                # Parse times
                start = datetime.strptime(str(start_time).strip(), "%H:%M")
                end = datetime.strptime(str(end_time).strip(), "%H:%M")
                
                # Handle cases where end time is on the next day
                if end < start:
                    end = end + timedelta(days=1)
                
                # Calculate metrics
                duration_min = (end - start).seconds // 60
                percent = round(duration_min / TOTAL_MINUTES * 100, 1)
                
                # Update values in the dataframe
                result_df.at[i, "Duration (min)"] = duration_min
                result_df.at[i, "% of 12h"] = percent
            except Exception:
                # Skip invalid entries
                pass
    
    return result_df

def create_simple_pie_chart(df, group_field):
    """Create a simple pie chart that should work reliably."""
    # Create a safe copy for chart operations
    chart_df = df.copy() if not df.empty else create_empty_df()
    
    # Convert duration to numeric if it's not already
    chart_df["Duration (min)"] = pd.to_numeric(chart_df["Duration (min)"], errors='coerce')
    
    # Filter out rows with missing data
    valid_data = chart_df[chart_df[group_field].notna() & chart_df["Duration (min)"].notna()]
    valid_data = valid_data[valid_data[group_field] != ""]
    
    if len(valid_data) == 0:
        # Return an empty chart placeholder
        placeholder_df = pd.DataFrame({
            group_field: ["No data"],
            "Duration (min)": [100],
            "Percent": [100]
        })
        
        return alt.Chart(placeholder_df).mark_arc().encode(
            theta=alt.Theta(field="Duration (min)"),
            color=alt.value("#333333")
        ).properties(
            width=400,
            height=400,
            background="#181818"
        )
    
    # Aggregate data by the grouping field
    agg_data = valid_data.groupby(group_field)["Duration (min)"].sum().reset_index()
    agg_data["Percent"] = (agg_data["Duration (min)"] / TOTAL_MINUTES * 100).round(1)
    
    # Create chart
    chart = alt.Chart(agg_data).mark_arc().encode(
        theta=alt.Theta(field="Duration (min)"),
        color=alt.Color(field=group_field, scale=alt.Scale(scheme='tableau20')),
        tooltip=[
            alt.Tooltip(group_field),
            alt.Tooltip("Duration (min)", title="Minutes"),
            alt.Tooltip("Percent", title="% of 12h", format=".1f")
        ]
    ).properties(
        width=400,
        height=400,
        background="#181818"
    )
    
    return chart

# ---------------- INITIALIZE SESSION STATE ----------------
if "current_date" not in st.session_state:
    st.session_state.current_date = date.today()

if "chart_group" not in st.session_state:
    st.session_state.chart_group = "Category"

# Function to toggle chart group
def toggle_chart_group():
    st.session_state.chart_group = "Activity" if st.session_state.chart_group == "Category" else "Category"

# ---------------- DATE NAVIGATION ----------------
col1, col2, col3 = st.columns([1, 5, 1])

with col1:
    if st.button("⬅️", key="prev_day"):
        st.session_state.current_date -= timedelta(days=1)
        st.experimental_rerun()

with col2:
    st.markdown(
        f"## <span class='accent'>{st.session_state.current_date.strftime('%d %B %Y')}</span>",
        unsafe_allow_html=True,
    )

with col3:
    if st.button("➡️", key="next_day"):
        st.session_state.current_date += timedelta(days=1)
        st.experimental_rerun()

st.divider()

# ---------------- LOAD DATA ONLY AFTER DATE NAVIGATION ----------------
# This prevents issues with data loading and table resetting
if "data" not in st.session_state or "last_date" not in st.session_state or st.session_state.last_date != st.session_state.current_date:
    st.session_state.data = load_data(st.session_state.current_date)
    st.session_state.last_date = st.session_state.current_date

# ---------------- EDITABLE TABLE ----------------
st.markdown("### Schedule")

# Create a data editor with fixed schema to prevent issues
edited_df = st.data_editor(
    st.session_state.data,
    num_rows="dynamic",
    use_container_width=True,
    column_config={
        "Start": st.column_config.TextColumn("Start", help="Format: HH:MM"),
        "End": st.column_config.TextColumn("End", help="Format: HH:MM"),
        "Category": st.column_config.TextColumn("Category"),
        "Activity": st.column_config.TextColumn("Activity", help="What you did"),
        "Comment": st.column_config.TextColumn("Comment"),
        "Duration (min)": st.column_config.NumberColumn("Duration (min)", disabled=True),
        "% of 12h": st.column_config.NumberColumn("% of 12h", disabled=True, format="%.1f%%"),
    },
    hide_index=True
)

# Update the data in session state with calculated metrics
if edited_df is not None:
    st.session_state.data = calculate_metrics(edited_df)

# Add a recalculate button for user convenience
if st.button("🔄 Recalculate", key="recalc_btn"):
    st.session_state.data = calculate_metrics(st.session_state.data)
    st.experimental_rerun()

# ---------------- ACTION BUTTONS ----------------
col1, col2, col3 = st.columns([6, 1, 1])
with col3:
    if st.button("💾 Save", type="primary", key="save_btn"):
        save_data(st.session_state.current_date, st.session_state.data)
        st.success("Saved successfully!")

st.divider()

# ---------------- CHARTS ----------------
st.markdown("### Time Analysis")

# Create custom toggle for chart type
toggle_col1, toggle_col2, toggle_col3 = st.columns([1, 3, 1])
with toggle_col2:
    st.markdown(
        f"""
        <div class="toggle-container">
            <div class="toggle-option {'active' if st.session_state.chart_group == 'Category' else ''}" 
                 onclick="document.getElementById('toggle_btn').click()">
                Category
            </div>
            <div class="toggle-option {'active' if st.session_state.chart_group == 'Activity' else ''}"
                 onclick="document.getElementById('toggle_btn').click()">
                Activity
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Hidden button that will be triggered by the JavaScript onclick
    if st.button("Toggle", key="toggle_btn", help="Toggle between Category and Activity view"):
        toggle_chart_group()
        st.experimental_rerun()

# Create and display the chart
try:
    chart = create_simple_pie_chart(st.session_state.data, st.session_state.chart_group)
    st.altair_chart(chart, use_container_width=True)
except Exception as e:
    st.error(f"Error creating chart: {type(e).__name__}")
    st.info("Add valid schedule entries to see analytics.")
