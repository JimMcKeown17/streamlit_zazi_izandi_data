import streamlit as st
import pandas as pd
import plotly.express as px
from process_survey_cto_updated import process_egra_data
import os
from datetime import datetime as dt
from dotenv import load_dotenv
from data_loader import load_zazi_izandi_2025
# Load environment variables
load_dotenv()

def display_2025_zz_midline_ecd():
    # Check authentication
    if 'user' not in st.session_state:
        st.session_state.user = None


    st.title("2025 ECD Centers Midline Assessments")
    
    # Read and process data
    try:
        df_full, df_ecd = load_zazi_izandi_2025()
        
        # Check if there's ECD data
        if df_ecd.empty:
            st.warning("⚠️ No ECD assessment data found for the specified period.")
            st.info("This could mean:")
            st.markdown("""
            - No assessments were conducted at ECD centers during this period
            - ECD centers may be categorized differently in the data
            - The data cutoff date may exclude ECD assessments
            """)
            return
            
        df_ecd['submission_date'] = pd.to_datetime(df_ecd['date'])
        
        # Create initial and midline datasets for comparison charts
        initial_ecd = df_ecd[df_ecd['submission_date'] < pd.Timestamp('2025-05-15')]
        midline_ecd = df_ecd[df_ecd['submission_date'] >= pd.Timestamp('2025-05-15')]
        
        # If no midline data, use all ECD data as midline
        if midline_ecd.empty:
            st.info("🔄 No data found after May 15, 2025. Showing all ECD data as current results.")
            midline_ecd = df_ecd.copy()
            initial_ecd = pd.DataFrame()  # Empty initial data
        
        # START OF PAGE

        col1, col2 = st.columns(2)

        with col1:# Total Assessed
            st.metric("Total ECD Children Assessed", len(midline_ecd))

        with col2:
            # Number of unique ECD centers
            unique_centers = midline_ecd['school_rep'].nunique()
            st.metric("ECD Centers Participating", unique_centers)


        # Comparison with Primary Schools (if initial data exists)
        if not initial_ecd.empty and not midline_ecd.empty:

            
            # Calculate averages for comparison
            if 'letters_correct' in initial_ecd.columns and 'letters_correct' in midline_ecd.columns:
                initial_avg = initial_ecd['letters_correct'].mean()
                midline_avg = midline_ecd['letters_correct'].mean()
                improvement = midline_avg - initial_avg
                
                comparison_data = pd.DataFrame({
                    'Period': ['Initial', 'Midline'],
                    'Average_Letters_Correct': [initial_avg, midline_avg]
                })
                
                fig_comparison = px.bar(
                    comparison_data,
                    x='Period',
                    y='Average_Letters_Correct',
                    title="ECD Centers: Initial vs Midline Performance",
                    color='Period',
                    color_discrete_map={'Initial': '#b3b3b3', 'Midline': '#ffd641'}
                )
                
                st.plotly_chart(fig_comparison, use_container_width=True)
                
                if improvement > 0:
                    st.success(f"🎉 ECD centers showed improvement of {improvement:.1f} letters on average!")
                elif improvement < 0:
                    st.warning(f"⚠️ ECD centers showed a decrease of {abs(improvement):.1f} letters on average.")
                else:
                    st.info("📊 ECD centers maintained the same average performance.")
        # ECD Centers Summary
        if not midline_ecd.empty:
            st.header("ECD Centers Performance")
            
            # Group by school/center
            center_summary = midline_ecd.groupby('school_rep').agg(
                Number_Assessed=('name_first_learner', 'count'),
                Average_Letters_Correct=('letters_correct', 'mean'),
                Average_Letter_Score=('letters_score_a1', 'mean') if 'letters_score_a1' in midline_ecd.columns else ('letters_correct', 'mean'),
                Count_Above_40=('letters_correct', lambda x: (x >= 40).sum()) if 'letters_correct' in midline_ecd.columns else ('letters_score_a1', lambda x: (x >= 40).sum())
            ).reset_index()
            
            center_summary['Average_Letters_Correct'] = center_summary['Average_Letters_Correct'].round(1)
            center_summary['Average_Letter_Score'] = center_summary['Average_Letter_Score'].round(1)
            center_summary = center_summary.sort_values(by='Average_Letters_Correct', ascending=False)

            # ECD Centers Bar Chart
            fig = px.bar(
                center_summary,
                x="school_rep",
                y="Average_Letters_Correct",
                title="Average Letters Correct by ECD Center",
                labels={"school_rep": "ECD Center", "Average_Letters_Correct": "Average Letters Correct"},
                color="Average_Letters_Correct",
                color_continuous_scale="RdYlGn"
            )

            fig.update_layout(
                xaxis_title="ECD Center",
                yaxis_title="Average Letters Correct",
                xaxis_tickangle=-45
            )

            st.plotly_chart(fig, use_container_width=True)

            st.dataframe(center_summary, use_container_width=True)

        st.divider()

        # Letter Knowledge Performance
        if not midline_ecd.empty and 'letters_correct' in midline_ecd.columns:
            st.header("📝 Letter Knowledge Performance")
            
            # Overall performance metrics
            avg_letters = midline_ecd['letters_correct'].mean()
            median_letters = midline_ecd['letters_correct'].median()
            above_40_count = (midline_ecd['letters_correct'] >= 40).sum()
            above_40_percent = (above_40_count / len(midline_ecd) * 100) if len(midline_ecd) > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Average Letters Correct", f"{avg_letters:.1f}")
            with col2:
                st.metric("Median Letters Correct", f"{median_letters:.1f}")
            with col3:
                st.metric("Children Above Benchmark (≥40)", above_40_count)
            with col4:
                st.metric("Percentage Above Benchmark", f"{above_40_percent:.1f}%")
            
            # Distribution histogram
            fig_hist = px.histogram(
                midline_ecd,
                x='letters_correct',
                nbins=20,
                title="Distribution of Letter Knowledge Scores in ECD Centers",
                labels={'letters_correct': 'Letters Correct', 'count': 'Number of Children'}
            )
            
            # Add vertical line at benchmark (40)
            fig_hist.add_vline(x=15, line_dash="dash", line_color="red", 
                              annotation_text="EOY Target (15)", annotation_position="top")
            
            st.plotly_chart(fig_hist, use_container_width=True)

        st.divider()

        

        # Individual Center Analysis
        if not midline_ecd.empty and midline_ecd['school_rep'].nunique() > 1:
            st.divider()
            st.header("🔍 Individual Center Analysis")
            
            selected_center = st.selectbox(
                "Select an ECD Center for detailed analysis:",
                options=sorted(midline_ecd['school_rep'].unique()),
                key="ecd_center_selector"
            )
            
            center_data = midline_ecd[midline_ecd['school_rep'] == selected_center]
            
            if not center_data.empty:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader(f"📊 {selected_center} - Key Metrics")
                    center_children = len(center_data)
                    center_avg = center_data['letters_correct'].mean() if 'letters_correct' in center_data.columns else 0
                    center_above_15 = (center_data['letters_correct'] >= 15).sum() if 'letters_correct' in center_data.columns else 0
                    center_percent_15 = (center_above_15 / center_children * 100) if center_children > 0 else 0
                    
                    st.metric("Children Assessed", center_children)
                    st.metric("Average Letters Correct", f"{center_avg:.1f}")
                    st.metric("Above Benchmark (≥15)", f"{center_above_15} ({center_percent_15:.1f}%)")
                
                with col2:
                    if 'grade_label' in center_data.columns:
                        st.subheader(f"👶 Grade Distribution - {selected_center}")
                        center_grades = center_data['grade_label'].value_counts()
                        st.bar_chart(center_grades)

        # Raw Data Export
        st.divider()
        st.header("📥 Data Export")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Download ECD Summary Data", type="secondary"):
                if not midline_ecd.empty:
                    summary_data = midline_ecd.groupby('school_rep').agg({
                        'name_first_learner': 'count',
                        'letters_correct': ['mean', 'median', 'std'],
                        'date': ['min', 'max']
                    }).round(2)
                    
                    csv = summary_data.to_csv()
                    st.download_button(
                        label="Download Summary CSV",
                        data=csv,
                        file_name=f"ecd_summary_{dt.today().strftime('%Y-%m-%d')}.csv",
                        mime="text/csv"
                    )
        
        with col2:
            if st.button("📋 Download Full ECD Data", type="secondary"):
                if not midline_ecd.empty:
                    csv = midline_ecd.to_csv(index=False)
                    st.download_button(
                        label="Download Full CSV",
                        data=csv,
                        file_name=f"ecd_full_data_{dt.today().strftime('%Y-%m-%d')}.csv",
                        mime="text/csv"
                    )

        # Data Quality Information
        with st.expander("🔍 Data Quality Information", expanded=False):
            st.markdown("### ECD Data Overview")
            if not midline_ecd.empty:
                st.write(f"**Total Records:** {len(midline_ecd)}")
                st.write(f"**Date Range:** {midline_ecd['date'].min()} to {midline_ecd['date'].max()}")
                st.write(f"**ECD Centers Included:** {', '.join(sorted(midline_ecd['school_rep'].unique()))}")
                
                # Missing data analysis
                missing_data = midline_ecd.isnull().sum()
                important_cols = ['letters_correct', 'name_first_learner', 'school_rep', 'grade_label']
                missing_important = missing_data[missing_data.index.isin(important_cols)]
                
                if missing_important.sum() > 0:
                    st.warning("⚠️ Missing Data Detected:")
                    for col, missing_count in missing_important.items():
                        if missing_count > 0:
                            st.write(f"- {col}: {missing_count} missing values")
                else:
                    st.success("✅ No missing data in key columns")

    except Exception as e:
        st.error(f"Error loading ECD data: {e}")
        st.info("Please check if the data files exist and contain ECD assessment data.")
        
display_2025_zz_midline_ecd()