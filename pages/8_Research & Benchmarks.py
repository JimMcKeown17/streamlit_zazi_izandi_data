import streamlit as st
import plotly.express as px
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels.api as sm
from zz_data_processing import process_zz_data_midline, process_zz_data_endline, grade1_df, gradeR_df
from data_loader import load_zazi_izandi_2024
import os
import pandas as pd

st.set_page_config(layout="wide", page_title="ZZ Data Portal")


baseline_df, midline_df, sessions_df, baseline2_df, endline_df, endline2_df = load_zazi_izandi_2024()
base_dir = os.path.dirname(os.path.abspath(__file__))

# ZZ Website colours. Going to use Yellow for EGRA and Blue for Letters Known
YELLOW = '#ffd641'
BLUE = '#28a1ff'
GREY = '#b3b3b3'
GREEN = '#32c93c'

midline, baseline = process_zz_data_midline(baseline_df, midline_df, sessions_df)
endline = process_zz_data_endline(endline_df)
grade1 = grade1_df(endline)
gradeR = gradeR_df(endline)

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
    st.header('FURTHER ANALYSIS (2023)')

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
