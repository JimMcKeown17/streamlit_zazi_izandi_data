import streamlit as st
import pandas as pd
import plotly.express as px
from process_survey_cto_updated import process_egra_data
import os
from datetime import datetime as dt
from dotenv import load_dotenv
from data_loader import load_zazi_izandi_2025, load_zazi_izandi_ecd_endline
# Load environment variables
load_dotenv()

def display_2025_zz_midline_ecd():
    # Check authentication
    if 'user' not in st.session_state:
        st.session_state.user = None


    st.title("2025 ECD Centers Assessments")
    
    # Read and process data
    try:
        df_full, df_ecd = load_zazi_izandi_2025()
        endline_ecd = load_zazi_izandi_ecd_endline()
        
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
        
        if endline_ecd.empty:
            st.warning("⚠️ No ECD endline assessment data found.")
            st.info("Endline data will appear here once assessments are completed.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total ECD Children Assessed", len(endline_ecd))
            with col2:
                if 'Program Name' in endline_ecd.columns:
                    unique_centers = endline_ecd['Program Name'].nunique()
                    st.metric("ECD Centers Participating", unique_centers)

            
            # Comparison chart with all three periods
            if not initial_ecd.empty and not midline_ecd.empty:
                # Calculate averages for comparison
                if 'letters_correct' in initial_ecd.columns and 'letters_correct' in midline_ecd.columns:
                    initial_avg = initial_ecd['letters_correct'].mean()
                    midline_avg = midline_ecd['letters_correct'].mean()
                    
                    # Create comparison data with all three periods
                    periods = ['Initial', 'Midline']
                    averages = [initial_avg, midline_avg]
                    endline_improvement = None
                    
                    # Add endline if available (note the trailing space in column name)
                    if 'Total cells correct - NMB ECD Endline ' in endline_ecd.columns:
                        endline_avg = endline_ecd['Total cells correct - NMB ECD Endline '].mean()
                        periods.append('Endline')
                        averages.append(endline_avg)
                        
                        # Calculate improvement from midline to endline
                        endline_improvement = endline_avg - midline_avg
                    
                    comparison_data = pd.DataFrame({
                        'Period': periods,
                        'Average_Letters_Correct': averages
                    })
                    
                    fig_comparison = px.bar(
                        comparison_data,
                        x='Period',
                        y='Average_Letters_Correct',
                        title="ECD Centers: Initial vs Midline vs Endline Performance",
                        color='Period',
                        color_discrete_map={'Initial': '#b3b3b3', 'Midline': '#ffd641', 'Endline': '#4CAF50'}
                    )
                    
                    st.plotly_chart(fig_comparison, key='endline_comparison_chart', use_container_width=True)
                    
                    if endline_improvement is not None:
                        if endline_improvement > 0:
                            st.success(f"🎉 ECD centers showed improvement of {endline_improvement:.1f} letters from midline to endline!")
                        elif endline_improvement < 0:
                            st.warning(f"⚠️ ECD centers showed a decrease of {abs(endline_improvement):.1f} letters from midline to endline.")
                        else:
                            st.info("📊 ECD centers maintained the same average performance from midline to endline.")
            
            # Baseline vs Endline Pie Charts
            st.header("Performance Comparison: Baseline vs Endline")
            
            # Benchmark slider
            benchmark = st.slider(
                "Select Benchmark (Letters Correct)",
                min_value=10,
                max_value=40,
                value=10,
                step=1,
                help="Adjust the benchmark to see how many children meet different performance thresholds"
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if not initial_ecd.empty and 'letters_correct' in initial_ecd.columns:
                    st.subheader("Baseline")
                    above_benchmark_baseline = (initial_ecd['letters_correct'] >= benchmark).sum()
                    below_benchmark_baseline = (initial_ecd['letters_correct'] < benchmark).sum()
                    
                    baseline_data = pd.DataFrame({
                        'Category': [f'At or Above Benchmark (≥{benchmark})', f'Below Benchmark (<{benchmark})'],
                        'Count': [above_benchmark_baseline, below_benchmark_baseline]
                    })
                    
                    fig_baseline = px.pie(
                        baseline_data,
                        values='Count',
                        names='Category',
                        title='Baseline: Children at Benchmark',
                        color='Category',
                        color_discrete_map={
                            f'At or Above Benchmark (≥{benchmark})': '#4CAF50',
                            f'Below Benchmark (<{benchmark})': '#FF6B6B'
                        }
                    )
                    
                    st.plotly_chart(fig_baseline, key='baseline_pie_chart', use_container_width=True)
                    
                    baseline_percent = (above_benchmark_baseline / len(initial_ecd) * 100) if len(initial_ecd) > 0 else 0
                    st.metric("Baseline: At Benchmark", f"{baseline_percent:.1f}%")
                else:
                    st.info("Baseline data not available")
            
            with col2:
                if not endline_ecd.empty and 'Total cells correct - NMB ECD Endline ' in endline_ecd.columns:
                    st.subheader("Endline")
                    above_benchmark_endline = (endline_ecd['Total cells correct - NMB ECD Endline '] >= benchmark).sum()
                    below_benchmark_endline = (endline_ecd['Total cells correct - NMB ECD Endline '] < benchmark).sum()
                    
                    endline_data = pd.DataFrame({
                        'Category': [f'At or Above Benchmark (≥{benchmark})', f'Below Benchmark (<{benchmark})'],
                        'Count': [above_benchmark_endline, below_benchmark_endline]
                    })
                    
                    fig_endline = px.pie(
                        endline_data,
                        values='Count',
                        names='Category',
                        title='Endline: Children at Benchmark',
                        color='Category',
                        color_discrete_map={
                            f'At or Above Benchmark (≥{benchmark})': '#4CAF50',
                            f'Below Benchmark (<{benchmark})': '#FF6B6B'
                        }
                    )
                    
                    st.plotly_chart(fig_endline, key='endline_pie_chart', use_container_width=True)
                    
                    endline_percent = (above_benchmark_endline / len(endline_ecd) * 100) if len(endline_ecd) > 0 else 0
                    st.metric("Endline: At Benchmark", f"{endline_percent:.1f}%")
                else:
                    st.info("Endline data not available")
            
            st.divider()
            
            # ECD Centers Summary
            st.header("ECD Centers Performance")
            
            # Group by Program Name (ECD center/school)
            if 'Program Name' in endline_ecd.columns and 'Total cells correct - NMB ECD Endline ' in endline_ecd.columns:
                center_summary = endline_ecd.groupby('Program Name').agg({
                    'Participant ID': 'count',
                    'Total cells correct - NMB ECD Endline ': 'mean'
                }).reset_index()
                
                center_summary.columns = ['ECD_Center', 'Number_Assessed', 'Average_Letters_Correct']
                center_summary['Average_Letters_Correct'] = center_summary['Average_Letters_Correct'].round(1)
                center_summary = center_summary.sort_values(by='Average_Letters_Correct', ascending=False)
                
                # ECD Centers Bar Chart
                fig = px.bar(
                    center_summary,
                    x="ECD_Center",
                    y="Average_Letters_Correct",
                    title="Average Letters Correct by ECD Center (Endline)",
                    labels={"ECD_Center": "ECD Center", "Average_Letters_Correct": "Average Letters Correct"},
                    color="Average_Letters_Correct",
                    color_continuous_scale="RdYlGn"
                )
                
                fig.update_layout(
                    xaxis_title="ECD Center",
                    yaxis_title="Average Letters Correct",
                    xaxis_tickangle=-45
                )
                
                st.plotly_chart(fig, key='endline_center_performance_chart', use_container_width=True)
                
                st.dataframe(center_summary, width='stretch')

            
            st.divider()
            
            # Letter Knowledge Performance
            if 'Total cells correct - NMB ECD Endline ' in endline_ecd.columns:
                st.header("📝 Letter Knowledge Performance")
                
                # Overall performance metrics
                avg_letters = endline_ecd['Total cells correct - NMB ECD Endline '].mean()
                median_letters = endline_ecd['Total cells correct - NMB ECD Endline '].median()
                above_benchmark_count = (endline_ecd['Total cells correct - NMB ECD Endline '] >= benchmark).sum()
                above_benchmark_percent = (above_benchmark_count / len(endline_ecd) * 100) if len(endline_ecd) > 0 else 0
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Average Letters Correct", f"{avg_letters:.1f}")
                with col2:
                    st.metric("Median Letters Correct", f"{median_letters:.1f}")
                with col3:
                    st.metric(f"Children Above Benchmark (≥{benchmark})", above_benchmark_count)
                with col4:
                    st.metric("Percentage Above Benchmark", f"{above_benchmark_percent:.1f}%")
                
                # Distribution histogram
                fig_hist = px.histogram(
                    endline_ecd,
                    x='Total cells correct - NMB ECD Endline ',
                    nbins=20,
                    title="Distribution of Letter Knowledge Scores in ECD Centers (Endline)",
                    labels={'Total cells correct - NMB ECD Endline ': 'Letters Correct', 'count': 'Number of Children'}
                )
                
                # Add vertical line at benchmark
                fig_hist.add_vline(x=benchmark, line_dash="dash", line_color="red", 
                                  annotation_text=f"Benchmark ({benchmark})", annotation_position="top")
                
                st.plotly_chart(fig_hist, key='endline_distribution_histogram', use_container_width=True)
            
            st.divider()

            
            # Individual Center Analysis
            if 'Program Name' in endline_ecd.columns and endline_ecd['Program Name'].nunique() > 1:
                st.header("🔍 Individual Center Analysis")
                
                selected_center = st.selectbox(
                    "Select an ECD Center for detailed analysis:",
                    options=sorted(endline_ecd['Program Name'].unique()),
                    key="ecd_center_selector_endline"
                )
                
                center_data = endline_ecd[endline_ecd['Program Name'] == selected_center]
                
                if not center_data.empty:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader(f"📊 {selected_center} - Key Metrics")
                        center_children = len(center_data)
                        center_avg = center_data['Total cells correct - NMB ECD Endline '].mean() if 'Total cells correct - NMB ECD Endline ' in center_data.columns else 0
                        center_above_benchmark = (center_data['Total cells correct - NMB ECD Endline '] >= benchmark).sum() if 'Total cells correct - NMB ECD Endline ' in center_data.columns else 0
                        center_percent_benchmark = (center_above_benchmark / center_children * 100) if center_children > 0 else 0
                        
                        st.metric("Children Assessed", center_children)
                        st.metric("Average Letters Correct", f"{center_avg:.1f}")
                        st.metric(f"Above Benchmark (≥{benchmark})", f"{center_above_benchmark} ({center_percent_benchmark:.1f}%)")
                    
                    with col2:
                        if 'Gender' in center_data.columns:
                            st.subheader(f"👶 Gender Distribution - {selected_center}")
                            center_gender = center_data['Gender'].value_counts()
                            st.bar_chart(center_gender)

            
            # Raw Data Export
            st.divider()
            st.header("📥 Data Export")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("📊 Download ECD Summary Data", type="secondary", key="download_summary_endline"):
                    if 'Program Name' in endline_ecd.columns and 'Total cells correct - NMB ECD Endline ' in endline_ecd.columns:
                        summary_data = endline_ecd.groupby('Program Name').agg({
                            'Participant ID': 'count',
                            'Total cells correct - NMB ECD Endline ': ['mean', 'median', 'std'],
                            'Response Date': ['min', 'max']
                        }).round(2)
                        
                        csv = summary_data.to_csv()
                        st.download_button(
                            label="Download Summary CSV",
                            data=csv,
                            file_name=f"ecd_endline_summary_{dt.today().strftime('%Y-%m-%d')}.csv",
                            mime="text/csv"
                        )
            
            with col2:
                if st.button("📋 Download Full ECD Data", type="secondary", key="download_full_endline"):
                    csv = endline_ecd.to_csv(index=False)
                    st.download_button(
                        label="Download Full CSV",
                        data=csv,
                        file_name=f"ecd_endline_full_data_{dt.today().strftime('%Y-%m-%d')}.csv",
                        mime="text/csv"
                    )
            
            # Data Quality Information
            with st.expander("🔍 Data Quality Information", expanded=False):
                st.markdown("### ECD Endline Data Overview")
                st.write(f"**Total Records:** {len(endline_ecd)}")
                if 'Response Date' in endline_ecd.columns:
                    st.write(f"**Date Range:** {endline_ecd['Response Date'].min()} to {endline_ecd['Response Date'].max()}")
                if 'Program Name' in endline_ecd.columns:
                    st.write(f"**ECD Centers Included:** {', '.join(sorted(endline_ecd['Program Name'].unique()))}")
                
                # Missing data analysis
                missing_data = endline_ecd.isnull().sum()
                important_cols = ['Total cells correct - NMB ECD Endline ', 'First Name', 'Program Name', 'Gender']
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