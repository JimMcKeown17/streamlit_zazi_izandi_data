import streamlit as st
import pandas as pd
import plotly.express as px
from dotenv import load_dotenv
import os
import traceback
from data_loader import load_mentor_visits_2025_tp

# Load environment variables
load_dotenv()

# Define color mapping for Yes/No responses
def get_yes_no_colors():
    return {"Yes": "#2E86AB", "No": "#F24236"}  # Blue for Yes, Light Red for No

def display_mentor_visits_dashboard():
    st.title("📊 Mentor Visits Dashboard")

    try:
        # === Load Data ===
        df = load_mentor_visits_2025_tp()

        # === School Type Toggle ===
        school_type = st.radio(
            "Select School Type:",
            ["Primary Schools", "ECDCs"],
            index=0,  # Default to Primary Schools
            horizontal=True
        )
        
        # Filter by school type
        if school_type == "Primary Schools":
            df = df[df["Grade"] != "PreR"]
        else:  # ECDCs
            df = df[df["Grade"] == "PreR"]

        # === Sidebar Filters ===
        mentors = st.sidebar.multiselect("Filter by Mentor", df["Mentor Name"].dropna().unique())
        schools = st.sidebar.multiselect("Filter by School", df["School Name"].dropna().unique())

        filtered_df = df.copy()
        if mentors:
            filtered_df = filtered_df[filtered_df["Mentor Name"].isin(mentors)]
        if schools:
            filtered_df = filtered_df[filtered_df["School Name"].isin(schools)]

        st.write(f"Total visits in dataset: **{len(filtered_df)}**")

        # === Charts ===
        ## 1. Number of visits per Mentor
        st.subheader("Visits per Mentor")
        mentor_counts = filtered_df["Mentor Name"].value_counts().reset_index()
        mentor_counts.columns = ["Mentor", "Visits"]
        fig1 = px.bar(mentor_counts, x="Mentor", y="Visits", text="Visits", title="Number of Visits per Mentor")
        st.plotly_chart(fig1, use_container_width=True)

        ## 2. EA Children Grouping
        st.subheader("EA Children Grouping Correctly")
        
        # Overall pie chart for grouping correctness
        grouping_counts = filtered_df["Are the EA's children grouped correctly?"].value_counts().reset_index()
        grouping_counts.columns = ["Response", "Count"]
        fig2_pie = px.pie(grouping_counts, values="Count", names="Response", 
                          title="Overall EA Children Grouping Correctness (%)",
                          color="Response", color_discrete_map=get_yes_no_colors())
        st.plotly_chart(fig2_pie, use_container_width=True)
        
        # Bar chart by mentor
        fig2 = px.histogram(filtered_df, x="Mentor Name", color="Are the EA's children grouped correctly?",
                            barmode="group", title="Grouping Correctness by Mentor",
                            color_discrete_map=get_yes_no_colors())
        fig2.update_layout(legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig2, use_container_width=True)

        ## 3. EA Letter Tracker Use
        st.subheader("EA Letter Tracker Usage")
        
        # Overall pie chart for letter tracker usage
        tracker_counts = filtered_df["Are the EA using their letter tracker correctly?"].value_counts().reset_index()
        tracker_counts.columns = ["Response", "Count"]
        fig3_pie = px.pie(tracker_counts, values="Count", names="Response", 
                          title="Overall EA Letter Tracker Usage (%)",
                          color="Response", color_discrete_map=get_yes_no_colors())
        st.plotly_chart(fig3_pie, use_container_width=True)
        
        # Bar chart by mentor
        fig3 = px.histogram(filtered_df, x="Mentor Name", color="Are the EA using their letter tracker correctly?",
                            barmode="group", title="Letter Tracker Usage by Mentor",
                            color_discrete_map=get_yes_no_colors())
        fig3.update_layout(legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig3, use_container_width=True)

        ## 4. EA Teaching Correct Letters
        st.subheader("EA Teaching Correct Letters")
        
        # Overall pie chart for teaching correct letters
        letters_counts = filtered_df["The EA is teaching the correct letters per the group's letter knowledge (and letter trackers)"].value_counts().reset_index()
        letters_counts.columns = ["Response", "Count"]
        fig4_pie = px.pie(letters_counts, values="Count", names="Response", 
                          title="Overall EA Teaching Correct Letters (%)",
                          color="Response", color_discrete_map=get_yes_no_colors())
        st.plotly_chart(fig4_pie, use_container_width=True)
        
        # Bar chart by mentor
        fig4 = px.histogram(filtered_df, x="Mentor Name",
                            color="The EA is teaching the correct letters per the group's letter knowledge (and letter trackers)",
                            barmode="group", title="Correct Letters Taught by Mentor",
                            color_discrete_map=get_yes_no_colors())
        fig4.update_layout(legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig4, use_container_width=True)

        ## 5. Overall Quality Ratings
        st.subheader("Session Quality Ratings")
        fig5 = px.histogram(filtered_df, x="Mentor Name", color="Please rate the overall quality of the sessions you observe",
                            barmode="group", title="Session Quality Ratings by Mentor")
        fig5.update_layout(legend=dict(title="", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
        st.plotly_chart(fig5, use_container_width=True)

        # Overall distribution (not by mentor)
        quality_counts = filtered_df["Please rate the overall quality of the sessions you observe"].value_counts().reset_index()
        quality_counts.columns = ["Quality", "Count"]
        
        # Define the desired order for quality ratings
        quality_order = ["Excellent", "Very Good", "Good", "Average", "Poor"]
        quality_counts["Quality"] = pd.Categorical(quality_counts["Quality"], categories=quality_order, ordered=True)
        quality_counts = quality_counts.sort_values("Quality").reset_index(drop=True)
        
        fig6 = px.bar(quality_counts, x="Quality", y="Count", text="Count", title="Overall Session Quality Ratings")
        st.plotly_chart(fig6, use_container_width=True)

    except Exception as e:
        st.error("An error occurred while loading or displaying the dashboard.")
        st.code(traceback.format_exc())

# === Call function ===
display_mentor_visits_dashboard()
