import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import os
import traceback
import subprocess
import sys
from pathlib import Path

# Load environment variables
load_dotenv()

# Auto-fetch and merge data on page load
@st.cache_data(ttl=3600)  # Cache for 1 hour to avoid running on every page refresh
def ensure_data_is_fresh():
    """
    Automatically fetch and merge mentor visit data if it doesn't exist or is outdated.
    Returns True if data is available, False otherwise.
    """
    api_dir = Path("api")
    merged_file = api_dir / "data" / "mentor_visit_tracker" / "merged_data_latest.csv"
    
    # Check if merged data exists and is recent (less than 24 hours old)
    data_is_fresh = False
    if merged_file.exists():
        import time
        file_age_hours = (time.time() - merged_file.stat().st_mtime) / 3600
        if file_age_hours < 24:
            data_is_fresh = True
            return {"success": True, "message": f"Using cached data (updated {file_age_hours:.1f} hours ago)", "fresh": True}
    
    # If data doesn't exist or is old, fetch and merge
    if not data_is_fresh:
        try:
            with st.spinner("🔄 Fetching latest mentor visit data from API..."):
                # Run fetch script
                fetch_script = api_dir / "fetch_mentor_visit_data.py"
                if not fetch_script.exists():
                    return {"success": False, "message": "Fetch script not found at api/fetch_mentor_visit_data.py"}
                
                result = subprocess.run(
                    [sys.executable, "fetch_mentor_visit_data.py"],
                    cwd=str(api_dir),
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode != 0:
                    return {"success": False, "message": f"Fetch failed: {result.stderr}"}
            
            with st.spinner("🔄 Merging old and new survey data..."):
                # Run merge script
                merge_script = api_dir / "merge_mentor_visit_data.py"
                if not merge_script.exists():
                    return {"success": False, "message": "Merge script not found at api/merge_mentor_visit_data.py"}
                
                result = subprocess.run(
                    [sys.executable, "merge_mentor_visit_data.py"],
                    cwd=str(api_dir),
                    capture_output=True,
                    text=True,
                    timeout=60  # 1 minute timeout
                )
                
                if result.returncode != 0:
                    return {"success": False, "message": f"Merge failed: {result.stderr}"}
            
            return {"success": True, "message": "✅ Data fetched and merged successfully!", "fresh": False}
            
        except subprocess.TimeoutExpired:
            return {"success": False, "message": "Operation timed out. Please try again."}
        except Exception as e:
            return {"success": False, "message": f"Error: {str(e)}"}
    
    return {"success": True, "message": "Data loaded successfully", "fresh": True}

# Run data check at startup
data_status = ensure_data_is_fresh()
if not data_status["success"]:
    st.error(data_status["message"])
    st.info("💡 Please ensure your TEAMPACT_API_TOKEN environment variable is set correctly.")
    st.stop()
elif not data_status.get("fresh", False):
    st.success(data_status["message"])

# DataQuest Schools Filter List
selected_schools_list = [
    "Aaron Gqadu Primary School",
    "Ben Sinuka Primary School",
    "Coega Primary School",
    "Dumani Primary School",
    "Ebongweni Public Primary School",
    "Elufefeni Primary School",
    "Empumalanga Primary School",
    "Enkululekweni Primary School",
    "Esitiyeni Public Primary School",
    "Fumisukoma Primary School",
    "Ilinge Primary School",
    "Isaac Booi Senior Primary School",
    "James Ntungwana Primary School",
    "Jarvis Gqamlana Public Primary School",
    "Joe Slovo Primary School",
    "Little Flower Primary School",
    "Magqabi Primary School",
    "Mjuleni Junior Primary School",
    "Mngcunube Primary School",
    "Molefe Senior Primary School",
    "Noninzi Luzipho Primary School",
    "Ntlemeza Primary School",
    "Phindubuye Primary School",
    "Seyisi Primary School",
    "Sikhothina Primary School",
    "Soweto-On-Sea Primary School",
    "Stephen Nkomo Senior Primary School",
    "W B Tshume Primary School"
]

# Define color mapping for Yes/No responses
def get_yes_no_colors():
    return {"Yes": "#2E86AB", "No": "#F24236"}  # Blue for Yes, Light Red for No

def load_merged_mentor_visits():
    """Load the merged mentor visits data from the merged CSV file"""
    try:
        # Load the merged data
        df = pd.read_csv('api/data/mentor_visit_tracker/merged_data_latest.csv')
        
        # Convert date columns to datetime
        date_columns = ['response_start_at', 'response_end_at', 'created_at', 'updated_at']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        # Create a user-friendly Response Date column
        df['Response Date'] = df['response_start_at']
        
        # Create unified "Teaching at Right Level" column that combines old and new questions
        # Old question: "The EA is teaching the correct letters per the group's letter knowledge (and letter trackers)"
        # New question: "Teaching at the right level"
        old_col = "The EA is teaching the correct letters per the group's letter knowledge (and letter trackers)"
        new_col = "Teaching at the right level"
        
        if old_col in df.columns and new_col in df.columns:
            # Create unified column - prioritize new column data where available
            df['Teaching at Right Level (Unified)'] = df[new_col].fillna(df[old_col])
        elif old_col in df.columns:
            df['Teaching at Right Level (Unified)'] = df[old_col]
        elif new_col in df.columns:
            df['Teaching at Right Level (Unified)'] = df[new_col]
        
        return df
        
    except Exception as e:
        st.error(f"Error loading merged data: {str(e)}")
        st.code(traceback.format_exc())
        return pd.DataFrame()

def display_mentor_visits_dashboard():
    st.title("📊 Mentor Visits Dashboard")

    try:
        # === Load Data ===
        df = load_merged_mentor_visits()
        
        if df.empty:
            st.warning("No data available. Please check the data loading process.")
            return

        # === School Type Toggle ===
        school_type = st.radio(
            "Select School Type:",
            ["Primary Schools", "ECDCs", "DataQuest Schools"],
            index=0,  # Default to Primary Schools
            horizontal=True
        )

        # Filter by school type
        if school_type == "Primary Schools":
            df = df[df["Grade"] != "PreR"]
        elif school_type == "ECDCs":
            df = df[df["Grade"] == "PreR"]
        else:  # DataQuest Schools
            # Filter to only include DataQuest schools using first-word matching (same logic as table flag)
            dataquest_first_words = [school.split()[0].lower() for school in selected_schools_list]

            def is_dataquest_school_filter(school_name):
                if pd.isna(school_name) or school_name == "":
                    return False
                # Get first word of the school name
                first_word = str(school_name).split()[0].lower()
                return first_word in dataquest_first_words

            df = df[df["School Name"].apply(is_dataquest_school_filter)]
            # Further filter to exclude PreR (ECDCs) since DataQuest are Primary Schools
            df = df[df["Grade"] != "PreR"]

        # === Sidebar Filters ===
        mentors = st.sidebar.multiselect("Filter by Mentor", df["Mentor Name"].dropna().unique())
        schools = st.sidebar.multiselect("Filter by School", df["School Name"].dropna().unique())
        
        # Add survey source filter
        if 'survey_source' in df.columns:
            survey_sources = st.sidebar.multiselect("Filter by Survey", df["survey_source"].dropna().unique())

        filtered_df = df.copy()
        if mentors:
            filtered_df = filtered_df[filtered_df["Mentor Name"].isin(mentors)]
        if schools:
            filtered_df = filtered_df[filtered_df["School Name"].isin(schools)]
        if 'survey_source' in df.columns and survey_sources:
            filtered_df = filtered_df[filtered_df["survey_source"].isin(survey_sources)]

        st.write(f"Total visits in dataset: **{len(filtered_df)}**")
        
        # Show data source breakdown
        if 'survey_source' in filtered_df.columns:
            source_counts = filtered_df['survey_source'].value_counts()
            cols = st.columns(len(source_counts))
            for idx, (source, count) in enumerate(source_counts.items()):
                with cols[idx]:
                    st.metric(label=source, value=count)

        # === Charts ===
        ## 1. Number of visits per Mentor
        st.subheader("Visits per Mentor")
        mentor_counts = filtered_df["Mentor Name"].value_counts().reset_index()
        mentor_counts.columns = ["Mentor", "Visits"]
        fig1 = px.bar(mentor_counts, x="Mentor", y="Visits", text="Visits", title="Number of Visits per Mentor")
        st.plotly_chart(fig1, width='stretch')

        ## 2. EA Children Grouping
        st.subheader("EA Children Grouping Correctly")
        
        grouping_col = "Are the EA's children grouped correctly?"
        
        if grouping_col in filtered_df.columns and 'School Name' in filtered_df.columns:
            # Get first and most recent visits per school
            school_comparison_data = []
            
            for school in filtered_df['School Name'].dropna().unique():
                school_df = filtered_df[filtered_df['School Name'] == school].copy()
                school_df = school_df[school_df[grouping_col].notna()]
                
                if not school_df.empty:
                    # Sort by date
                    school_df['Response Date'] = pd.to_datetime(school_df['response_start_at'], errors='coerce')
                    school_df = school_df.sort_values('Response Date')
                    
                    first_visit = school_df.iloc[0]
                    most_recent_visit = school_df.iloc[-1]
                    
                    school_comparison_data.append({
                        'School Name': school,
                        'First Visit Mentor': first_visit.get('Mentor Name', 'Unknown'),
                        'First Visit EA': first_visit.get('EA Name', 'Unknown'),
                        'First Visit Date': first_visit['Response Date'].strftime('%Y-%m-%d') if pd.notna(first_visit['Response Date']) else 'Unknown',
                        'First Visit Response': first_visit[grouping_col],
                        'Most Recent Visit Date': most_recent_visit['Response Date'].strftime('%Y-%m-%d') if pd.notna(most_recent_visit['Response Date']) else 'Unknown',
                        'Most Recent Visit Response': most_recent_visit[grouping_col],
                        'Most Recent Visit Mentor': most_recent_visit.get('Mentor Name', 'Unknown'),
                        'Most Recent Visit EA': most_recent_visit.get('EA Name', 'Unknown'),
                        'Total Visits': len(school_df),
                        'Same Visit': len(school_df) == 1
                    })
            
            if school_comparison_data:
                comparison_df = pd.DataFrame(school_comparison_data)
                
                # Create side-by-side pie charts
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**First Visits to Each School**")
                    first_counts = comparison_df['First Visit Response'].value_counts().reset_index()
                    first_counts.columns = ["Response", "Count"]
                    fig2_first = px.pie(first_counts, values="Count", names="Response", 
                                        title="First Visit: EA Children Grouping",
                                        color="Response", color_discrete_map=get_yes_no_colors())
                    st.plotly_chart(fig2_first, width='stretch')
                    st.caption(f"Based on {len(comparison_df)} schools")
                
                with col2:
                    st.markdown("**Most Recent Visits to Each School**")
                    recent_counts = comparison_df['Most Recent Visit Response'].value_counts().reset_index()
                    recent_counts.columns = ["Response", "Count"]
                    fig2_recent = px.pie(recent_counts, values="Count", names="Response", 
                                         title="Most Recent Visit: EA Children Grouping",
                                         color="Response", color_discrete_map=get_yes_no_colors())
                    st.plotly_chart(fig2_recent, width='stretch')
                    st.caption(f"Based on {len(comparison_df)} schools")
                
                # Show detailed table in expander
                with st.expander("📋 View School-by-School Comparison Table"):
                    display_comparison = comparison_df.copy()
                    display_comparison['Status'] = display_comparison.apply(
                        lambda row: '✅ Same' if row['Same Visit'] else 
                                   ('✅ Improved' if row['First Visit Response'] == 'No' and row['Most Recent Visit Response'] == 'Yes' else
                                    ('⚠️ Declined' if row['First Visit Response'] == 'Yes' and row['Most Recent Visit Response'] == 'No' else
                                     '→ No Change')), axis=1
                    )
                    
                    # Reorder columns to include Mentor and EA names
                    table_cols = ['School Name', 'First Visit Mentor', 'First Visit EA', 'Total Visits', 
                                  'First Visit Date', 'First Visit Response', 
                                  'Most Recent Visit Date', 'Most Recent Visit Response', 
                                  'Most Recent Visit Mentor', 'Most Recent Visit EA', 'Status']
                    st.dataframe(display_comparison[table_cols], width='stretch', hide_index=True)
                    
                    # Summary stats
                    improved = len(display_comparison[display_comparison['Status'] == '✅ Improved'])
                    declined = len(display_comparison[display_comparison['Status'] == '⚠️ Declined'])
                    no_change = len(display_comparison[display_comparison['Status'] == '→ No Change'])
                    same_visit = len(display_comparison[display_comparison['Status'] == '✅ Same'])
                    
                    st.info(f"📊 **Change Summary**: {improved} improved | {declined} declined | {no_change} no change | {same_visit} single visit only")
            else:
                st.info("No data available for grouping comparison")
        
        # Bar chart by mentor (overall)
        if grouping_col in filtered_df.columns:
            fig2_mentor = px.histogram(filtered_df, x="Mentor Name", color=grouping_col,
                                barmode="group", title="Grouping Correctness by Mentor (All Visits)",
                                color_discrete_map=get_yes_no_colors())
            fig2_mentor.update_layout(legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig2_mentor, width='stretch')

        ## 3. EA Letter Tracker Use
        st.subheader("EA Letter Tracker Usage")
        
        tracker_col = "Are the EA using their letter tracker correctly?"
        
        if tracker_col in filtered_df.columns and 'School Name' in filtered_df.columns:
            # Get first and most recent visits per school
            tracker_comparison_data = []
            
            for school in filtered_df['School Name'].dropna().unique():
                school_df = filtered_df[filtered_df['School Name'] == school].copy()
                school_df = school_df[school_df[tracker_col].notna()]
                
                if not school_df.empty:
                    # Sort by date
                    school_df['Response Date'] = pd.to_datetime(school_df['response_start_at'], errors='coerce')
                    school_df = school_df.sort_values('Response Date')
                    
                    first_visit = school_df.iloc[0]
                    most_recent_visit = school_df.iloc[-1]
                    
                    tracker_comparison_data.append({
                        'School Name': school,
                        'First Visit Mentor': first_visit.get('Mentor Name', 'Unknown'),
                        'First Visit EA': first_visit.get('EA Name', 'Unknown'),
                        'First Visit Date': first_visit['Response Date'].strftime('%Y-%m-%d') if pd.notna(first_visit['Response Date']) else 'Unknown',
                        'First Visit Response': first_visit[tracker_col],
                        'Most Recent Visit Date': most_recent_visit['Response Date'].strftime('%Y-%m-%d') if pd.notna(most_recent_visit['Response Date']) else 'Unknown',
                        'Most Recent Visit Response': most_recent_visit[tracker_col],
                        'Most Recent Visit Mentor': most_recent_visit.get('Mentor Name', 'Unknown'),
                        'Most Recent Visit EA': most_recent_visit.get('EA Name', 'Unknown'),
                        'Total Visits': len(school_df),
                        'Same Visit': len(school_df) == 1
                    })
            
            if tracker_comparison_data:
                comparison_df = pd.DataFrame(tracker_comparison_data)
                
                # Create side-by-side pie charts
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**First Visits to Each School**")
                    first_counts = comparison_df['First Visit Response'].value_counts().reset_index()
                    first_counts.columns = ["Response", "Count"]
                    fig3_first = px.pie(first_counts, values="Count", names="Response", 
                                        title="First Visit: Letter Tracker Usage",
                                        color="Response", color_discrete_map=get_yes_no_colors())
                    st.plotly_chart(fig3_first, width='stretch')
                    st.caption(f"Based on {len(comparison_df)} schools")
                
                with col2:
                    st.markdown("**Most Recent Visits to Each School**")
                    recent_counts = comparison_df['Most Recent Visit Response'].value_counts().reset_index()
                    recent_counts.columns = ["Response", "Count"]
                    fig3_recent = px.pie(recent_counts, values="Count", names="Response", 
                                         title="Most Recent Visit: Letter Tracker Usage",
                                         color="Response", color_discrete_map=get_yes_no_colors())
                    st.plotly_chart(fig3_recent, width='stretch')
                    st.caption(f"Based on {len(comparison_df)} schools")
                
                # Show detailed table in expander
                with st.expander("📋 View School-by-School Comparison Table"):
                    display_comparison = comparison_df.copy()
                    display_comparison['Status'] = display_comparison.apply(
                        lambda row: '✅ Same' if row['Same Visit'] else 
                                   ('✅ Improved' if row['First Visit Response'] == 'No' and row['Most Recent Visit Response'] == 'Yes' else
                                    ('⚠️ Declined' if row['First Visit Response'] == 'Yes' and row['Most Recent Visit Response'] == 'No' else
                                     '→ No Change')), axis=1
                    )
                    
                    # Reorder columns to include Mentor and EA names
                    table_cols = ['School Name', 'First Visit Mentor', 'First Visit EA', 'Total Visits', 
                                  'First Visit Date', 'First Visit Response', 
                                  'Most Recent Visit Date', 'Most Recent Visit Response',
                                  'Most Recent Visit Mentor', 'Most Recent Visit EA', 'Status']
                    st.dataframe(display_comparison[table_cols], width='stretch', hide_index=True)
                    
                    # Summary stats
                    improved = len(display_comparison[display_comparison['Status'] == '✅ Improved'])
                    declined = len(display_comparison[display_comparison['Status'] == '⚠️ Declined'])
                    no_change = len(display_comparison[display_comparison['Status'] == '→ No Change'])
                    same_visit = len(display_comparison[display_comparison['Status'] == '✅ Same'])
                    
                    st.info(f"📊 **Change Summary**: {improved} improved | {declined} declined | {no_change} no change | {same_visit} single visit only")
            else:
                st.info("No data available for tracker usage comparison")
        
        # Bar chart by mentor (overall)
        if tracker_col in filtered_df.columns:
            fig3_mentor = px.histogram(filtered_df, x="Mentor Name", color=tracker_col,
                                barmode="group", title="Letter Tracker Usage by Mentor (All Visits)",
                                color_discrete_map=get_yes_no_colors())
            fig3_mentor.update_layout(legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.plotly_chart(fig3_mentor, width='stretch')

        ## 4. Teaching at Right Level - Split by Survey Type
        st.subheader("Teaching at the Right Level")
        
        # Split data by survey source
        old_survey_col = "The EA is teaching the correct letters per the group's letter knowledge (and letter trackers)"
        new_survey_col = "Teaching at the right level"
        
        # Create two columns for side-by-side charts
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Old Survey (Yes/No)**")
            if old_survey_col in filtered_df.columns:
                old_data = filtered_df[filtered_df[old_survey_col].notna()]
                
                if not old_data.empty:
                    # Old survey - simple Yes/No pie chart
                    old_counts = old_data[old_survey_col].value_counts().reset_index()
                    old_counts.columns = ["Response", "Count"]
                    
                    fig4_old = px.pie(old_counts, values="Count", names="Response", 
                                      title="Teaching Correct Letters (Old Survey)",
                                      color="Response", color_discrete_map=get_yes_no_colors())
                    st.plotly_chart(fig4_old, width='stretch')
                    
                    # Show counts
                    st.caption(f"Total responses: {len(old_data)}")
                else:
                    st.info("No old survey data available")
            else:
                st.info("Old survey column not found")
        
        with col2:
            st.markdown("**New Survey (Multiple Options)**")
            if new_survey_col in filtered_df.columns:
                new_data = filtered_df[filtered_df[new_survey_col].notna()]
                
                if not new_data.empty:
                    # New survey - split comma-separated values and count each option
                    # Create a list to store expanded records
                    expanded_records = []
                    
                    for idx, value in new_data[new_survey_col].items():
                        if pd.notna(value):
                            # Split by comma and strip whitespace
                            options = [opt.strip() for opt in str(value).split(',')]
                            for option in options:
                                if option:  # Only add non-empty options
                                    expanded_records.append(option)
                    
                    # Count occurrences of each option
                    if expanded_records:
                        expanded_df = pd.DataFrame({'Response': expanded_records})
                        new_counts = expanded_df['Response'].value_counts().reset_index()
                        new_counts.columns = ["Response", "Count"]
                        
                        # Bar chart for multiple options (better for 4+ categories)
                        fig4_new = px.bar(new_counts, x="Response", y="Count", 
                                          title="Teaching at Right Level (New Survey)",
                                          text="Count")
                        fig4_new.update_layout(xaxis_title="", yaxis_title="Count")
                        fig4_new.update_traces(textposition='outside')
                        st.plotly_chart(fig4_new, width='stretch')
                        
                        # Show counts
                        st.caption(f"Total individual responses: {len(expanded_records)} (from {len(new_data)} visits)")
                    else:
                        st.info("No valid responses in new survey data")
                else:
                    st.info("No new survey data available")
            else:
                st.info("New survey column not found")
        
        # Combined bar chart by mentor (optional - shows distribution across mentors)
        st.markdown("**Teaching at Right Level by Mentor**")
        
        # For old survey data
        if old_survey_col in filtered_df.columns:
            old_mentor_data = filtered_df[filtered_df[old_survey_col].notna()]
            if not old_mentor_data.empty:
                fig4_old_mentor = px.histogram(old_mentor_data, x="Mentor Name",
                                                color=old_survey_col,
                                                barmode="group", 
                                                title="Old Survey: Teaching Correct Letters by Mentor",
                                                color_discrete_map=get_yes_no_colors())
                fig4_old_mentor.update_layout(legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                st.plotly_chart(fig4_old_mentor, width='stretch')
        
        # For new survey data - expand comma-separated values
        if new_survey_col in filtered_df.columns:
            new_mentor_data = filtered_df[filtered_df[new_survey_col].notna()].copy()
            if not new_mentor_data.empty:
                # Expand comma-separated values for mentor chart
                expanded_mentor_records = []
                for idx, row in new_mentor_data.iterrows():
                    mentor = row.get('Mentor Name', 'Unknown')
                    value = row[new_survey_col]
                    if pd.notna(value):
                        options = [opt.strip() for opt in str(value).split(',')]
                        for option in options:
                            if option:
                                expanded_mentor_records.append({
                                    'Mentor Name': mentor,
                                    'Response': option
                                })
                
                if expanded_mentor_records:
                    expanded_mentor_df = pd.DataFrame(expanded_mentor_records)
                    fig4_new_mentor = px.histogram(expanded_mentor_df, x="Mentor Name",
                                                    color="Response",
                                                    barmode="group", 
                                                    title="New Survey: Teaching at Right Level by Mentor")
                    fig4_new_mentor.update_layout(legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig4_new_mentor, width='stretch')

        ## 5. Overall Quality Ratings
        st.subheader("Session Quality Ratings")
        fig5 = px.histogram(filtered_df, x="Mentor Name", color="Please rate the overall quality of the sessions you observe",
                            barmode="group", title="Session Quality Ratings by Mentor")
        fig5.update_layout(legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig5, width='stretch')

        ## 6. EA-Teacher Relationship
        st.subheader("EA-Teacher Relationships")
        fig6 = px.histogram(filtered_df, x="Mentor Name", color="How is the EA's relationship with their teacher?",
                            barmode="group", title="EA-Teacher Relationship by Mentor")
        fig6.update_layout(legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig6, width='stretch')

        st.divider()

        # === DataQuest Schools Summary Table ===
        st.subheader("DataQuest Schools Summary")
        
        # Create DataQuest schools summary using the same first-word matching logic
        dataquest_first_words = [school.split()[0].lower() for school in selected_schools_list]

        def matches_dataquest_school(school_name, target_first_word):
            if pd.isna(school_name) or school_name == "":
                return False
            first_word = str(school_name).split()[0].lower()
            return first_word == target_first_word

        dataquest_summary = []

        for dataquest_school in selected_schools_list:
            target_first_word = dataquest_school.split()[0].lower()

            # Filter visits for this DataQuest school using first-word matching
            school_visits = filtered_df[filtered_df["School Name"].apply(
                lambda x: matches_dataquest_school(x, target_first_word)
            )]

            if not school_visits.empty:
                # Get most recent visit
                if "Response Date" in school_visits.columns:
                    school_visits_sorted = school_visits.copy()
                    school_visits_sorted["Response Date"] = pd.to_datetime(school_visits_sorted["Response Date"], errors='coerce')
                    most_recent_visit = school_visits_sorted.loc[school_visits_sorted["Response Date"].idxmax()]
                    last_visit_date = most_recent_visit["Response Date"].strftime('%Y-%m-%d') if pd.notna(most_recent_visit["Response Date"]) else "No date"

                    # Get the most recent Teaching at Right Level value (unified column)
                    teaching_col = 'Teaching at Right Level (Unified)'
                    last_teaching_correct = most_recent_visit.get(teaching_col, "No data")
                else:
                    last_visit_date = "No date"
                    last_teaching_correct = "No data"

                # Count total visits
                total_visits = len(school_visits)

                dataquest_summary.append({
                    "DataQuest School": dataquest_school,
                    "Total Visits": total_visits,
                    "Last Visit Date": last_visit_date,
                    "Last Teaching at Right Level": last_teaching_correct
                })
            else:
                # No visits found for this school
                dataquest_summary.append({
                    "DataQuest School": dataquest_school,
                    "Total Visits": 0,
                    "Last Visit Date": "No visits",
                    "Last Teaching at Right Level": "No visits"
                })

        # Create DataFrame and display
        if dataquest_summary:
            dataquest_df = pd.DataFrame(dataquest_summary)

            # Sort by Total Visits descending, then by Last Visit Date descending
            dataquest_df = dataquest_df.sort_values(["Total Visits", "Last Visit Date"], ascending=[False, False])

            st.dataframe(dataquest_df, width='stretch', hide_index=True)

            # Summary statistics
            total_dataquest_visits = dataquest_df["Total Visits"].sum()
            schools_with_visits = (dataquest_df["Total Visits"] > 0).sum()
            st.info(f"📊 **Summary**: {schools_with_visits} of {len(selected_schools_list)} DataQuest schools have received mentor visits. Total visits: {total_dataquest_visits}")

        st.divider()

        # === Data Table ===
        st.subheader("All Visits Data")

        # Create a copy of filtered data with abbreviated column names
        table_df = filtered_df.copy()

        # Select and rename columns for the table - include all relevant questions
        potential_columns_mapping = {
            "Response Date": "Visit Date",
            "survey_source": "Survey Source",
            "Mentor Name": "Mentor Name",
            "School Name": "School Name",
            "EA Name": "EA Name",
            "Grade": "Grade",
            "Class": "Class",
            "Are the EA's children grouped correctly?": "Grouping Correct",
            "If EA grouping are incorrect, please explain why?": "Grouping Issues",
            "Are the EA using their letter tracker correctly?": "Letter Tracker Use",
            "If No, have you corrected it?": "Tracker Corrected",
            "Session Tag": "Session Tag",
            "Is the EA using the comment section accordingly?": "Using Comments",
            "Teaching at Right Level (Unified)": "Teaching at Right Level",
            "How engaged did you feel the learners are?": "Learner Engagement",
            "How energertic & prepared was the EA?": "EA Energy & Prep",
            "Please rate the overall quality of the sessions you observe": "Session Quality",
            "How many sessions does the EA say they can do per day?": "Sessions Per Day",
            "How is the EA's relationship with their teacher?": "Teacher Relationship",
            "Does the EA experience challenges accessing the learners": "Access Challenges",
            "Reason for having 1 session or none": "Reason for Low Sessions",
            "Any additional commentary?": "Additional Comments"
        }

        # Only use columns that actually exist in the dataframe
        columns_mapping = {}
        for original_col, display_name in potential_columns_mapping.items():
            if original_col in table_df.columns:
                columns_mapping[original_col] = display_name

        if columns_mapping:
            # Select only the columns we want and rename them
            display_columns = list(columns_mapping.keys())
            table_display = table_df[display_columns].rename(columns=columns_mapping)

            # Convert Visit Date to datetime and sort by most recent first
            if "Visit Date" in table_display.columns:
                # Convert to datetime, handling various date formats
                table_display["Visit Date"] = pd.to_datetime(table_display["Visit Date"], errors='coerce')
                # Format to show only date (no time)
                table_display["Visit Date"] = table_display["Visit Date"].dt.strftime('%Y-%m-%d')
                # Sort by Visit Date (most recent first), with NaT values at the end
                table_display = table_display.sort_values("Visit Date", ascending=False, na_position='last')

            # Add DataQuest School flag and reorder columns to put it after School Name
            if "School Name" in table_display.columns:
                # Extract first word from each DataQuest school name (case-insensitive)
                dataquest_first_words = [school.split()[0].lower() for school in selected_schools_list]

                # Extract first word from school names in the data and check if it matches any DataQuest first word
                def is_dataquest_school(school_name):
                    if pd.isna(school_name) or school_name == "":
                        return "No"
                    # Get first word of the school name
                    first_word = str(school_name).split()[0].lower()
                    return "Yes" if first_word in dataquest_first_words else "No"

                table_display["DataQuest School"] = table_display["School Name"].apply(is_dataquest_school)

                # Reorder columns to put DataQuest School after School Name
                cols = list(table_display.columns)
                if "School Name" in cols and "DataQuest School" in cols:
                    # Remove DataQuest School from its current position
                    cols.remove("DataQuest School")
                    # Find position of School Name and insert DataQuest School after it
                    school_name_idx = cols.index("School Name")
                    cols.insert(school_name_idx + 1, "DataQuest School")
                    # Reorder the dataframe
                    table_display = table_display[cols]

            # Display the table with scrolling
            st.dataframe(
                table_display,
                width='stretch',
                height=400  # Fixed height to make it scrollable
            )

            st.write(f"Showing **{len(table_display)}** visits")
        else:
            st.warning("No expected columns found in the data.")
            # Show all available data as fallback
            st.dataframe(table_df, width='stretch', height=400)

    except Exception as e:
        st.error("An error occurred while loading or displaying the dashboard.")
        st.code(traceback.format_exc())

# === Call function ===
display_mentor_visits_dashboard()