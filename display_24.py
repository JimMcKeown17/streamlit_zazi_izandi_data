import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from zz_data_processing import process_zz_data, grade1_df, gradeR_df
from data_loader import load_zazi_izandi_2024
import os
import streamlit as st

def display_2024():
    # Import dataframes
    baseline_df, midline_df, sessions_df = load_zazi_izandi_2024()
    base_dir = os.path.dirname(os.path.abspath(__file__))


    #ZZ Website colours. Going to use Yellow for EGRA and Blue for Letters Known
    YELLOW = '#ffd641'
    BLUE = '#28a1ff'
    GREY = '#b3b3b3'
    GREEN = '#32c93c'


    midline, baseline = process_zz_data(baseline_df, midline_df, sessions_df)
    grade1 = grade1_df(midline)
    gradeR = gradeR_df(midline)

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
        st.metric('Community\n Youth Jobs:', '52')
    with c2:
        st.metric('Children on\n Programme:', '1895')
    with c3:
        st.metric('Schools on\n Programme:', '12')
    st.markdown('---')
    st.header('HIGHLIGHTS')

    with st.container():
        st.subheader('Letter EGRA Improvement')
        st.success('On average, the children improved their Letter EGRA scores '
                   'by 214% (17 points).')
        egra_summary = midline.groupby('Grade').agg({
            'EGRA Baseline': 'mean',
            'EGRA Midline': 'mean',
            'Egra Improvement Agg': 'mean'
        }).round(1).reset_index()

        # Melt the DataFrame for Plotly
        egra_summary_melted = egra_summary.melt(id_vars='Grade', value_vars=['EGRA Baseline', 'EGRA Midline'], var_name='Measurement', value_name='Score')

        # Create the Plotly bar graph with grouped bars
        egra_fig = px.bar(
            egra_summary_melted,
            x='Grade',
            y='Score',
            color='Measurement',
            barmode='group',
            labels={'Score': 'Average Score'},
            color_discrete_map={'EGRA Baseline': GREY, 'EGRA Midline': YELLOW}
        )

        st.plotly_chart(egra_fig, use_container_width=True)

    with st.expander('Click to view data:'):
        egra_summary = midline.groupby('Grade').agg({
            'EGRA Baseline': 'mean',
            'EGRA Midline': 'mean',
            'Egra Improvement Agg': 'mean'
        }).round(1)
        st.dataframe(egra_summary)

    st.markdown("---")

    with st.container():
        st.subheader('Letters Known Improvement')
        st.success('Children improved their letter knowledge by 193% and learned, on average, 8.5 letters')
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

    st.markdown('---')

    with st.container():
        st.subheader("Percentage of Grade 1's On Grade Level")
        st.success("The number of Grade 1 children 'On Grade Level' for letter knowledge more than tripled, increasing from 13% to 45%. And we are only halfway through the year!")

        # Calculate percentages for baseline
        baseline_40_or_more = (grade1['EGRA Baseline'] >= 40).sum()
        baseline_less_than_40 = (grade1['EGRA Baseline'] < 40).sum()
        total_baseline = baseline_40_or_more + baseline_less_than_40

        baseline_40_or_more_percent = (baseline_40_or_more / total_baseline).round(3) * 100
        baseline_less_than_40_percent = (baseline_less_than_40 / total_baseline).round(3) * 100

        # Calculate percentages for midline
        midline_40_or_more = (grade1['EGRA Midline'] >= 40).sum()
        midline_less_than_40 = (grade1['EGRA Midline'] < 40).sum()
        total_midline = midline_40_or_more + midline_less_than_40

        midline_40_or_more_percent = (midline_40_or_more / total_midline).round(3) * 100
        midline_less_than_40_percent = (midline_less_than_40 / total_midline).round(3) * 100

        # Create DataFrame
        data = {
            'Below Grade Level': [baseline_less_than_40_percent, midline_less_than_40_percent],
            'Above Grade Level': [baseline_40_or_more_percent, midline_40_or_more_percent]
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

    # GENDER STATS
    st.markdown('---')
    with st.container():
        st.subheader('Gender Improvement')
        st.success('South Africa has the highest gender disparity in literacy in the world (for countries measured in PIRLS) with our boys drastically underperforming our girls. We are keeping a close eye on our boys performance and hope to contribute towards closing this gap.')
        grade_selection = st.selectbox('Select Grade', ['All Grades', 'Grade 1', 'Grade R'],key="gender", index=1)
        metric_selection = st.selectbox('Select Metric', ['Total Score', 'Improvement'], key="gender_metric", index=1)

        if grade_selection == 'All Grades':
            filtered_midline = midline
        else:
            filtered_midline = midline[midline['Grade'] == grade_selection]

        if metric_selection == 'Total Score':
            metric = 'EGRA Midline'
        else:
            metric = 'Egra Improvement Agg'

        gender_egra_improvement = filtered_midline.groupby(['Gender']).agg({
            'EGRA Baseline': 'mean',
            'EGRA Midline': 'mean',
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
            gender_egra_improvement = filtered_midline.groupby(['Gender']).agg({
                'EGRA Baseline': 'mean',
                'EGRA Midline': 'mean',
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
            filtered_midline = midline
        else:
            filtered_midline = midline[midline['Grade'] == grade_selection]

        school_egra_improvement = filtered_midline.groupby(['School']).agg({
            'EGRA Baseline': 'mean',
            'EGRA Midline': 'mean',
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
            school_egra_improvement = filtered_midline.groupby(['School']).agg({
                'EGRA Baseline': 'mean',
                'EGRA Midline': 'mean',
                'Egra Improvement Agg': 'mean',
            }).round(1).sort_values(by='Egra Improvement Agg', ascending=False)
            st.dataframe(school_egra_improvement)

    with st.container():
        st.subheader('School Level Letter Improvement')

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
        schools = midline['School'].value_counts().index
        choice = st.selectbox('Choose a School', schools)
        df = midline[midline['School'] == choice]

        grade_selection = st.selectbox('Select Grade', ['All Grades', 'Grade 1', 'Grade R'], key="grade_by_School")
        if grade_selection == 'All Grades':
            df = df
        else:
            df = df[df['Grade'] == grade_selection]

        metric_selection = st.selectbox('Select Metric', ['Midline Letters Known', 'EGRA Midline'], key="metric_by_School")


        fig = px.histogram(data_frame=df, x=metric_selection, nbins=20, color_discrete_sequence=[BLUE])
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('---')

    with st.container():
        st.subheader("Percentage of Grade 1's On Grade Level by School")
        st.success(
            "The number of Grade 1 children 'On Grade Level' for letter knowledge more than tripled, increasing from 13% to 45%. And we are only halfway through the year!")
        schools = midline['School'].value_counts().index
        school_choice = st.selectbox('Choose a School', schools, key="school_choice")

        df = grade1[grade1['School'] == school_choice]

        # Calculate percentages for baseline
        baseline_40_or_more = (df['EGRA Baseline'] >= 40).sum()
        baseline_less_than_40 = (df['EGRA Baseline'] < 40).sum()
        total_baseline = baseline_40_or_more + baseline_less_than_40

        baseline_40_or_more_percent = (baseline_40_or_more / total_baseline).round(3) * 100
        baseline_less_than_40_percent = (baseline_less_than_40 / total_baseline).round(3) * 100

        # Calculate percentages for midline
        midline_40_or_more = (df['EGRA Midline'] >= 40).sum()
        midline_less_than_40 = (df['EGRA Midline'] < 40).sum()
        total_midline = midline_40_or_more + midline_less_than_40

        midline_40_or_more_percent = (midline_40_or_more / total_midline).round(3) * 100
        midline_less_than_40_percent = (midline_less_than_40 / total_midline).round(3) * 100

        # Create DataFrame
        data = {
            'Below Grade Level': [baseline_less_than_40_percent, midline_less_than_40_percent],
            'Above Grade Level': [baseline_40_or_more_percent, midline_40_or_more_percent]
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
        'Midline Above Grade Level (%)': (x['EGRA Midline'] >= 40).sum() / len(x) * 100
    })).reset_index()

    # Sort by 'Midline Above Grade Level (%)'
    school_data_sorted = school_data.sort_values(by='Midline Above Grade Level (%)', ascending=False)

    # Create the Plotly bar graph
    school_fig = px.bar(
        school_data_sorted,
        x='School',
        y='Midline Above Grade Level (%)',
        color='School',
        labels={'School': 'School', 'Midline Above Grade Level (%)': 'Percentage (%)'},
        title='Percentage of Grade 1 Students Above Grade Level by School'
    )

    # Streamlit app
    with st.container():
        st.subheader("Percentage of Grade 1's Above Grade Level by School (Midline)")
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
            filtered_midline = midline
        else:
            filtered_midline = midline[midline['Grade'] == grade_selection]

        ta_performance = filtered_midline.groupby(['School', 'EA Name']).agg({
            'Total Sessions': 'mean',
            'Baseline Letters Known': 'mean',
            'Letters Known': 'mean',
            'Letters Learned': 'mean',
            'EGRA Baseline': 'mean',
            'EGRA Midline': 'mean',
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
            TA_performance = filtered_midline.groupby(['School', 'EA Name']).agg({
                'Total Sessions': 'mean',
                'Baseline Letters Known': 'mean',
                'Letters Known': 'mean',
                'Letters Learned': 'mean',
                'EGRA Baseline': 'mean',
                'EGRA Midline': 'mean',
                'Egra Improvement Agg': 'mean',
            }).round(1).sort_values(by='Egra Improvement Agg', ascending=False)
            st.dataframe(TA_performance)

    with st.container():
        st.subheader('Teaching Assistants With Underperforming Children')
        st.warning('The project mentors will be retraining (and potentially replacing) these Teacher Assistants.')
        digressed = midline[midline['Egra Improvement Agg'] < 3]
        result = digressed.groupby('EA Name').agg({
            'Surname': 'count',
            'Total Sessions': 'mean',
            'Baseline Letters Known': 'mean',
            'Midline Letters Known': 'mean',
            'Letters Learned': 'mean',
            'EGRA Baseline': 'mean',
            'EGRA Midline': 'mean',
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
                'Total Sessions': 'mean',
                'Baseline Letters Known': 'mean',
                'Midline Letters Known': 'mean',
                'Letters Learned': 'mean',
                'EGRA Baseline': 'mean',
                'EGRA Midline': 'mean',
                'Egra Improvement Agg': 'mean'
            }).round(1)
            result = result.rename(columns={'Surname': 'Number of Children'}).sort_values(by='Number of Children', ascending=False)
            st.dataframe(result)

    # SESSIONS

    st.markdown('---')
    st.header('SESSIONS')

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
    # FURTHER STATS
    st.markdown('---')
    st.header('FURTHER ANALYSIS')

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
        result_df = filtered_groups.groupby('School').size().sort_values(ascending=False).reset_index(name='Count')

        # Display the resulting DataFrame
        st.dataframe(result_df)

    with st.expander('Validity of Results'):
        st.success('The following analysis demonstrates a strong correlation between the improvements in Letters Known and the Letters EGRA assessments, reinforcing the validity of our Zazi iZandi results. The two metrcis were captured via different assessment methodologies, making the high correlation even more impressive. The two metrics have a Spearman CoEfficient of 0.933.')
        # Drop rows with NaN or infinite values
        clean_data = midline[['Letters Learned', 'Egra Improvement Agg', 'Grade']].dropna()
        x = clean_data['Letters Learned']
        y = clean_data['Egra Improvement Agg']

        # Create scatter plot
        fig, ax = plt.subplots(figsize=(10, 6))
        scatter = sns.scatterplot(data=clean_data, x='Letters Learned', y='Egra Improvement Agg', hue='Grade', palette='viridis', ax=ax)

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

        # Display the plot in Streamlit
        st.pyplot(fig)

    with st.expander('Visualizing Progress: KDE Plot'):
        st.success('The blue wave shows how many children knew zero (or few) letters to begin the programme. The orange wave illustrates the substantial change in the number of children that know many letters in the first half of 2024. ')
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
        st.success("This illustrates the substaintial progress that ALL children made, regardless of their level at the baseline. Children who knew nothing progressed as fast as children who already knew some of their letters. Note that final cohort already knew 19+ letters, so there wasn't much room for improvement.")
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
        st.success("This illustrates the letters the children have mastered. We teach the letter sounds in order from left to right, so we would expect the highest values on the left to slope downwards to the right. It's interesting that this isn't exactly the case.")
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