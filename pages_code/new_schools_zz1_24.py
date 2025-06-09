import pandas as pd
import plotly.express as px
from zz_data_processing import process_zz_data_endline_new_schools, grade1_df, gradeR_df
from data_loader import load_zazi_izandi_new_schools_2024
import os
import streamlit as st

def new_schools_page():

    endline_df = load_zazi_izandi_new_schools_2024()
    endline = process_zz_data_endline_new_schools(endline_df)

    #ZZ Website colours. Going to use Yellow for EGRA and Blue for Letters Known
    YELLOW = '#ffd641'
    BLUE = '#28a1ff'
    GREY = '#b3b3b3'
    GREEN = '#32c93c'

    grade1 = endline[endline["Grade"] == 'Grade 1']
    gradeR = endline[endline["Grade"] == 'Grade R']


    st.header('SUMMARY STATS')
    c1,c2,c3 = st.columns(3)
    with c1:
        st.metric('Community\n Youth Jobs:', '28')
    with c2:
        st.metric('Children on\n Programme:', '1134')
    with c3:
        st.metric('Schools on\n Programme:', '6')

    st.info("The following 6 schools, constituting 1,134 children, began implementing Zazi iZandi in August, 2024. In only 3 months, we saw incredible gains in the children's letter knowledge. It's the second year in a row, in completely different schools, a pilot project has created huge gains in a mere 3 months.")
    st.markdown('---')
    st.header('HIGHLIGHTS')

    with st.container():
        st.subheader(f'Letter EGRA Improvement')

        df = endline.copy()

        egra_summary = df.groupby('Grade').agg({
            'EGRA Baseline': 'mean',
            'EGRA Endline': 'mean',
            'Egra Improvement Agg': 'mean'
        }).round(1).reset_index()

        # Melt the DataFrame for Plotly
        egra_summary_melted = egra_summary.melt(id_vars='Grade', value_vars=['EGRA Baseline', 'EGRA Endline'], var_name='Measurement', value_name='Score')

        # Create the Plotly bar graph with grouped bars
        egra_fig = px.bar(
            egra_summary_melted,
            x='Grade',
            y='Score',
            color='Measurement',
            barmode='group',
            labels={'Score': 'Average Score'},
            color_discrete_map={'EGRA Baseline': GREY, 'EGRA Endline': YELLOW}
        )

        st.plotly_chart(egra_fig, use_container_width=True)

    with st.expander('Click to view data:'):
        egra_summary = df.groupby('Grade').agg({
            'EGRA Baseline': 'mean',
            'EGRA Endline': 'mean',
            'Egra Improvement Agg': 'mean'
        }).round(1)
        st.dataframe(egra_summary)

    st.divider()

    with st.container():
        st.subheader("Percentage of Grade 1's On Grade Level")
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

    # GENDER STATS
    st.markdown('---')
    with st.container():
        st.subheader('Gender Improvement')
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


    school_data = grade1.groupby('School').apply(lambda x: pd.Series({
        'Endline Above Grade Level (%)': (x['EGRA Endline'] >= 40).sum() / len(x) * 100
    })).reset_index()

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
