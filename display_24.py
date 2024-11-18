import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from zz_data_processing import process_zz_data_midline, process_zz_data_endline, grade1_df, gradeR_df
from data_loader import load_zazi_izandi_2024
import os
import streamlit as st


def display_2024():
    tab1, tab2, tab3, tab4 = st.tabs(["1.0 Results", "2.0 Results", "Sessions", "Benchmarks & Research"])

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
            st.success("On average, our Grade R's scored 67% higher than Grade 1 learners not on the programme. They are more than a full year ahead of a typical South African learner. Meanwhile, our Grade 1's improved the letter EGRA scores by 170%.")
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
                "The number of Grade 1 children 'On Grade Level' for letter knowledge more than tripled, increasing from 13% to 45%. And we are only halfway through the year!")

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

        # SESSIONS

        st.markdown('---')
        st.header('Midline Sessions')

        with st.container():
            st.subheader('Sessions per School')
            st.info("Sessions are a good indicator of if the teacher is allowing the programme to occur. The classrooms and teacher assistants with low sessions are now priority areas of project mentors to address.")
            sessions = midline.groupby('School')['Total Sessions'].mean().round(1).sort_values(ascending=False)
            df = sessions.reset_index()
            df.columns = ['School', 'Average Total Sessions']

            sessions_fig = px.bar(
                df,
                x='School',
                y='Average Total Sessions',
                color_discrete_sequence=[GREY]
            )
            st.plotly_chart(sessions_fig, use_container_width=True)
            with st.expander('Click to view data'):
                st.dataframe(df)

        with st.container():
            st.subheader('Sessions per Education Assistant')
            mentor_sessions = midline.groupby('EA Name')['Total Sessions'].mean().round(1).sort_values(ascending=False)
            df = mentor_sessions.reset_index()
            df.columns = ['EA Name', 'Average Total Sessions']

            mentor_sessions_fig = px.bar(
                df,
                x='EA Name',
                y='Average Total Sessions',
                color_discrete_sequence=[GREY]
            )
            st.plotly_chart(mentor_sessions_fig, use_container_width=True)
            with st.expander('Click to view data'):
                st.dataframe(df)

        # CHECK GROUP STUFF
        st.markdown('---')
        st.header('GROUP ANALYSIS')

        with st.container():
            st.subheader('Group Analysis by School')
            st.info('Children are paired into groups of 7 depending upon their assessment scores. This enables us to teach each group "at the right level." The charts below allow one to investigate performance of different groups.')

            schools = midline['School'].value_counts().index
            school_choice = st.selectbox('Choose a School', schools, key="school_choice_group")

            df = midline[midline['School'] == school_choice]

            grade_selection = st.selectbox('Select Grade', ['All Grades', 'Grade 1', 'Grade R'],key="group_grade")
            if grade_selection == 'All Grades':
                filtered_midline = df
            else:
                filtered_midline = df[df['Grade'] == grade_selection]

            metric_selection = st.selectbox('Select Metric', ['Total Score', 'Improvement'], key="group_metric", index=1)

            if metric_selection == 'Total Score':
                metric = 'EGRA Midline'
            else:
                metric = 'Egra Improvement Agg'

            group_egra_improvement = filtered_midline.groupby(['Group']).agg({
                'EGRA Baseline': 'mean',
                'EGRA Midline': 'mean',
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
                group_egra_improvement = filtered_midline.groupby(['Group']).agg({
                    'EGRA Baseline': 'mean',
                    'EGRA Midline': 'mean',
                    'Egra Improvement Agg': 'mean',
                }).round(1).sort_values(by=metric, ascending=False)
                st.dataframe(group_egra_improvement)

    with tab2:
        st.markdown("---")
        st.title("Zazi iZandi 2.0")
        st.success(
            "Zazi IZandi 2.0 is for children that have learned all of their letter sounds. They now focus on learning to blend those letter sounds together to make, and ultimately read, words. As of Sept 17, 2024 we have 522 children on ZZ 2.0. This represents 47% of the initial Grade 1 cohort. The remaining 53% are still mastering their letter sounds on ZZ 1.0")


        st.markdown("---")
        with st.container():
            st.subheader("Average Word Reading and Non-Word Reading Scores")
            st.info(
                "The charts below compare the average scores for Word Reading and Non-Word Reading between Baseline and Endline assessments.")

            # Calculate average scores for Word Reading
            baseline_avg_word_reading = baseline2_df['B. Word reading'].mean()
            endline_avg_word_reading = endline2_df['B. Word reading'].mean()

            # Calculate average scores for Non-Word Reading
            baseline_avg_nonword_reading = baseline2_df['A.Non-word reading'].mean()
            endline_avg_nonword_reading = endline2_df['A.Non-word reading'].mean()

            # Prepare data for Word Reading bar chart
            data_word_reading = pd.DataFrame({
                'Cohort': ['Baseline', 'Endline'],
                'Average Score': [baseline_avg_word_reading, endline_avg_word_reading]
            })

            # Prepare data for Non-Word Reading bar chart
            data_nonword_reading = pd.DataFrame({
                'Cohort': ['Baseline', 'Endline'],
                'Average Score': [baseline_avg_nonword_reading, endline_avg_nonword_reading]
            })

            # Define color mapping for Cohorts
            color_discrete_map = {
                'Baseline': 'blue',
                'Endline': 'red'
            }

            # Create two columns for side-by-side display
            col1, col2 = st.columns(2)

            # Word Reading Bar Chart
            with col1:
                st.write("**Average Word Reading Scores**")
                fig_word = px.bar(
                    data_word_reading,
                    x='Cohort',
                    y='Average Score',
                    color='Cohort',
                    color_discrete_map=color_discrete_map,
                    text='Average Score',
                    title='Word Reading'
                )
                fig_word.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                fig_word.update_layout(
                    showlegend=False,
                    xaxis_title=None,
                    yaxis_title='Average Score'
                )
                st.plotly_chart(fig_word)

            # Non-Word Reading Bar Chart
            with col2:
                st.write("**Average Non-Word Reading Scores**")
                fig_nonword = px.bar(
                    data_nonword_reading,
                    x='Cohort',
                    y='Average Score',
                    color='Cohort',
                    color_discrete_map=color_discrete_map,
                    text='Average Score',
                    title='Non-Word Reading'
                )
                fig_nonword.update_traces(texttemplate='%{text:.2f}', textposition='outside')
                fig_nonword.update_layout(
                    showlegend=False,
                    xaxis_title=None,
                    yaxis_title='Average Score'
                )
                st.plotly_chart(fig_nonword)


        st.markdown("---")
        with st.container():
            st.subheader("Word Reading Buckets Pie Charts")
            st.info("The charts below bucket children's assessment scores based on the numbers of words read.")

            # Define bins and labels
            bins = [-1, 0, 5, 10, 15, 20, float('inf')]  # float('inf') represents 21+
            labels = ['0', '1-5', '6-10', '11-15', '16-20', '21+']

            # Define color mapping for each group
            color_discrete_map = {
                '0': 'darkblue',
                '1-5': 'blue',
                '6-10': 'lightblue',
                '11-15': 'green',
                '16-20': 'orange',
                '21+': 'red'
            }

            # Create two columns for side-by-side display
            col1, col2 = st.columns(2)

            # Process and display Baseline DataFrame in the left column
            with col1:
                st.write("**Baseline Word Reading Distribution**")
                df_baseline = baseline2_df.copy()
                df_baseline['Word Reading Group'] = pd.cut(
                    df_baseline['B. Word reading'], bins=bins, labels=labels, right=True
                )
                df_baseline['Word Reading Group'] = pd.Categorical(
                    df_baseline['Word Reading Group'], categories=labels, ordered=True
                )
                bucket_counts_baseline = df_baseline['Word Reading Group'].value_counts().sort_index()
                bucket_df_baseline = pd.DataFrame({
                    'Group': bucket_counts_baseline.index,
                    'Count': bucket_counts_baseline.values
                })
                fig_baseline = px.pie(
                    bucket_df_baseline,
                    values='Count',
                    names='Group',
                    title='Baseline',
                    category_orders={'Group': labels},
                    color='Group',
                    color_discrete_map=color_discrete_map,
                    hole=0.4
                )
                fig_baseline.update_layout(legend_title_text='No. of words read')

                st.plotly_chart(fig_baseline)

            # Process and display Endline DataFrame in the right column
            with col2:
                st.write("**Endline Word Reading Distribution**")
                df_endline = endline2_df.copy()
                df_endline['Word Reading Group'] = pd.cut(
                    df_endline['B. Word reading'], bins=bins, labels=labels, right=True
                )
                df_endline['Word Reading Group'] = pd.Categorical(
                    df_endline['Word Reading Group'], categories=labels, ordered=True
                )
                bucket_counts_endline = df_endline['Word Reading Group'].value_counts().sort_index()
                bucket_df_endline = pd.DataFrame({
                    'Group': bucket_counts_endline.index,
                    'Count': bucket_counts_endline.values
                })
                fig_endline = px.pie(
                    bucket_df_endline,
                    values='Count',
                    names='Group',
                    title='Endline',
                    category_orders={'Group': labels},
                    color='Group',
                    color_discrete_map=color_discrete_map,
                    hole=0.4
                )
                fig_endline.update_layout(legend_title_text='No. of words read')

                st.plotly_chart(fig_endline)

        st.markdown("---")
        with st.container():
            st.subheader("Non-Word Reading Buckets Pie Charts")
            st.info("The charts below bucket children's assessment scores based on the numbers of non-words read.")

            # Define bins and labels
            bins = [-1, 0, 5, 10, 15, 20, float('inf')]  # float('inf') represents 21+
            labels = ['0', '1-5', '6-10', '11-15', '16-20', '21+']

            # Define color mapping for each group
            color_discrete_map = {
                '0': 'darkblue',
                '1-5': 'blue',
                '6-10': 'lightblue',
                '11-15': 'green',
                '16-20': 'orange',
                '21+': 'red'
            }

            # Create two columns for side-by-side display
            col1, col2 = st.columns(2)

            # Process and display Baseline DataFrame in the left column
            with col1:
                st.write("**Baseline Non-Word Reading Distribution**")
                df_baseline = baseline2_df.copy()
                df_baseline['Non-Word Reading Group'] = pd.cut(
                    df_baseline['A.Non-word reading'], bins=bins, labels=labels, right=True
                )
                df_baseline['Non-Word Reading Group'] = pd.Categorical(
                    df_baseline['Non-Word Reading Group'], categories=labels, ordered=True
                )
                bucket_counts_baseline = df_baseline['Non-Word Reading Group'].value_counts().sort_index()
                bucket_df_baseline = pd.DataFrame({
                    'Group': bucket_counts_baseline.index,
                    'Count': bucket_counts_baseline.values
                })
                fig_baseline = px.pie(
                    bucket_df_baseline,
                    values='Count',
                    names='Group',
                    title='Baseline',
                    category_orders={'Group': labels},
                    color='Group',
                    color_discrete_map=color_discrete_map,
                    hole=0.4
                )
                fig_baseline.update_layout(legend_title_text='No. of non-words read')

                st.plotly_chart(fig_baseline)

            # Process and display Endline DataFrame in the right column
            with col2:
                st.write("**Endline Non-Word Reading Distribution**")
                df_endline = endline2_df.copy()
                df_endline['Non-Word Reading Group'] = pd.cut(
                    df_endline['A.Non-word reading'], bins=bins, labels=labels, right=True
                )
                df_endline['Non-Word Reading Group'] = pd.Categorical(
                    df_endline['Non-Word Reading Group'], categories=labels, ordered=True
                )
                bucket_counts_endline = df_endline['Non-Word Reading Group'].value_counts().sort_index()
                bucket_df_endline = pd.DataFrame({
                    'Group': bucket_counts_endline.index,
                    'Count': bucket_counts_endline.values
                })
                fig_endline = px.pie(
                    bucket_df_endline,
                    values='Count',
                    names='Group',
                    title='Endline',
                    category_orders={'Group': labels},
                    color='Group',
                    color_discrete_map=color_discrete_map,
                    hole=0.4
                )
                fig_endline.update_layout(legend_title_text='No. of non-words read')

                st.plotly_chart(fig_endline)

        with st.container():
            st.subheader("Histogram Results for ZZ 2.0")
            st.info(
                "The Non-Word assessment included 10 2-letter sounds to begin, so it is not comparable to the 'Real Word' assessment. You'll notice many kids in the 0-10 buckets for non-words b/c they could blend those two sounds together.")
            # Dropdown selection for the df
            df_choice = st.selectbox(
                "Select a cohort:",
                ("Baseline", "Endline"), key="histogram_df1"
            )

            if df_choice == "Baseline":
                df = baseline2_df.copy()
            else:
                df = endline2_df.copy()

            word_metric = st.selectbox(
                "Select a variable for the histogram:",
                ("Real Words", "Non-Words")
            )

            if word_metric == "Non-Words":
                variable = "A.Non-word reading"
            else:
                variable = "B. Word reading"

            fig = px.histogram(df, x=variable, title=f"Histogram of {variable}")

            st.plotly_chart(fig)

        with st.container():
            st.subheader("Non-word reading vs. Word reading Scores")

            df_choice = st.selectbox(
                "Select a cohort:",
                ("Baseline", "Endline")
            )

            if df_choice == "Baseline":
                df = baseline2_df.copy()
            else:
                df = endline2_df.copy()

            fig = px.scatter(df,
                             x="A.Non-word reading",
                             y="B. Word reading",
                             title="Non-word reading vs. Word reading Scores")

            st.plotly_chart(fig)

    with tab3:
        st.header("Sessions Analysis")

        # Some quick data cleaning/organizing

        df = pd.read_excel("data/Zazi iZandi Session Tracker 20092024.xlsx", sheet_name="Sesssions")
        months = ['Feb', 'Mar', 'Apr', 'May', 'Jul', 'Aug', 'Sep']

        # Prepare the list of 'Total Sessions' and 'Sessions per Day' columns
        total_sessions_cols = [f'{month}: Total Sessions' for month in months]
        sessions_per_day_cols = [f'{month}: Sessions per Day' for month in months]

        # Melt the DataFrame for 'Total Sessions'
        total_sessions_df = df.melt(
            id_vars=['School', 'EA Name'],
            value_vars=total_sessions_cols,
            var_name='Month',
            value_name='Total Sessions'
        )

        # Clean the 'Month' column to extract month names
        total_sessions_df['Month'] = total_sessions_df['Month'].str.replace(': Total Sessions', '')

        # Melt the DataFrame for 'Sessions per Day'
        sessions_per_day_df = df.melt(
            id_vars=['School', 'EA Name'],
            value_vars=sessions_per_day_cols,
            var_name='Month',
            value_name='Sessions per Day'
        )

        # Clean the 'Month' column to extract month names
        sessions_per_day_df['Month'] = sessions_per_day_df['Month'].str.replace(': Sessions per Day', '')

        # Merge the two DataFrames on 'School', 'EA Name', and 'Month'
        merged_df = pd.merge(
            total_sessions_df,
            sessions_per_day_df,
            on=['School', 'EA Name', 'Month']
        )

        # Set the categorical data type for 'Month' with the correct order
        month_categories = ['Feb', 'Mar', 'Apr', 'May', 'Jul', 'Aug', 'Sep']
        merged_df['Month'] = pd.Categorical(
            merged_df['Month'],
            categories=month_categories,
            ordered=True
        )

        # Streamlit Code
        with st.container():
            st.subheader("Session Metrics per Month")
            # Metric selection
            metric = st.selectbox('Select Metric', ['Total Sessions', 'Sessions per Day'])

            # Use the entire merged_df without filtering
            plot_df = merged_df.copy()

            # Group and aggregate data
            if metric == 'Total Sessions':
                plot_data = plot_df.groupby('Month')[metric].sum().reset_index()
            else:
                plot_data = plot_df.groupby('Month')[metric].mean().reset_index()

            # Create the bar chart
            fig = px.bar(
                plot_data,
                x='Month',
                y=metric,
                title=f'{metric} by Month'
            )

            # Ensure months are in order
            fig.update_xaxes(categoryorder='array', categoryarray=month_categories)

            # Display the chart
            st.plotly_chart(fig)

        st.markdown("---")
        with st.container():
            # Streamlit app
            st.subheader('Average Sessions per Day per School')

            months = ['Feb', 'Mar', 'Apr', 'May', 'Jul', 'Aug', 'Sep']
            month_options = ['All Months'] + months

            # Month selection
            selected_month = st.selectbox('Select Month', month_options)

            # Filter data based on the selected month
            if selected_month == 'All Months':
                filtered_df = sessions_per_day_df.copy()
            else:
                filtered_df = sessions_per_day_df[sessions_per_day_df['Month'] == selected_month]

            # Calculate the average 'Sessions per Day' per school
            average_sessions = filtered_df.groupby('School')['Sessions per Day'].mean().reset_index()

            # Sort the schools from highest to lowest average 'Sessions per Day'
            average_sessions = average_sessions.sort_values(by='Sessions per Day', ascending=False)

            # Create the bar chart
            fig = px.bar(
                average_sessions,
                x='School',
                y='Sessions per Day',
                title=f"Average Sessions per Day per School ({selected_month})",
                labels={'Sessions per Day': 'Average Sessions per Day'}
            )

            # Update layout to rotate x-axis labels if needed
            fig.update_layout(xaxis_tickangle=-45)

            # Display the chart
            st.plotly_chart(fig)
        st.markdown("---")
        with st.container():
            with st.container():
                # Streamlit app
                st.subheader('Average Sessions per Day per School')

                months = ['Feb', 'Mar', 'Apr', 'May', 'Jul', 'Aug', 'Sep']
                month_options = ['All Months'] + months

                # Month selection
                selected_month = st.selectbox('Select Month', month_options, key="ea_month")

                # Filter data based on the selected month
                if selected_month == 'All Months':
                    filtered_df = sessions_per_day_df.copy()
                else:
                    filtered_df = sessions_per_day_df[sessions_per_day_df['Month'] == selected_month]

                # Calculate the average 'Sessions per Day' per school
                average_sessions = filtered_df.groupby('EA Name')['Sessions per Day'].mean().reset_index()

                # Sort the schools from highest to lowest average 'Sessions per Day'
                average_sessions = average_sessions.sort_values(by='Sessions per Day', ascending=False)

                # Create the bar chart
                fig = px.bar(
                    average_sessions,
                    x='EA Name',
                    y='Sessions per Day',
                    title=f"Average Sessions per Day per EA for ({selected_month})",
                    labels={'Sessions per Day': 'Average Sessions per Day'}
                )

                # Update layout to rotate x-axis labels if needed
                fig.update_layout(xaxis_tickangle=-45)

                # Display the chart
                st.plotly_chart(fig)
            st.markdown("---")
            with st.container():
                st.subheader('Sessions per Day Over Time by EA')

                # Use the entire DataFrame without filtering
                filtered_df = sessions_per_day_df.copy()

                # Check if the DataFrame is not empty
                if filtered_df.empty:
                    st.warning('No data available.')
                else:
                    # Create the line chart
                    fig = px.line(
                        filtered_df,
                        x='Month',
                        y='Sessions per Day',
                        color='EA Name',
                        markers=True,
                        title='Sessions per Day per EA Over Time'
                    )

                    # Ensure months are in the correct order on the x-axis
                    fig.update_xaxes(categoryorder='array', categoryarray=months)

                    # Customize layout
                    fig.update_layout(
                        xaxis_title='Month',
                        yaxis_title='Sessions per Day',
                        legend_title='EA Name',
                        hovermode='x unified'
                    )

                    # Display the chart
                    st.plotly_chart(fig)
    with tab4:
        # FURTHER STATS
        st.markdown('---')
        st.header("Benchmarks & Research")
        with st.container():
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("isiXhosa National Benchmarks")
                st.write("""
                    - Grade 1 Letter Knowledge: 40 letters per minute
                    - Grade 2 Passage Reading: 20 words per minute
                    - Grade 3 Passage Reading: 35 words per minute
                    """)
        with st.container():
            st.subheader('Research & Findings')
            with st.expander("Spaull, Pretorious 2022"):
                st.write("""
                        - Fewer than 50% of South African learners in no-fee schools know all the letters of the alphabet by the end of Grade 1 and less than 50% can reach a minimal fluency threshold in Grade 2.
                        - Being alphabetically illiterate in Grade 1 sets learners back by at least four years, reaching a Grade 3 benchmark (60 wcpm) only in Grade 7.
                        - Across different samples, large proportions of Grade 6 learners (35–46%) do not reach fluency benchmarks for African languages set for the Grade 3 level.
                        - Between 50-70% of EC learners finishing Grade 1 (or starting Grade 2) cannot pronounce a single complex consonant sound.
                        - More than 55% of Nguni and Sesotho-Setswana language learner samples assessed pre-pandemic cannot read a single word correctly from a grade-level text by the end of Grade 1.
                        - There’s a HUGE gap between boys & girls as grades go on .The gap becomes exacerbated even for the strongest 25% of girls & boys.
                        - By the end of Grade 2, 29-54% of children hit the 20 words per minute bench mark in Nguni languages.
                        """)
                st.image("assets/EC isiXhosa Against Benchmarks.png", width=600)
            with st.expander("DoE EFAL Technical Report (2022)"):
                st.write("""
                        - Grade 2: 21% of learners nationally were unable to read one word correctly. Median fluency including non-readers was 11 correct words per minute (cwpm), while the benchmark is set at 30+ cwpm.
                        - Grade 3: Between 19-34% of learners nationally could not read one word. Median fluency including non-readers ranged from 13-34 cwpm, with a benchmark of 50+ cwpm.
                        - Grade 4: 8-30% of learners nationally could not read one word. Median fluency including non-readers was between 21-46 cwpm, while the benchmark was 70+ cwpm.
                        - Grade 5: Median fluency including non-readers was 62 cwpm, with a benchmark of 90+ cwpm.
                        - In the Eastern Cape, by the end of Grade 4, 8-15% of learners meet the benchmark of 90 cwpm.
                        """)
            with st.expander("Wordworks (2023)"):
                st.write("""
                        - Only 27% of EC Grade 1 children hit the Grade 1 benchmark of 40lpm by end of the year.
                        - 51% of EC Grade 1 children knew zero letter sounds to begin the year.
                        - Only 23% of EC Grade 1 children could identify the first sounds of 3 words correctly (phonelogical awareness).
                        """)
                st.image("assets/WW Letter Sound Eastern Cape (Grade 1).png", width=800)
            with st.expander("DoE 2022"):
                st.write("""
                        - More than 55% of Nguni and Sesotho-Setswana language learner samples assessed pre-pandemic cannot read a single word correctly from a grade-level text by the end of Grade 1.
                        - In Nguni languages, only at the 75th percentile is a minimum Grade 3 luency benchmark of 35 wcpm being reached in Grade 3 (or start of Grade 4) learner samples, with median fluency at 20–33 wcpm and 11–47% meeting the benchmark.
                        - It is very sobering that, of the Grade  6 samples, 35–46% do not meet Grade 3 fluency benchmarks and 7–27% fail to meet Grade 2 luency benchmarks.
                        - Among Nguni language samples, about 7–32% of learners assessed at the end of Grade  1 or the start of Grade  2 were meeting the benchmark of 40 lscpm.
                        - By the end of grade 3, most learners (53% to 76%, depending on the sample) have reached the lower threshold (20 cwpm) and approximately a quarter have reached the benchmark (35 cwpm).
                        - At the start of Grade 1, 51% and 42% of the Eastern Cape and North West learner samples respectively have no alphabetic knowledge, despite most of these learners having attended Grade
                        - Across the two samples, 16% and 32% sound fewer than 26 letters per minute by the end of Grade  2.
                        - However, at the beginning of Grade  1, half of learners in an Eastern Cape sample (49%) and two-thirds of learners in a Mpumalanga sample (68%) were unable to provide the initial sound of any of three simple words read aloud by the assessor in a Nguni language (kodwa, misa, and vuka in the Eastern Cape; busa, gogo, and wena in Mpumalanga). Only 23% and 7% of learners in the Eastern Cape and Mpumalanga samples respectively were able to correctly identify the initial sound of all three words.
                        """)

            with st.expander("Masinyusane (2023 EGRA)"):
                st.write("""
                        - Midway through Grade 1, EC children knew 12.7 letters and averaged 23.7 letters per minute in isiXhosa (sample size 1100).
                        - Midway through Grade 1, 22% of EC children had met the benchmark of 40 letter sounds per minute in Grade 1 (sample size 1100).
                        - Midway through Grade %, EC children know 3.4 letters and averaged 5.1 letters per minute (sample size 775).
                        """)
            with st.expander("Masinyusane (2024 EGRA)"):
                st.write("""
                        - EC Grade 1 children knew 5.2 letters and scored a 9.3 on their letter EGRA to begin the year (sample size 388).
                        - EC Grade R children know 0.7 letters and scored 0.9 on their letter EGRA to begin the year (sample size 1101).
                        - Midway through Grade 1, EC children (not on our programme) knew 5.5 letters and averaged 17.7 letters per minute in isiXhosa (sample size 588).
                        - Midway through Grade 1, 14% of EC children (not on our programme) had met the benchmark of 40 letter sounds per minute in Grade 1 (sample size 588).
                        - Midway through Grade R, EC children (not on our programme) know 2.7 letters and averaged 5.2 letters per minute (2023 Masi EGRA; sample size 440).

                        """)
        st.markdown("---")

        # FURTHER STATS
        with st.container():
            st.header('FURTHER ANALYSIS')

            with st.expander('Validity of Results'):
                st.success(
                    'The following analysis demonstrates a strong correlation between the improvements in Letters Known and the Letters EGRA assessments, reinforcing the validity of our Zazi iZandi results. The two metrcis were captured via different assessment methodologies, making the high correlation even more impressive. The two metrics have a Spearman CoEfficient of 0.933.')
                # Drop rows with NaN or infinite values
                clean_data = midline[['Letters Learned', 'Egra Improvement Agg', 'Grade']].dropna()
                x = clean_data['Letters Learned']
                y = clean_data['Egra Improvement Agg']

                # Create scatter plot
                fig, ax = plt.subplots(figsize=(10, 6))
                scatter = sns.scatterplot(data=clean_data, x='Letters Learned', y='Egra Improvement Agg', hue='Grade',
                                          palette='viridis', ax=ax)

                # Fit OLS model
                X = sm.add_constant(x)  # Add constant for OLS
                model = sm.OLS(y, X).fit()
                predictions = model.predict(X)

                # Plot the OLS trendline
                ax.plot(x, predictions, color='red', label='OLS Trendline')

                # Update layout
                ax.set_title('Scatter Plot of Letters Learned vs EGRA Improvement')
                ax.set_xlabel('Letters Learned')
                ax.set_ylabel('EGRA Improvement Agg')
                ax.grid(False)
                ax.legend()

                st.pyplot(fig)

            with st.expander('Visualizing Progress: KDE Plot'):
                st.success(
                    'The blue wave shows how many children knew zero (or few) letters to begin the programme. The orange wave illustrates the substantial change in the number of children that know many letters in the first half of 2024. ')
                fig, ax = plt.subplots(figsize=(10, 6))

                # Plot KDE for Baseline Letters Known
                sns.kdeplot(midline['Baseline Letters Known'], fill=True, label='Beginning Letters Known', ax=ax)

                # Plot KDE for Midline Letters Known
                sns.kdeplot(midline['Midline Letters Known'], fill=True, label='Midline Letters Known', ax=ax)

                ax.set_title('Beginning and Midline Letters Known')
                ax.set_xlabel('Score')
                ax.set_ylabel('Density')
                ax.legend()

                st.pyplot(fig)

            with st.expander('Cohort Performance'):
                st.success(
                    "This illustrates the substaintial progress that ALL children made, regardless of their level at the baseline. Children who knew nothing progressed as fast as children who already knew some of their letters. Note that final cohort already knew 19+ letters, so there wasn't much room for improvement.")
                fig, ax = plt.subplots(figsize=(10, 6))
                grouped = midline.groupby('Letter Cohort_baseline')['Letters Learned'].mean().round(1)
                cohort_order = ['0-5', '6-12', '13-18', '19+']
                result = grouped.reindex(cohort_order)
                ax.bar(result.index, result.values, edgecolor='black')

                ax.set_title('Average Letters Learned by Baseline Letter Cohort')
                ax.set_xlabel('Letters Known Baseline (by Cohort)')
                ax.set_ylabel('Average Letters Learned')

                # Annotate bars with values
                for i, v in enumerate(result.values):
                    ax.text(i, v + 0.1, str(v), ha='center', va='bottom')
                st.pyplot(fig)

            with st.expander('Letters Known Charted'):
                st.success(
                    "This illustrates the letters the children have mastered. We teach the letter sounds in order from left to right, so we would expect the highest values on the left to slope downwards to the right. It's interesting that this isn't exactly the case.")
                # List of letters in the correct order
                letters = ['a', 'e', 'i', 'o', 'u', 'b', 'l', 'm', 'k', 'p', 's', 'h', 'z', 'n',
                           'd', 'y', 'f', 'w', 'v', 'x', 'g', 't', 'q', 'r', 'c', 'j']

                letter_counts = midline[letters].applymap(lambda x: 1 if pd.notna(x) else 0).sum()

                letter_df = pd.DataFrame({'Letter': letter_counts.index, 'Count': letter_counts.values})

                fig = px.bar(letter_df, x='Letter', y='Count', title='Count of Letters Known',
                             labels={'Count': 'Total Count of Letters Known'})
                st.plotly_chart(fig)

            with st.expander('Percent of Children Assessed'):
                st.success('We successfully assessed over 90% of children for both baseline & midline results.')
                midline_assessed = midline['EGRA Midline'].notna().sum()
                midline_assessed_percent = (midline_assessed / midline['Mcode'].count() * 100).round(1)

                baseline_assessed = baseline['EGRA Baseline'].notna().sum()
                baseline_assessed_percent = (baseline_assessed / baseline['Mcode'].count() * 100).round(1)

                data = {
                    'Time Period': ['Midline Assessed', 'Baseline Assessed'],
                    '% Assessed': [midline_assessed_percent, baseline_assessed_percent]
                }

                df = pd.DataFrame(data)
                st.dataframe(df)
            with st.expander('Children Over 40 EGRA by School'):
                filtered_df = midline[midline['EGRA Midline'] >= 40]

                # Group by 'School' and count the number of children per school
                result_df = filtered_df.groupby('School').size().sort_values(ascending=False).reset_index(name='Count')

                # Display the resulting DataFrame
                st.dataframe(result_df)

            with st.expander('Groups Over 40 EGRA by School'):
                grouped_means = midline.groupby(['School', 'EA Name', 'Group'])['EGRA Midline'].mean().reset_index()

                # Filter for groups where the mean 'EGRA Midline' is >= 40
                filtered_groups = grouped_means[grouped_means['EGRA Midline'] >= 40]

                # Now, count how many groups per school meet the criteria
                result_df = filtered_groups.groupby('School').size().sort_values(ascending=False).reset_index(
                    name='Count')

                # Display the resulting DataFrame
                st.dataframe(result_df)
