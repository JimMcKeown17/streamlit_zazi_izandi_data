import pandas as pd
import plotly.express as px
from zz_data_processing import process_zz_data_midline, process_zz_data_endline, grade1_df, gradeR_df
from data_loader import load_zazi_izandi_2024
import os
import streamlit as st

st.set_page_config(layout="wide", page_title="ZZ Data Portal")


tab1, tab2 = st.tabs(["Endline Results", "Midline Results"])

with tab1:
    # Import dataframes
    baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df = load_zazi_izandi_2024()
    base_dir = os.path.dirname(os.path.abspath(__file__))

    #ZZ Website colours. Going to use Yellow for EGRA and Blue for Letters Known
    YELLOW = '#ffd641'
    BLUE = '#28a1ff'
    GREY = '#b3b3b3'
    GREEN = '#32c93c'

    midline, baseline = process_zz_data_midline(baseline_df, midline_df, sessions_df)
    endline = process_zz_data_endline(endline_df)
    grade1 = grade1_df(endline)
    gradeR = gradeR_df(endline)

    # START PAGE NOW

    col1, col2 = st.columns(2)
    with col1:
        st.image('assets/Zazi iZandi logo.png', width=250)
    with col2:
        st.title('2024 Results')
    # FEATURE STATS
    st.header('SUMMARY STATS')
    c1,c2,c3 = st.columns(3)
    with c1:
        st.metric('Community\n Youth Jobs:', '82')
    with c2:
        st.metric('Children on\n Programme:', '3490')
    with c3:
        st.metric('Schools on\n Programme:', '16')
    st.markdown('---')
    st.header('HIGHLIGHTS')

    with st.container():
        st.subheader(f'Letter EGRA Improvement')
        st.success("On average, our Grade R's perform similar to a Grade 1 learner not on the programme. They are more than a full year ahead of a typical South African learner. Meanwhile, our Grade 1's improved the letter EGRA scores by 179%.")
        assessment_choice = st.selectbox("Choose an Assessment Period:", ['Endline', 'Midline', 'September'])
        if assessment_choice == "Endline":
            assessment = "Endline"
            egra_type = "EGRA Endline"
            df = endline.copy()
        elif assessment_choice == 'September':
            assessment = "September"
            egra_type = "EGRA Midline Sept"
            df = endline.copy()
        else:
            assessment = "Midline"
            egra_type = "EGRA Midline"
            df = midline.copy()


        egra_summary = df.groupby('Grade').agg({
            'EGRA Baseline': 'mean',
            egra_type: 'mean',
            'Egra Improvement Agg': 'mean'
        }).round(1).reset_index()

        # Melt the DataFrame for Plotly
        egra_summary_melted = egra_summary.melt(id_vars='Grade', value_vars=['EGRA Baseline', egra_type], var_name='Measurement', value_name='Score')

        # Create the Plotly bar graph with grouped bars
        egra_fig = px.bar(
            egra_summary_melted,
            x='Grade',
            y='Score',
            color='Measurement',
            barmode='group',
            labels={'Score': 'Average Score'},
            color_discrete_map={'EGRA Baseline': GREY, egra_type: YELLOW}
        )

        st.plotly_chart(egra_fig, use_container_width=True)

    with st.expander('Click to view data:'):
        egra_summary = df.groupby('Grade').agg({
            'EGRA Baseline': 'mean',
            egra_type: 'mean',
            'Egra Improvement Agg': 'mean'
        }).round(1)
        st.dataframe(egra_summary)
    with st.expander('View Results Side-By-Side'):
        st.subheader('Letter EGRA Improvement')
        # Filter for Grade 1 and Grade R
        filtered_df = endline[endline['Grade'].isin(['Grade 1', 'Grade R'])]

        # Calculate mean results for the four assessments
        egra_summary = filtered_df.groupby('Grade').agg({
            'EGRA Baseline': 'mean',
            'EGRA Midline': 'mean',
            'EGRA Endline': 'mean',
            'EGRA Midline Sept': 'mean'
        }).round(1).reset_index()

        # Melt the DataFrame for Plotly
        egra_summary_melted = egra_summary.melt(id_vars='Grade',
                                                value_vars=['EGRA Baseline', 'EGRA Midline', 'EGRA Midline Sept',
                                                            'EGRA Endline'], var_name='Measurement',
                                                value_name='Score')

        # Ensure the measurements are ordered as Baseline, Midline, September, Endline
        measurement_order = ['EGRA Baseline', 'EGRA Midline', 'EGRA Midline Sept', 'EGRA Endline']
        egra_summary_melted['Measurement'] = pd.Categorical(egra_summary_melted['Measurement'],
                                                            categories=measurement_order, ordered=True)

        # Create the Plotly bar graph with grouped bars and custom colors
        color_discrete_map = {
            'EGRA Baseline': 'rgba(173, 216, 230, 0.8)',  # very light blue
            'EGRA Midline': 'rgba(135, 206, 235, 0.8)',  # light blue
            'EGRA Midline Sept': 'rgba(70, 130, 180, 0.8)',  # blue
            'EGRA Endline': 'rgba(0, 0, 139, 0.8)'  # dark blue
        }

        egra_fig = px.bar(
            egra_summary_melted,
            x='Grade',
            y='Score',
            color='Measurement',
            barmode='group',
            labels={'Score': 'Average Score'},
            title='EGRA Results for Grade 1 and Grade R',
            color_discrete_map=color_discrete_map
        )

        st.plotly_chart(egra_fig, use_container_width=True)
    st.divider()

    with st.container():
        st.subheader("Percentage of Grade 1's On Grade Level")
        st.success(
            "The number of Grade 1 children 'On Grade Level' for letter knowledge more than quadrupled, increasing from 13% to 53%!")

        # Calculate percentages for baseline
        baseline_40_or_more = (grade1['EGRA Baseline'] >= 40).sum()
        baseline_less_than_40 = (grade1['EGRA Baseline'] < 40).sum()
        total_baseline = baseline_40_or_more + baseline_less_than_40

        baseline_40_or_more_percent = (baseline_40_or_more / total_baseline).round(3) * 100
        baseline_less_than_40_percent = (baseline_less_than_40 / total_baseline).round(3) * 100

        # Calculate percentages for midline
        endline_40_or_more = (grade1['EGRA Endline'] >= 40).sum()
        endline_less_than_40 = (grade1['EGRA Endline'] < 40).sum()
        total_endline = endline_40_or_more + endline_less_than_40

        endline_40_or_more_percent = (endline_40_or_more / total_endline).round(3) * 100
        endline_less_than_40_percent = (endline_less_than_40 / total_endline).round(3) * 100

        # Create DataFrame
        data = {
            'Above Grade Level': [baseline_40_or_more_percent, endline_40_or_more_percent]
        }

        df = pd.DataFrame(data, index=['Baseline', 'Endline'])

        # Melt the DataFrame for Plotly
        df_melted = df.reset_index().melt(id_vars='index', value_vars=['Above Grade Level'],
                                          var_name='Score Category', value_name='Percentage')

        # Create the Plotly bar graph
        grade_level_fig = px.bar(
            df_melted,
            x='index',
            y='Percentage',
            color='Score Category',
            barmode='group',
            labels={'index': 'Assessment', 'Percentage': 'Percentage (%)'},
            color_discrete_map={'Above Grade Level': GREEN}

        )
        # Add horizontal line at y=27 with label 'South Africa Average'
        grade_level_fig.add_hline(y=27, line_dash='dash', line_color='red', annotation_text='South Africa Average',
                           annotation_position='top left')

        st.plotly_chart(grade_level_fig, use_container_width=True)

        with st.expander('Click to view data:'):
            st.dataframe(df)
    st.divider()

    with st.container():
        st.subheader('Letters Known Improvement (Midline)')
        st.success('On their midline assessments, children improved their letter knowledge by 193% and learned, on average, 8.5 letters. Endline data still being captured.')
        letter_summary = midline.groupby('Grade').agg({
            'Baseline Letters Known': 'mean',
            'Midline Letters Known': 'mean',
        }).round(1).reset_index()

        # Attempt to Melt
        letter_summary_melted = letter_summary.melt(id_vars="Grade",
                                                    value_vars=['Baseline Letters Known', 'Midline Letters Known'],
                                                    var_name="Measurement", value_name="Letters Known")

        # Create the Plotly bar graph with grouped bars
        letter_fig = px.bar(
            letter_summary_melted,
            x='Grade',
            y='Letters Known',
            color='Measurement',
            barmode='group',
            labels={'Letters Known': 'Average Letter Known'},
            color_discrete_map={'Baseline Letters Known': GREY, 'Midline Letters Known': BLUE}

        )
        st.plotly_chart(letter_fig, use_container_width=True)

        with st.expander('Click to view data:'):
            letter_summary = midline.groupby('Grade').agg({
                'Baseline Letters Known': 'mean',
                'Midline Letters Known': 'mean',
            }).round(1)
            st.dataframe(letter_summary)


    # GENDER STATS
    st.markdown('---')
    with st.container():
        st.subheader('Gender Improvement')
        st.success('South Africa has the highest gender disparity in literacy in the world (for countries measured in PIRLS) with our boys drastically underperforming our girls. We are keeping a close eye on our boys performance and hope to contribute towards closing this gap.')
        grade_selection = st.selectbox('Select Grade', ['All Grades', 'Grade 1', 'Grade R'],key="gender", index=1)
        metric_selection = st.selectbox('Select Metric', ['Total Score', 'Improvement'], key="gender_metric", index=1)

        if grade_selection == 'All Grades':
            filtered_endline = endline
        else:
            filtered_endline = endline[endline['Grade'] == grade_selection]

        if metric_selection == 'Total Score':
            metric = 'EGRA Endline'
        else:
            metric = 'Egra Improvement Agg'

        gender_egra_improvement = filtered_endline.groupby(['Gender']).agg({
            'EGRA Baseline': 'mean',
            'EGRA Endline': 'mean',
            'Egra Improvement Agg': 'mean',
        }).round(1).sort_values(by=metric, ascending=False).reset_index()

        school_fig = px.bar(
            gender_egra_improvement,
            x='Gender',
            y=metric,
            color_discrete_sequence=[YELLOW]
        )
        st.plotly_chart(school_fig, use_container_width=True)

        with st.expander('Click to view data:'):
            gender_egra_improvement = filtered_endline.groupby(['Gender']).agg({
                'EGRA Baseline': 'mean',
                'EGRA Endline': 'mean',
                'Egra Improvement Agg': 'mean',
            }).round(1).sort_values(by=metric, ascending=False)
            st.dataframe(gender_egra_improvement)

    # SCHOOLS

    st.markdown('---')
    st.header('SCHOOL PERFORMANCE')

    with st.container():
        st.subheader('School Level EGRA Improvement')

        grade_selection = st.selectbox('Select Grade', ['All Grades', 'Grade 1', 'Grade R'],key="egra")
        if grade_selection == 'All Grades':
            filtered_endline = endline
        else:
            filtered_endline = endline[endline['Grade'] == grade_selection]

        school_egra_improvement = filtered_endline.groupby(['School']).agg({
            'EGRA Baseline': 'mean',
            'EGRA Endline': 'mean',
            'Egra Improvement Agg': 'mean',
        }).round(1).sort_values(by='Egra Improvement Agg', ascending=False).reset_index()

        school_fig = px.bar(
            school_egra_improvement,
            x='School',
            y='Egra Improvement Agg',
            color_discrete_sequence=[YELLOW]
        )
        st.plotly_chart(school_fig, use_container_width=True)

        with st.expander('Click to view data:'):
            school_egra_improvement = filtered_endline.groupby(['School']).agg({
                'EGRA Baseline': 'mean',
                'EGRA Endline': 'mean',
                'Egra Improvement Agg': 'mean',
            }).round(1).sort_values(by='Egra Improvement Agg', ascending=False)
            st.dataframe(school_egra_improvement)

    with st.container():
        st.subheader('School Level Letter Improvement (Midline)')

        grade_selection = st.selectbox('Select Grade', ['All Grades', 'Grade 1', 'Grade R'], key="letters")
        if grade_selection == 'All Grades':
            filtered_midline = midline
        else:
            filtered_midline = midline[midline['Grade'] == grade_selection]

        schools_letters_learned = filtered_midline.groupby('School')['Letters Learned'].mean().round(1).sort_values(ascending=False).reset_index()

        school_letters_fig = px.bar(
            schools_letters_learned,
            x='School',
            y='Letters Learned',
            color_discrete_sequence=[BLUE]
        )
        st.plotly_chart(school_letters_fig, use_container_width=True)

        with st.expander('Click to view data:'):
            letters_per_school = filtered_midline.groupby(['School']).agg({
                'Baseline Letters Known': 'mean',
                'Midline Letters Known': 'mean',
                'Letters Learned': 'mean',
            }).round(1).sort_values(by='Letters Learned', ascending=False)
            st.dataframe(letters_per_school)

    with st.container():
        st.subheader("Chart of Children's Results By School")
        schools = endline['School'].value_counts().index
        choice = st.selectbox('Choose a School', schools)
        df = endline[endline['School'] == choice]

        grade_selection = st.selectbox('Select Grade', ['All Grades', 'Grade 1', 'Grade R'], key="grade_by_School")
        if grade_selection == 'All Grades':
            df = df
        else:
            df = df[df['Grade'] == grade_selection]

        metric_selection = st.selectbox('Select Metric', [ 'EGRA Endline','Endline Letters Known'], key="metric_by_School")


        fig = px.histogram(data_frame=df, x=metric_selection, nbins=20, color_discrete_sequence=[BLUE])
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('---')

    with st.container():
        st.subheader("Percentage of Grade 1's On Grade Level by School")
        st.success(
            "The number of Grade 1 children 'On Grade Level' for letter knowledge more than tripled, increasing from 13% to 45%. And we are only halfway through the year!")
        schools = endline['School'].value_counts().index
        school_choice = st.selectbox('Choose a School', schools, key="school_choice")

        df = grade1[grade1['School'] == school_choice]

        # Calculate percentages for baseline
        baseline_40_or_more = (df['EGRA Baseline'] >= 40).sum()
        baseline_less_than_40 = (df['EGRA Baseline'] < 40).sum()
        total_baseline = baseline_40_or_more + baseline_less_than_40

        baseline_40_or_more_percent = (baseline_40_or_more / total_baseline).round(3) * 100
        baseline_less_than_40_percent = (baseline_less_than_40 / total_baseline).round(3) * 100

        # Calculate percentages for midline
        endline_40_or_more = (df['EGRA Endline'] >= 40).sum()
        endline_less_than_40 = (df['EGRA Endline'] < 40).sum()
        total_endline = endline_40_or_more + endline_less_than_40

        endline_40_or_more_percent = (endline_40_or_more / total_endline).round(3) * 100
        endline_less_than_40_percent = (endline_less_than_40 / total_endline).round(3) * 100

        # Create DataFrame
        data = {
            'Below Grade Level': [baseline_less_than_40_percent, endline_less_than_40_percent],
            'Above Grade Level': [baseline_40_or_more_percent, endline_40_or_more_percent]
        }

        df = pd.DataFrame(data, index=['Baseline', 'Midline'])

        # Melt the DataFrame for Plotly
        df_melted = df.reset_index().melt(id_vars='index', value_vars=['Below Grade Level', 'Above Grade Level'],
                                          var_name='Score Category', value_name='Percentage')

        # Create the Plotly bar graph
        grade_level_fig = px.bar(
            df_melted,
            x='index',
            y='Percentage',
            color='Score Category',
            barmode='group',
            labels={'index': 'Assessment', 'Percentage': 'Percentage (%)'},
            color_discrete_map={'Below Grade Level': GREY, 'Above Grade Level': GREEN}

        )

        st.plotly_chart(grade_level_fig, use_container_width=True)

        with st.expander('Click to view data:'):
            st.dataframe(df)

    st.markdown("---")

    # Calculate the percentage of students 'Above Grade Level' for midline for each school
    school_data = grade1.groupby('School').apply(lambda x: pd.Series({
        'Endline Above Grade Level (%)': (x['EGRA Endline'] >= 40).sum() / len(x) * 100
    })).reset_index()

    # Sort by 'Midline Above Grade Level (%)'
    school_data_sorted = school_data.sort_values(by='Endline Above Grade Level (%)', ascending=False)

    # Create the Plotly bar graph
    school_fig = px.bar(
        school_data_sorted,
        x='School',
        y='Endline Above Grade Level (%)',
        color='School',
        labels={'School': 'School', 'Endline Above Grade Level (%)': 'Percentage (%)'},
        title='Percentage of Grade 1 Students Above Grade Level by School'
    )

    with st.container():
        st.subheader("Percentage of Grade 1's Above Grade Level by School")
        st.plotly_chart(school_fig, use_container_width=True)

        with st.expander('Click to view data:'):
            st.dataframe(school_data_sorted)

    # TEACHER ASSISTANTS

    st.markdown('---')
    st.header('TEACHER ASSISTANT PERFORMANCE')

    with st.container():
        st.subheader('Top Performing Teaching Assistants')

        grade_selection = st.selectbox('Select Grade', ['All Grades', 'Grade 1', 'Grade R'])
        if grade_selection == 'All Grades':
            filtered_endline = endline
        else:
            filtered_endline = endline[endline['Grade'] == grade_selection]

        ta_performance = filtered_endline.groupby(['School', 'EA Name']).agg({
            # 'Total Sessions': 'mean',
            # 'Baseline Letters Known': 'mean',
            # 'Letters Known': 'mean',
            # 'Letters Learned': 'mean',
            'EGRA Baseline': 'mean',
            'EGRA Endline': 'mean',
            'Egra Improvement Agg': 'mean',
        }).round(1).sort_values(by='Egra Improvement Agg', ascending=False).reset_index()
        ta_fig = px.bar(
            ta_performance.head(15),
            x='EA Name',
            y='Egra Improvement Agg',
            color_discrete_sequence=[YELLOW]
        )
        st.plotly_chart(ta_fig, use_container_width=True)


        with st.expander('Click to view data:'):
            st.subheader('Performance of Teaching Assistants')
            TA_performance = filtered_endline.groupby(['School', 'EA Name']).agg({
                # 'Total Sessions': 'mean',
                # 'Baseline Letters Known': 'mean',
                # 'Letters Known': 'mean',
                # 'Letters Learned': 'mean',
                'EGRA Baseline': 'mean',
                'EGRA Endline': 'mean',
                'Egra Improvement Agg': 'mean',
            }).round(1).sort_values(by='Egra Improvement Agg', ascending=False)
            st.dataframe(TA_performance)

    with st.container():
        st.subheader('Teaching Assistants With Underperforming Children')
        st.warning('The project mentors will be retraining (and potentially replacing) these Teacher Assistants.')
        digressed = endline[endline['Egra Improvement Agg'] < 3]
        result = digressed.groupby('EA Name').agg({
            'Surname': 'count',
            # 'Total Sessions': 'mean',
            # 'Baseline Letters Known': 'mean',
            # 'Midline Letters Known': 'mean',
            # 'Letters Learned': 'mean',
            'EGRA Baseline': 'mean',
            'EGRA Endline': 'mean',
            'Egra Improvement Agg': 'mean'
        }).round(1).sort_values(by='Surname', ascending=False).reset_index().head(15)
        result = result.rename(columns={'Surname': 'Number of Under-performing Children'})

        digressed_fig = px.bar(
            result,
            x='EA Name',
            y='Number of Under-performing Children',
            color_discrete_sequence=['#de6f7c']
        )
        st.plotly_chart(digressed_fig, use_container_width=True)

        with st.expander('Click to view data:'):
            result = digressed.groupby('EA Name').agg({
                'Surname': 'count',
                # 'Total Sessions': 'mean',
                # 'Baseline Letters Known': 'mean',
                # 'Midline Letters Known': 'mean',
                # 'Letters Learned': 'mean',
                'EGRA Baseline': 'mean',
                'EGRA Endline': 'mean',
                'Egra Improvement Agg': 'mean'
            }).round(1)
            result = result.rename(columns={'Surname': 'Number of Children'}).sort_values(by='Number of Children', ascending=False)
            st.dataframe(result)

    # CHECK GROUP STUFF
    st.markdown('---')
    st.header('GROUP ANALYSIS')

    with st.container():
        st.subheader('Group Analysis by School')
        st.info('Children are paired into groups of 7 depending upon their assessment scores. This enables us to teach each group "at the right level." The charts below allow one to investigate performance of different groups.')

        schools = endline['School'].value_counts().index
        school_choice = st.selectbox('Choose a School', schools, key="school_choice_group")

        df = endline[endline['School'] == school_choice]

        grade_selection = st.selectbox('Select Grade', ['All Grades', 'Grade 1', 'Grade R'],key="group_grade")
        if grade_selection == 'All Grades':
            filtered_endline = df
        else:
            filtered_endline = df[df['Grade'] == grade_selection]

        metric_selection = st.selectbox('Select Metric', ['Total Score', 'Improvement'], key="group_metric", index=1)

        if metric_selection == 'Total Score':
            metric = 'EGRA Endline'
        else:
            metric = 'Egra Improvement Agg'

        group_egra_improvement = filtered_endline.groupby(['Group']).agg({
            'EGRA Baseline': 'mean',
            'EGRA Endline': 'mean',
            'Egra Improvement Agg': 'mean',
        }).round(1).sort_values(by=metric, ascending=False).reset_index()

        school_fig = px.bar(
            group_egra_improvement,
            x='Group',
            y=metric,
            # color="EA Name"
            color_discrete_sequence=[YELLOW]
        )
        st.plotly_chart(school_fig, use_container_width=True)

        with st.expander('Click to view data:'):
            group_egra_improvement = filtered_endline.groupby(['Group']).agg({
                'EGRA Baseline': 'mean',
                'EGRA Endline': 'mean',
                'Egra Improvement Agg': 'mean',
            }).round(1).sort_values(by=metric, ascending=False)
            st.dataframe(group_egra_improvement)
    st.divider()

    # st.subheader("Further Analysis")
    # with st.expander("2.0 Learner Endline Results"):
    #
    #     st.subheader('Letter EGRA Improvement for 2.0 Learners')
    #     # Filter for Grade 1 and 2.0 Check
    #     filtered_df_2_0 = endline[(endline['Grade'] == 'Grade 1') & (endline['2.0 Check'] == "Yes")]
    #
    #     # Calculate mean results for the four assessments
    #     egra_summary_2_0 = filtered_df_2_0.agg({
    #         'EGRA Baseline': 'mean',
    #         'EGRA Midline': 'mean',
    #         'EGRA Endline': 'mean',
    #         'EGRA Midline Sept': 'mean'
    #     }).round(1).reset_index(name='Score')
    #
    #     # Rename columns for easier plotting
    #     egra_summary_2_0.rename(columns={'index': 'Measurement'}, inplace=True)
    #
    #     # Ensure the measurements are ordered as Baseline, Midline, September, Endline
    #     measurement_order = ['EGRA Baseline', 'EGRA Midline', 'EGRA Midline Sept', 'EGRA Endline']
    #     egra_summary_2_0['Measurement'] = pd.Categorical(egra_summary_2_0['Measurement'], categories=measurement_order, ordered=True)
    #
    #     # Sort by EGRA Endline score
    #     egra_summary_2_0 = egra_summary_2_0.sort_values(by='Score', ascending=True)
    #
    #     # Create the Plotly bar graph with grouped bars and custom colors
    #     egra_fig_2_0 = px.bar(
    #         egra_summary_2_0,
    #         x='Measurement',
    #         y='Score',
    #         color='Measurement',
    #         barmode='group',
    #         labels={'Score': 'Average Score'},
    #         title='EGRA Results for 2.0 Children',
    #         color_discrete_map=color_discrete_map
    #     )
    #
    #     # Update bar width to make bars wider
    #     egra_fig_2_0.update_traces(width=0.5)
    #
    #     st.plotly_chart(egra_fig_2_0, use_container_width=True)
    #
    # with st.expander("1.0 Only Learner Endline Results"):
    #
    #     st.subheader("Letter EGRA Improvement for 1.0 Learners That Didn't Move on to 2.0")
    #     # Filter for Grade 1 and 2.0 Check
    #     filtered_df_2_0 = endline[(endline['Grade'] == 'Grade 1') & (endline['2.0 Check'] != "Yes")]
    #
    #     # Calculate mean results for the four assessments
    #     egra_summary_2_0 = filtered_df_2_0.agg({
    #         'EGRA Baseline': 'mean',
    #         'EGRA Midline': 'mean',
    #         'EGRA Endline': 'mean',
    #         'EGRA Midline Sept': 'mean'
    #     }).round(1).reset_index(name='Score')
    #
    #     # Rename columns for easier plotting
    #     egra_summary_2_0.rename(columns={'index': 'Measurement'}, inplace=True)
    #
    #     # Define the desired order of measurements
    #     measurement_order = ['EGRA Baseline', 'EGRA Midline', 'EGRA Midline Sept', 'EGRA Endline']
    #
    #     # Set 'Measurement' as a categorical type with the specified order
    #     egra_summary_2_0['Measurement'] = pd.Categorical(
    #         egra_summary_2_0['Measurement'],
    #         categories=measurement_order,
    #         ordered=True
    #     )
    #
    #
    #     # Create the Plotly bar graph with grouped bars and custom colors
    #     egra_fig_2_0 = px.bar(
    #         egra_summary_2_0,
    #         x='Measurement',
    #         y='Score',
    #         color='Measurement',
    #         barmode='group',
    #         labels={'Score': 'Average Score'},
    #         title='EGRA Results for 2.0 Children',
    #         color_discrete_map=color_discrete_map
    #     )
    #
    #     # Update bar width to make bars wider
    #     egra_fig_2_0.update_traces(width=0.5)
    #
    #     # Update layout to ensure the x-axis respects the categorical order
    #     egra_fig_2_0.update_layout(
    #         xaxis={'categoryorder': 'array', 'categoryarray': measurement_order}
    #     )
    #
    #     st.plotly_chart(egra_fig_2_0, use_container_width=True)
    # with st.expander("EGRA Improvement by EA Name: Midline to Endline"):
    #
    #     st.subheader("Improvement in EGRA Scores from Midline to Endline by EA Name")
    #
    #     # 1. Group the data by 'EA Name' and calculate mean scores
    #     improvement_df = endline.groupby('EA Name').agg({
    #         'EGRA Midline': 'mean',
    #         'EGRA Endline': 'mean'
    #     }).reset_index()
    #
    #     # 2. Calculate the improvement
    #     improvement_df['Improvement'] = improvement_df['EGRA Endline'] - improvement_df['EGRA Midline']
    #
    #     # 3. Round the improvement for better readability
    #     improvement_df['Improvement'] = improvement_df['Improvement'].round(2)
    #
    #     # 4. Sort the DataFrame in ascending order of improvement
    #     improvement_df = improvement_df.sort_values(by='Improvement', ascending=True)
    #
    #     # 5. Create the Plotly bar chart
    #     improvement_fig = px.bar(
    #         improvement_df,
    #         x='EA Name',
    #         y='Improvement',
    #         color='Improvement',
    #         color_continuous_scale='Blues',
    #         labels={'Improvement': 'EGRA Improvement (Endline - Midline)', 'EA Name': 'EA Name'},
    #         title='EGRA Score Improvement by EA Name',
    #         text='Improvement'  # Display the improvement value on each bar
    #     )
    #
    #     # 6. Customize the layout for better readability
    #     improvement_fig.update_layout(
    #         xaxis_title='EA Name',
    #         yaxis_title='Improvement in EGRA Score',
    #         xaxis_tickangle=-45,  # Rotate x-axis labels if they are long
    #         coloraxis_colorbar=dict(
    #             title="Improvement",
    #             ticksuffix=" pts"
    #         ),
    #         uniformtext_minsize=8,
    #         uniformtext_mode='hide'
    #     )
    #
    #     # 7. Adjust the text on bars for better visibility
    #     improvement_fig.update_traces(texttemplate='%{text:.2f}', textposition='outside')
    #
    #     # 8. Update layout to ensure the bars are ordered as per the DataFrame
    #     improvement_fig.update_layout(
    #         xaxis={'categoryorder': 'array', 'categoryarray': improvement_df['EA Name']}
    #     )
    #
    #     # 9. Display the Plotly chart in Streamlit
    #     st.plotly_chart(improvement_fig, use_container_width=True)
    #
    #     # Optional: Display the processed data
    #     st.write(improvement_df)
with tab2:
    st.write("Midline results coming soon...")