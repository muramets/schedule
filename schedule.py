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
    
    /* Sorting indicators */
    .sortable-header {
        cursor: pointer;
        position: relative;
        padding-right: 20px !important;
    }
    
    .sortable-header:after {
        content: "⇅";
        position: absolute;
        right: 5px;
        top: 50%;
        transform: translateY(-50%);
        opacity: 0.5;
    }
    
    .sortable-header.asc:after {
        content: "↑";
        opacity: 1;
    }
    
    .sortable-header.desc:after {
        content: "↓";
        opacity: 1;
    }
    
    /* Drag and drop rows */
    .draggable-row {
        cursor: move;
    }
    
    .draggable-row:hover {
        background-color: #2b2b2b !important;
    }
    
    .drag-handle {
        cursor: move;
        width: 16px;
        height: 16px;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23e0e0e0' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='3' y1='12' x2='21' y2='12'%3E%3C/line%3E%3Cline x1='3' y1='6' x2='21' y2='6'%3E%3C/line%3E%3Cline x1='3' y1='18' x2='21' y2='18'%3E%3C/line%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: center;
        opacity: 0.5;
    }
    
    .drag-handle:hover {
        opacity: 1;
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
                # Create DataFrame with explicit data types to prevent issues
                df = pd.DataFrame(data)
                
                # Ensure all columns exist with correct types
                required_columns = {
                    "Start": str,
                    "End": str,
                    "Category": str,
                    "Activity": str,
                    "Comment": str,
                    "Duration (min)": float,
                    "% of 12h": float
                }
                
                for col, dtype in required_columns.items():
                    if col not in df.columns:
                        df[col] = pd.Series(dtype=dtype)
                    else:
                        df[col] = df[col].astype(dtype)
                
                return df
            except:
                return create_empty_df()
    return create_empty_df()

def create_empty_df():
    """Create an empty dataframe with the correct columns."""
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
    """Save data for a specific date."""
    file_path = get_file_path(d)
    # Convert to records for JSON serialization
    df_dict = df.to_dict('records')
    with open(file_path, 'w') as f:
        json.dump(df_dict, f)

def calculate_metrics(df):
    """Calculate duration and percentage for each activity."""
    # Handle empty dataframe case
    if df is None or len(df) == 0:
        return create_empty_df()
    
    # Make a copy to avoid changing during iteration
    result_df = df.copy()
    
    # Process each row
    for i, row in result_df.iterrows():
        # Check for valid start and end times
        try:
            start_time = str(row.get("Start", ""))
            end_time = str(row.get("End", ""))
            
            if start_time and end_time and start_time != "nan" and end_time != "nan":
                try:
                    # Parse times
                    start = datetime.strptime(start_time.strip(), "%H:%M")
                    end = datetime.strptime(end_time.strip(), "%H:%M")
                    
                    # Handle cases where end time is on the next day
                    if end < start:
                        end = end + timedelta(days=1)
                    
                    # Calculate metrics
                    duration_min = (end - start).seconds // 60
                    percent = round(duration_min / TOTAL_MINUTES * 100, 1)
                    
                    # Update values in the dataframe
                    result_df.at[i, "Duration (min)"] = duration_min
                    result_df.at[i, "% of 12h"] = percent
                except:
                    # Skip invalid entries
                    result_df.at[i, "Duration (min)"] = 0.0
                    result_df.at[i, "% of 12h"] = 0.0
        except:
            # Skip problematic rows
            result_df.at[i, "Duration (min)"] = 0.0
            result_df.at[i, "% of 12h"] = 0.0
    
    return result_df

def create_simple_pie_chart(df, group_field):
    """Create a simple pie chart that should work reliably."""
    if df is None or len(df) == 0:
        # Return an empty chart placeholder
        placeholder_df = pd.DataFrame({
            "label": ["No data"],
            "value": [100]
        })
        
        return alt.Chart(placeholder_df).mark_arc().encode(
            theta=alt.Theta(field="value"),
            color=alt.value("#333333")
        ).properties(
            width=400,
            height=400,
            background="#181818"
        )
    
    # Create a safe copy for chart operations
    chart_df = df.copy()
    
    # Convert duration to numeric 
    chart_df["Duration (min)"] = pd.to_numeric(chart_df["Duration (min)"], errors='coerce')
    
    # Filter out rows with missing data
    valid_data = chart_df[chart_df[group_field].notna() & chart_df["Duration (min)"].notna()]
    valid_data = valid_data[valid_data[group_field].astype(str) != ""]
    valid_data = valid_data[valid_data[group_field].astype(str) != "nan"]
    
    if len(valid_data) == 0:
        # Return an empty chart placeholder
        placeholder_df = pd.DataFrame({
            "label": ["No data"],
            "value": [100]
        })
        
        return alt.Chart(placeholder_df).mark_arc().encode(
            theta=alt.Theta(field="value"),
            color=alt.value("#333333")
        ).properties(
            width=400,
            height=400,
            background="#181818"
        )
    
    # Aggregate data by the grouping field
    try:
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
    except:
        # Return a fallback chart on error
        placeholder_df = pd.DataFrame({
            "label": ["Error in data"],
            "value": [100]
        })
        
        return alt.Chart(placeholder_df).mark_arc().encode(
            theta=alt.Theta(field="value"),
            color=alt.value("#333333")
        ).properties(
            width=400,
            height=400,
            background="#181818"
        )

# ---------------- INITIALIZE SESSION STATE ----------------
if "current_date" not in st.session_state:
    st.session_state.current_date = date.today()

if "chart_group" not in st.session_state:
    st.session_state.chart_group = "Category"

if "sort_column" not in st.session_state:
    st.session_state.sort_column = None
    st.session_state.sort_ascending = True

if "dragged_row" not in st.session_state:
    st.session_state.dragged_row = None

# Function to toggle chart group
def toggle_chart_group():
    st.session_state.chart_group = "Activity" if st.session_state.chart_group == "Category" else "Category"

# Function to handle sorting
def handle_sort(column):
    if st.session_state.sort_column == column:
        # Toggle direction if same column clicked
        st.session_state.sort_ascending = not st.session_state.sort_ascending
    else:
        # New column, default to ascending
        st.session_state.sort_column = column
        st.session_state.sort_ascending = True
    st.rerun()

# Function to handle row reordering
def handle_row_reorder(dragged_index, target_index):
    if dragged_index is not None and target_index is not None:
        df = st.session_state["data"].copy()
        row = df.iloc[dragged_index].copy()
        df = df.drop(dragged_index).reset_index(drop=True)
        df.loc[target_index] = row
        df = df.sort_index().reset_index(drop=True)
        st.session_state["data"] = df
        st.rerun()

# ---------------- DATE NAVIGATION ----------------
col1, col2, col3 = st.columns([1, 5, 1])

with col1:
    if st.button("⬅️", key="prev_day"):
        st.session_state.current_date -= timedelta(days=1)
        st.session_state["data_needs_reload"] = True

with col2:
    st.markdown(
        f"## <span class='accent'>{st.session_state.current_date.strftime('%d %B %Y')}</span>",
        unsafe_allow_html=True,
    )

with col3:
    if st.button("➡️", key="next_day"):
        st.session_state.current_date += timedelta(days=1)
        st.session_state["data_needs_reload"] = True

st.divider()

# ---------------- LOAD DATA ----------------
# Load data for the current date
if "data" not in st.session_state or st.session_state.get("data_needs_reload", True):
    loaded_data = load_data(st.session_state.current_date)
    st.session_state["data"] = calculate_metrics(loaded_data)
    st.session_state["data_needs_reload"] = False

# ---------------- EDITABLE TABLE ----------------
st.markdown("### Schedule")

try:
    # Create a base dataframe for editing
    if len(st.session_state["data"]) == 0:
        # Start with one empty row
        edit_df = pd.DataFrame([{
            "Start": "",
            "End": "",
            "Category": "",
            "Activity": "",
            "Comment": "",
            "Duration (min)": 0.0,
            "% of 12h": 0.0
        }])
    else:
        edit_df = st.session_state["data"].copy()
    
    # Apply sorting if specified
    if st.session_state.sort_column:
        edit_df = edit_df.sort_values(
            by=st.session_state.sort_column,
            ascending=st.session_state.sort_ascending
        )
    
    # Add index column for drag and drop
    edit_df[''] = "⋮⋮"  # Drag handle
    
    # Reorder columns to put drag handle first
    cols = [''] + [col for col in edit_df.columns if col != '']
    edit_df = edit_df[cols]
    
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
    
    # Simple data editor with minimal configuration
    edited_df = st.data_editor(
        edit_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config=column_config,
        hide_index=True,
        key="data_editor"
    )
    
    # Remove drag handle column before saving
    if '' in edited_df.columns:
        edited_df = edited_df.drop('', axis=1)
    
    # Immediately calculate metrics when data changes
    if not edited_df.equals(st.session_state.get("last_edited_df", None)):
        st.session_state["data"] = calculate_metrics(edited_df)
        st.session_state["last_edited_df"] = edited_df.copy()
        st.rerun()
        
except Exception as e:
    st.error(f"Error displaying data editor: {str(e)}")
    st.session_state["data"] = create_empty_df()

# Add JavaScript for sorting and drag and drop
st.markdown("""
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.14.0/Sortable.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {
    // Sorting functionality
    const headers = document.querySelectorAll('.stDataFrame th');
    headers.forEach(header => {
        if (header.textContent.trim() !== '' && !header.textContent.trim().includes('⋮⋮')) {
            header.classList.add('sortable-header');
            
            header.addEventListener('click', function() {
                const column = this.textContent.trim();
                // Send message to Streamlit to trigger sorting
                window.parent.postMessage({
                    isStreamlitMessage: true,
                    type: 'sort_column',
                    column: column
                }, '*');
            });
        }
    });
    
    // Drag and drop functionality
    const table = document.querySelector('.stDataFrame table tbody');
    if (table) {
        new Sortable(table, {
            animation: 150,
            handle: '.drag-handle',
            onEnd: function(evt) {
                window.parent.postMessage({
                    isStreamlitMessage: true,
                    type: 'row_reorder',
                    oldIndex: evt.oldIndex,
                    newIndex: evt.newIndex
                }, '*');
            }
        });
        
        // Add drag handles to each row
        const rows = table.querySelectorAll('tr');
        rows.forEach(row => {
            const firstCell = row.querySelector('td:first-child');
            if (firstCell) {
                firstCell.innerHTML = '<div class="drag-handle">⋮⋮</div>';
                firstCell.classList.add('draggable-row');
            }
        });
    }
});
</script>
""", unsafe_allow_html=True)

# Handle messages from JavaScript
if st.session_state.get('sort_column_js'):
    handle_sort(st.session_state.sort_column_js)
    st.session_state.sort_column_js = None

if st.session_state.get('row_reorder'):
    handle_row_reorder(st.session_state.row_reorder.oldIndex, st.session_state.row_reorder.newIndex)
    st.session_state.row_reorder = None

# Add a recalculate button for user convenience
if st.button("🔄 Recalculate", key="recalc_btn"):
    try:
        st.session_state["data"] = calculate_metrics(st.session_state["data"])
        st.rerun()
    except Exception as e:
        st.error(f"Error recalculating: {e}")

# ---------------- ACTION BUTTONS ----------------
col1, col2, col3 = st.columns([6, 1, 1])
with col3:
    if st.button("💾 Save", type="primary", key="save_btn"):
        try:
            save_data(st.session_state.current_date, st.session_state["data"])
            st.success("Saved successfully!")
        except Exception as e:
            st.error(f"Error saving: {e}")

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

# Create and display the chart
try:
    chart = create_simple_pie_chart(st.session_state["data"], st.session_state.chart_group)
    st.altair_chart(chart, use_container_width=True)
except Exception as e:
    st.error(f"Error creating chart: {str(e)}")
    st.info("Add valid schedule entries to see analytics.")
