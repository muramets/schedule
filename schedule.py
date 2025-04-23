"""
Schedule Helper - A MonkeyType-inspired schedule tracking app
"""
import pandas as pd
import streamlit as st
import altair as alt
from datetime import datetime, date, timedelta
import json
import os
import streamlit.components.v1 as components

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
        cursor: pointer !important;
    }
    
    .stDataFrame th:hover {
        background-color: #2b2b2b !important;
        color: #ff8f1f !important;
    }
    
    /* Fix for table header tooltip issues */
    .stDataFrame [data-testid="StyledThTooltip"] {
        display: none !important;
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
    
    /* Sortable headers styling */
    .sortable-header {
        cursor: pointer;
        user-select: none;
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .sortable-header:hover {
        color: #ff8f1f;
    }
    
    .sort-icon {
        margin-left: 5px;
        font-size: 0.8em;
    }
    
    /* Other elements */
    .stDivider {
        background-color: #2b2b2b !important;
    }
    
    /* For the drag handle in the draggable editor */
    .drag-handle {
        cursor: grab;
        color: #555;
    }
    
    .drag-handle:hover {
        color: #ff8f1f;
    }
    
    /* Styling for the data editor with drag handles */
    .draggable-table-container {
        position: relative;
    }

    /* Info box styling */
    .stAlert {
        background-color: #232323 !important;
        border-color: #555 !important;
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
    
if "sort_ascending" not in st.session_state:
    st.session_state.sort_ascending = True

# Function to toggle chart group
def toggle_chart_group():
    st.session_state.chart_group = "Activity" if st.session_state.chart_group == "Category" else "Category"

# Function to sort data by column
def sort_data_by_column(column_name):
    if st.session_state.sort_column == column_name:
        # Toggle sort direction if same column is clicked again
        st.session_state.sort_ascending = not st.session_state.sort_ascending
    else:
        # Set new sort column and default to ascending
        st.session_state.sort_column = column_name
        st.session_state.sort_ascending = True
    
    # Apply sorting to the data
    if st.session_state.sort_column and st.session_state.sort_column in st.session_state["data"].columns:
        st.session_state["data"] = st.session_state["data"].sort_values(
            by=st.session_state.sort_column, 
            ascending=st.session_state.sort_ascending
        )

# Function to handle drag-and-drop reordering
def handle_reordering(new_order):
    """Reorder the dataframe based on the new indices"""
    if "data" in st.session_state and len(st.session_state["data"]) > 0:
        # Reorder the dataframe
        st.session_state["data"] = st.session_state["data"].reindex(new_order).reset_index(drop=True)

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
    st.session_state["data"] = load_data(st.session_state.current_date)
    st.session_state["data"] = calculate_metrics(st.session_state["data"])
    st.session_state["data_needs_reload"] = False

# ---------------- SCHEDULE TABLE ----------------
st.markdown("### Schedule")

# Create header with information about the new functionality
st.info("🔍 Click on column headers to sort the table. You can also drag and drop rows to reorder them.")

# -------------------- EDITABLE TABLE WITH DRAG-AND-DROP --------------------
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
    
    # Add column configurations with sort indicators
    column_config = {
        "Start": st.column_config.TextColumn(
            "Start", 
            required=True,
            help="Format: HH:MM"
        ),
        "End": st.column_config.TextColumn(
            "End", 
            required=True,
            help="Format: HH:MM"
        ),
        "Category": st.column_config.TextColumn(
            "Category", 
            required=True
        ),
        "Activity": st.column_config.TextColumn(
            "Activity", 
            required=True
        ),
        "Comment": st.column_config.TextColumn(
            "Comment"
        ),
        "Duration (min)": st.column_config.NumberColumn(
            "Duration (min)", 
            disabled=True,
            format="%d"
        ),
        "% of 12h": st.column_config.NumberColumn(
            "% of 12h", 
            disabled=True, 
            format="%.1f%%"
        )
    }
    
    # Add sort indicators to column headers if sorting is active
    if st.session_state.sort_column:
        col_name = st.session_state.sort_column
        if col_name in column_config:
            sort_indicator = " ↑" if st.session_state.sort_ascending else " ↓"
            column_config[col_name].label = f"{col_name}{sort_indicator}"
    
    # Add dataframe editor with drag-and-drop capability
    edited_df = st.data_editor(
        edit_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config=column_config,
        hide_index=True,
        key="data_editor",
        disabled=False,
        # Enable row drag-and-drop
        column_order=["Start", "End", "Category", "Activity", "Comment", "Duration (min)", "% of 12h"],
        # This enables row reordering through drag-and-drop
        use_dynamic_ordering=True
    )
    
    # Handle data changes
    if not edited_df.equals(st.session_state.get("last_edited_df", None)):
        # Calculate metrics based on edited data
        updated_df = calculate_metrics(edited_df)
        st.session_state["data"] = updated_df
        st.session_state["last_edited_df"] = edited_df.copy()
        st.rerun()

except Exception as e:
    st.error(f"Error displaying data editor. Please try refreshing the page. Error: {e}")
    st.session_state["data"] = create_empty_df()

# Add column sort buttons
st.markdown("#### Sort by Column")
sort_cols = st.columns(7)
col_names = ["Start", "End", "Category", "Activity", "Comment", "Duration (min)", "% of 12h"]

for i, col_name in enumerate(col_names):
    with sort_cols[i]:
        # Show a different icon depending on sort state
        sort_text = col_name
        if st.session_state.sort_column == col_name:
            sort_text += " ↑" if st.session_state.sort_ascending else " ↓"
            
        if st.button(sort_text, key=f"sort_{col_name}"):
            sort_data_by_column(col_name)
            st.rerun()

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

# Add JavaScript for enhanced table interactivity
js_code = """
<script>
// Function to handle column header clicks for sorting
function setupSortableHeaders() {
    // Wait for table headers to be rendered
    setTimeout(() => {
        const headers = document.querySelectorAll('.stDataFrame th');
        if (headers.length === 0) {
            return; // No headers found yet, try again later
        }
        
        headers.forEach((header, index) => {
            // Skip if already set up
            if (header.getAttribute('data-sort-setup') === 'true') {
                return;
            }
            
            // Get column name (remove sort indicators)
            const columnName = header.textContent.replace(/[↑↓]/g, '').trim();
            
            // Add click event
            header.addEventListener('click', function() {
                // Find the corresponding button and click it
                const sortButton = document.querySelector(`button[key="sort_${columnName}"]`);
                if (sortButton) {
                    sortButton.click();
                }
            });
            
            // Mark as set up
            header.setAttribute('data-sort-setup', 'true');
            
            // Add hover effect
            header.style.transition = 'color 0.3s ease, background-color 0.3s ease';
        });
    }, 1000); // Wait for elements to be fully rendered
}

// Enhance drag handles with better visual feedback
function enhanceDragHandles() {
    setTimeout(() => {
        const dragHandles = document.querySelectorAll('[data-testid="column-drag-handle"]');
        dragHandles.forEach(handle => {
            handle.style.cursor = 'grab';
            handle.addEventListener('mousedown', () => {
                handle.style.cursor = 'grabbing';
            });
            document.addEventListener('mouseup', () => {
                handle.style.cursor = 'grab';
            });
        });
    }, 1000);
}

// Run our setup functions
document.addEventListener('DOMContentLoaded', function() {
    // Initial setup
    setupSortableHeaders();
    enhanceDragHandles();
    
    // Set up mutation observer to catch dynamically loaded elements
    const observer = new MutationObserver((mutations) => {
        setupSortableHeaders();
        enhanceDragHandles();
    });
    
    // Start observing document body for DOM changes
    observer.observe(document.body, { 
        childList: true, 
        subtree: true 
    });
});

// Also set up periodic checks for reliability
setInterval(setupSortableHeaders, 2000);
setInterval(enhanceDragHandles, 2000);
</script>
"""

# Inject the JavaScript
components.html(js_code, height=0)

# Add summary statistics below the chart
if len(st.session_state["data"]) > 0:
    st.markdown("### Summary Statistics")
    
    # Calculate total time tracked
    total_minutes = st.session_state["data"]["Duration (min)"].sum()
    total_percent = round(total_minutes / TOTAL_MINUTES * 100, 1)
    
    # Create metrics in columns
    metric_cols = st.columns(3)
    
    with metric_cols[0]:
        hours = int(total_minutes // 60)
        mins = int(total_minutes % 60)
        st.metric("Total Time Tracked", f"{hours}h {mins}m")
    
    with metric_cols[1]:
        st.metric("% of 12h Day", f"{total_percent}%")
    
    with metric_cols[2]:
        remaining = TOTAL_MINUTES - total_minutes
        if remaining < 0:
            st.metric("Overbooked", f"{abs(int(remaining)) // 60}h {abs(int(remaining)) % 60}m")
        else:
            st.metric("Unallocated Time", f"{int(remaining) // 60}h {int(remaining) % 60}m")
    
    # Add category breakdown
    if st.session_state["data"]["Category"].notna().any():
        st.markdown("#### Category Breakdown")
        
        # Group by category
        cat_data = st.session_state["data"].groupby("Category")["Duration (min)"].sum().reset_index()
        cat_data["% of Total"] = (cat_data["Duration (min)"] / total_minutes * 100).round(1)
        cat_data["Hours"] = (cat_data["Duration (min)"] / 60).round(2)
        
        # Sort by duration
        cat_data = cat_data.sort_values("Duration (min)", ascending=False)
        
        # Display as table
        st.dataframe(
            cat_data[["Category", "Hours", "% of Total"]],
            column_config={
                "Category": st.column_config.TextColumn("Category"),
                "Hours": st.column_config.NumberColumn("Hours", format="%.2f"),
                "% of Total": st.column_config.NumberColumn("% of Total", format="%.1f%%")
            },
            use_container_width=True,
            hide_index=True
        )
