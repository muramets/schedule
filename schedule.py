"""
Schedule Helper - A MonkeyType-inspired schedule tracking app
"""
import pandas as pd
import streamlit as st
import altair as alt
from datetime import datetime, date, timedelta
from pathlib import Path
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
                return pd.DataFrame(json.load(f))
            except:
                return create_empty_df()
    return create_empty_df()

def create_empty_df():
    """Create an empty dataframe with the correct columns."""
    return pd.DataFrame(columns=["Start", "End", "Category", "Activity", "Comment", "Duration (min)", "% of 12h"])

def save_data(d, df):
    """Save data for a specific date."""
    file_path = get_file_path(d)
    # Convert to records for JSON serialization
    df_dict = df.to_dict('records')
    with open(file_path, 'w') as f:
        json.dump(df_dict, f)

def calculate_metrics(df):
    """Calculate duration and percentage for each activity."""
    if len(df) == 0:
        return df
    
    for i, row in df.iterrows():
        try:
            if pd.notna(row["Start"]) and pd.notna(row["End"]):
                start = datetime.strptime(str(row["Start"]).strip(), "%H:%M")
                end = datetime.strptime(str(row["End"]).strip(), "%H:%M")
                
                # Handle cases where end time is on the next day
                if end < start:
                    end = end + timedelta(days=1)
                
                duration_min = (end - start).seconds // 60
                percent = round(duration_min / TOTAL_MINUTES * 100, 1)
                
                df.at[i, "Duration (min)"] = duration_min
                df.at[i, "% of 12h"] = percent
        except Exception as e:
            pass
    
    return df

def create_pie_chart(df, group_field):
    """Create a pie chart based on the specified grouping field."""
    # Filter and aggregate data
    valid_data = df.dropna(subset=[group_field, "Duration (min)"])
    if not valid_data.empty:
        agg_data = valid_data.groupby(group_field)["Duration (min)"].sum().reset_index()
        agg_data["Percent"] = (agg_data["Duration (min)"] / TOTAL_MINUTES * 100).round(1)
        agg_data["Label"] = agg_data.apply(lambda x: f"{x[group_field]}: {x['Percent']}%", axis=1)
        
        # Create the chart
        chart = alt.Chart(agg_data).mark_arc(innerRadius=50, outerRadius=120).encode(
            theta=alt.Theta(field="Duration (min)", type="quantitative"),
            color=alt.Color(field=group_field, type="nominal", legend=None),
            tooltip=[
                alt.Tooltip(group_field), 
                alt.Tooltip("Duration (min)", title="Minutes"),
                alt.Tooltip("Percent", title="% of 12h")
            ]
        ).properties(
            width=400,
            height=400,
            background="#181818"
        )
        
        # Add text labels
        text = chart.mark_text(radius=140, fontSize=12).encode(
            text="Label"
        )
        
        return chart + text
    else:
        # Empty dataframe, return empty chart
        empty_df = pd.DataFrame({group_field: ["No Data"], "Duration (min)": [1], "Percent": [100]})
        return alt.Chart(empty_df).mark_arc(innerRadius=50, outerRadius=120).encode(
            theta=alt.Theta(field="Duration (min)", type="quantitative"),
            color=alt.value("#333333"),
            tooltip=[alt.Tooltip(group_field)]
        ).properties(
            width=400,
            height=400,
            background="#181818"
        )

# ---------------- SESSION STATE SETUP ----------------
if "current_date" not in st.session_state:
    st.session_state.current_date = date.today()

if "data" not in st.session_state:
    st.session_state.data = load_data(st.session_state.current_date)

# ---------------- DATE NAVIGATION ----------------
col1, col2, col3 = st.columns([1, 5, 1])

with col1:
    if st.button("⬅️"):
        st.session_state.current_date -= timedelta(days=1)
        st.session_state.data = load_data(st.session_state.current_date)
        st.rerun()

with col2:
    st.markdown(
        f"## <span class='accent'>{st.session_state.current_date.strftime('%d %B %Y')}</span>",
        unsafe_allow_html=True,
    )

with col3:
    if st.button("➡️"):
        st.session_state.current_date += timedelta(days=1)
        st.session_state.data = load_data(st.session_state.current_date)
        st.rerun()

st.divider()

# ---------------- EDITABLE TABLE ----------------
st.markdown("### Schedule")

# Create a placeholder for the edited dataframe
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
    hide_index=True,
)

# Calculate metrics when the data has changed
if not edited_df.equals(st.session_state.data):
    st.session_state.data = calculate_metrics(edited_df)

# ---------------- ACTION BUTTONS ----------------
col1, col2, col3 = st.columns([6, 1, 1])
with col3:
    if st.button("💾 Save", type="primary"):
        save_data(st.session_state.current_date, st.session_state.data)
        st.success("Saved successfully!")

st.divider()

# ---------------- CHARTS ----------------
st.markdown("### Time Analysis")

# Chart type selector
chart_type = st.radio(
    "Group by:",
    options=["Category", "Activity"],
    horizontal=True
)

# Create and display the chart
if not st.session_state.data.empty:
    chart = create_pie_chart(st.session_state.data, chart_type)
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("Add some schedule entries to see analytics.")
