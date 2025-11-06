import streamlit as st

st.set_page_config(page_title="Table of Contents", page_icon="📑", layout="wide")

st.title("📑 Data Portal Table of Contents")
st.markdown("---")

# M&E Data Sources Section
st.header("🔬 Monitoring & Evaluation Framework")
st.markdown("""
Our data portal integrates three complementary data sources to provide a comprehensive view of program implementation and impact. 
By triangulating these different perspectives, we ensure data quality, validate findings, and gain deeper insights into what's working.
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📱 EA Daily Sessions")
    st.markdown("""
    **Education Assistant Submissions**
    
    Daily session logs submitted by EAs capturing:
    - Letters taught each day
    - Groups worked with
    - Participant attendance
    - Session duration
    
    *Real-time implementation data*
    """)

with col2:
    st.markdown("### 📋 EGRA Assessments")
    st.markdown("""
    **Formal Learning Assessments**
    
    Standardized EGRA tests conducted every 6 months:
    - Baseline
    - Midline
    - Endline
    
    Measures letter sound knowledge per minute (and, in some cases, word and non-word reading fluency.)
    
    *Validated learning outcomes*
    """)

with col3:
    st.markdown("### 👁️ Mentor Visits")
    st.markdown("""
    **Site Observation Data**
    
    Trained mentors conduct site visits documenting:
    - Implementation quality
    - EA performance observations
    - School environment factors
    - Qualitative feedback
    - Action items and support needs
    
    *Contextual insights and quality*
    """)

st.info("""
**Triangulation Approach:** We cross-reference all three data sources to validate findings. For example, if EA session data 
shows high activity but assessment results are low, mentor visit observations help us understand implementation quality issues. 
This multi-source approach ensures we're not just counting sessions, but understanding real impact.
""")

st.markdown("*Each page below is tagged with icons showing its primary data source: 📱 EA Daily Sessions | 📋 EGRA Assessments | 👁️ Mentor Visits | 🔄 Multiple Sources*")

st.markdown("---")

# Pilot Streams Section
st.header("🧪 Program Evolution: Pilot Streams")
st.markdown("""
Each year, we test something new as we iterate towards the best possible program. ⚠️ Note that we expect drastically different results from different cohorts as some are full-time youth, some are part-time youth (eg SEF 4 days a week, half day), some are government TAs given one hour per day for ZZ, while others are government TAs given only one hour per week by their teacher.
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### 📅 2023: Pilot Launch")
    st.markdown("""
    **ZZ 1.0 - Letter Sounds**
    
    *August - November 2023*
    
    - **12 schools**
    - **52 youth**
    - **1,897 children**
    
    Initial pilot testing the letter sounds curriculum and delivery model.
    """)

with col2:
    st.markdown("### 📊 2024: Expansion & Innovation")
    st.markdown("""
    **ZZ 1.0 + 2.0 Launch**
    
    *February - October 2024*
    
    **Cohort 1:**
    - 16 schools, 82 youth, 3,490 children
    - Improved 1.0 with lessons learned
    
    **Cohort 2 (mid-year):**
    - 6 schools, 28 youth, 1,134 children
    
    **Innovations:**
    - Introduced ZZ 2.0 (blending & word reading)
    - First ECD center pilot
    """)

with col3:
    st.markdown("### 🚀 2025: Scale & Diversification")
    st.markdown("""
    **ZZ 1.0 at Scale**
    
    **Multiple Testing Streams:**
    
    *SEF Youth (Feb-May):*
    - 42 schools, 73 part-time TAs
    - 4 days/week model
    
    *Government TAs - NMB (Aug-Oct):*
    - 460 trained, ~30-40% uptake
    - Rushed intervention with no time, huge data variance.
    - Huge partnership gain with Dept of Education though.
    
    *Government TAs - East London:*
    - 50 schools, 1 month foundation
    
    *ECD Year-Long:*
    - 16 centers, 353 children
    
    **New Tests:**
    - 3 languages
    - SurveyCTO & TeamPact tools
    - Full-time vs part-time models
    """)

st.markdown("---")

# Check if user is logged in to show internal sections
if 'user' in st.session_state and st.session_state.user:
    # Project Management Section (Internal Only)
    st.header("📊 Project Management")
    st.info("🔒 Internal Access Only")
    
    st.markdown("""
    ### 📱 Letter Progress (Cohort 2)
    Tracks letter teaching progress for the July 2025 cohort (Cohort 2) showing which letters have been taught across schools and education assistants based on recent sessions.
    
    ### 📱 Letter Progress Detailed (Cohort 2)
    Detailed school-by-school analysis of letter teaching progress with tabs for each school showing individual education assistant progress through the letter sequence.
    
    **Tabs:** Individual school tabs (dynamically generated based on participating schools)
    
    ### 👁️ Mentor Visits (Cohort 2)
    Comprehensive mentor visit tracking and analysis for the July 2025 cohort.
    
    **Tabs:**
    - 📊 **Quantitative Dashboard** - Visit frequency, coverage metrics, and school-level visit patterns
    - 📝 **Qualitative Analysis** - Review of mentor observations, feedback themes, and action items. Powered by AI.
    
    ### 📱 AutomatedCheck: Same Letter Groups
    Quality assurance tool that flags education assistants who are teaching the same letter groups across multiple consecutive sessions, which may indicate data entry issues or implementation challenges.
    
    ### 📱 Automated Check: Moving Too Fast
    Quality control page that identifies education assistants who may be progressing through the letter sequence faster than recommended, potentially compromising learning quality.
    """)
    
    st.markdown("---")

# 2025 Results Section
st.header("📈 2025 Results")

st.markdown("""
### 📋 2025 Midline NMB (Cohort 1)
**Public Access** - Comprehensive midline assessment results for Nelson Mandela Bay Cohort 1 (January 2025 start) showing literacy improvement from baseline to midline.

This page includes multiple sections:
- Overall letter EGRA improvement charts comparing baseline to midline
- Letter knowledge performance by grade (Grade 1 and Grade R)
- Percentage of Grade 1 learners achieving benchmark (40+ letters)
- School-by-school performance comparisons
- Individual school deep-dive analysis
- Baseline vs Midline comparison charts with benchmark percentages
- TA performance rankings (by improvement and by absolute midline scores)
- Data export tools for letter trackers and combined datasets

### 📋 2025 Baseline NMB (Cohort 1)
**Public Access** - Initial baseline assessment results for Nelson Mandela Bay Cohort 1 showing starting literacy levels across schools and grades.

Key sections:
- Summary metrics (total children assessed, TA coverage)
- EGRA scores by grade level
- School-level performance breakdown
- Grade 1 benchmark achievement (percentage at 40+ letters)
- School-by-school Grade 1 benchmark analysis
- Data export tools

### 📋 2025 ECD NMB Midline
**Public Access** - Midline assessment results specifically for Early Childhood Development (ECD) centers in Nelson Mandela Bay showing literacy progress for pre-school learners.
""")

if 'user' in st.session_state and st.session_state.user:
    st.info("🔒 Additional Internal Pages")
    st.markdown("""
    ### 📋 2025 Baseline NMB (Cohort 2)
    **Internal Access** - Baseline assessment results for Nelson Mandela Bay Cohort 2 (July 2025 start).
    
    **Tabs:**
    - **Baseline - July** - Initial assessment results and literacy levels for the July cohort
    - **Endline - Oct** (if available) - End-of-program assessment results
    
    ### 🔄 2025 Endline NMB (Cohort 2)
    **Internal Access** - Comprehensive endline analysis for Nelson Mandela Bay Cohort 2 with cohort-based performance tracking and quality flag analysis. Combines assessment data with session attendance data.
    
    **Tabs:**
    - 📊 **Overview** - High-level summary of endline assessment results
    - 🎯 **Cohort Performance** - Analysis of performance by session attendance cohorts (0-30, 30-60, 60-90, 90+ sessions)
    - 🚩 **Quality Flag Impact** - Analysis of data quality flags and their impact on results
    - 🔬 **Cross-Analysis** - Multi-dimensional analysis combining cohort, grade, and other factors
    - 🏫 **School & EA Insights** - School-level and education assistant performance breakdown
    - 📈 **Data Explorer** - Interactive data exploration tools
    
    ### 📱 2025 Sessions NMB (Cohort 2)
    **Internal Access** - Comprehensive session tracking and analysis for Nelson Mandela Bay Cohort 2 showing education assistant activity, implementation quality, and school-level session patterns.
    
    **Tabs:**
    - **EA Sessions Analysis** - Education assistant session counts, frequency, and activity patterns
    - **Children's Sessions** - Analysis of session participation from children's perspective including sessions received per child, average weekly sessions, and participation distribution
    - **Group Sessions** - Analysis of group-level session patterns and attendance (NMB schools only)
    - **EA Implementation Status** - Current implementation status by EA including session counts and last session date
    - **DataQuest Schools** - Session analysis for DataQuest partner schools
    
    ### 📱 2025 Sessions East London (Cohort 2)
    **Internal Access** - Dedicated session tracking and analysis page for East London schools showing EA activity, school-level performance, and implementation patterns specific to the East London region.
    
    **Tabs:**
    - **EA Sessions Analysis** - Education assistant session counts, frequency, and activity patterns for East London schools
    - **Group Session Analysis** - Analysis of group-level session patterns and attendance for East London schools
    
    ### 📋 2025 Baseline BCM (Cohort 2)
    **Internal Access** - Baseline assessment results for East London Cohort 2 schools showing initial literacy levels across the East London implementation area.
    """)

st.markdown("---")

# 2024 Results Section
st.header("📊 2024 Results")

st.markdown("""
### 📋 2024 Letter Knowledge
**Public Access** - Comprehensive analysis of letter knowledge development throughout 2024, showing baseline to endline improvement in letter recognition and letter sound knowledge.

### 📋 2024 Word Reading
**Public Access** - Word reading assessment results for 2024 showing progression in reading fluency and comprehension skills.

### 📋 2024 New Schools
**Public Access** - Special analysis of schools that joined the program in 2024, tracking their implementation journey and initial results.

### 📱 2024 Session Analysis
**Public Access** - Analysis of session delivery patterns, frequency, and quality throughout the 2024 program year.
""")

st.markdown("---")

# 2023 Results Section
st.header("📅 2023 Results")

st.markdown("""
### 📋 2023 Results
**Public Access** - Historical results from the 2023 program year showing literacy outcomes and program impact from the previous cohort.
""")

st.markdown("---")

# Research & Benchmarks Section
st.header("🔍 Research & Benchmarks")

st.markdown("""
### 📚 Research & Benchmarks
**Public Access** - Contextual research and literacy benchmarks comparing Zazi iZandi results to South African national averages and international literacy standards.
""")

if 'user' in st.session_state and st.session_state.user:
    st.info("🔒 Additional Internal Pages")
    st.markdown("""
    ### 🤖 Zazi Bot
    **Internal Access** - AI-powered assistant for analyzing program data, answering questions about implementation, and providing insights based on the data portal contents. Cannot yet access 2025 data, waiting for all results.
    
    ### 📋 Year Comparisons
    **Internal Access** - Cross-year analysis comparing program results across 2023, 2024, and 2025 cohorts to identify trends and measure sustained impact.
    """)

st.markdown("---")

# Additional Information
st.header("ℹ️ Navigation Tips")
st.markdown("""
- **Data Source Icons**: Each page is tagged with 📱 (EA Sessions), 📋 (EGRA Assessments), 👁️ (Mentor Visits), or 🔄 (Multiple Sources)
- **Public Pages** are accessible without login and showcase key program results
- **Internal Pages** (marked with 🔒) require login and provide detailed operational data and quality monitoring tools
- Pages with **Tabs** allow you to switch between different views or data subsets within the same page
- Use the **sidebar** to navigate between pages
- Most pages include **data export** options to download analysis results
- **Triangulation**: Compare findings across different data sources to validate results and gain deeper insights
""")

st.markdown("---")

# Login prompt if not logged in
if 'user' not in st.session_state or not st.session_state.user:
    st.warning("🔒 Log in to access additional internal pages and detailed operational tools.")

