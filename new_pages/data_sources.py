import streamlit as st
import pandas as pd

st.title("📊 Data Sources Documentation")
st.caption("Comprehensive overview of all data sources in the Zazi iZandi Data Portal")

st.markdown("---")

# Last Updated
st.info("**Last Updated:** May 26, 2026")

# Introduction
with st.expander("📖 About This Documentation", expanded=False):
    st.markdown("""
    This page provides a complete reference for understanding where all data in the portal comes from.
    Use this to:
    - Understand the data pipeline architecture
    - Troubleshoot data loading issues
    - Plan data migrations and updates
    - Onboard new team members
    """)

# Database Tables Summary
st.header("🗄️ Database Tables Summary")

db_tables = [
    {
        "Table Name": "teampact_sessions_complete",
        "Status": "✅ Production",
        "Purpose": "Session attendance, participation, letters taught",
        "Update Method": "Nightly cron job",
        "Used By": "Session analysis, Letter progress, Quality checks"
    },
    {
        "Table Name": "teampact_assessment_endline_2025",
        "Status": "✅ Production",
        "Purpose": "Endline EGRA assessments, cohort analysis",
        "Update Method": "Django management",
        "Used By": "Endline analysis, Cohort analysis"
    },
    {
        "Table Name": "assessments_2026",
        "Status": "✅ Production",
        "Purpose": "2026 baseline and primary midline EGRA assessments",
        "Update Method": "Nightly sync_assessments_2026",
        "Used By": "2026 baseline, 2026 midline, ECD baseline"
    },
    {
        "Table Name": "assessment_cells_2026",
        "Status": "✅ Production",
        "Purpose": "2026 cell-level EGRA results",
        "Update Method": "Nightly sync_assessment_cells_2026",
        "Used By": "Letter-level analysis"
    },
    {
        "Table Name": "sessions_2026",
        "Status": "✅ Production",
        "Purpose": "2026 session attendance and letter progress",
        "Update Method": "Nightly sync_teampact_sessions_2026",
        "Used By": "2026 sessions, letter progress"
    },
    {
        "Table Name": "mentor_visits_2026",
        "Status": "✅ Production",
        "Purpose": "2026 mentor visit observations",
        "Update Method": "Nightly sync_mentor_visits_2026",
        "Used By": "2026 mentor visits"
    },
    {
        "Table Name": "teampact_nmb_sessions",
        "Status": "⚠️ Legacy",
        "Purpose": "Original session data table",
        "Update Method": "Legacy API sync",
        "Used By": "Being phased out"
    },
    {
        "Table Name": "api_tasession",
        "Status": "✅ Active",
        "Purpose": "TA mentor visit observations",
        "Update Method": "Django app",
        "Used By": "TA mentor tracking"
    },
    {
        "Table Name": "api_teampactsession",
        "Status": "🔍 Inspection",
        "Purpose": "Session data (inspection only)",
        "Update Method": "Django app",
        "Used By": "Database inspection scripts"
    }
]

df_tables = pd.DataFrame(db_tables)
st.dataframe(df_tables, use_container_width=True, hide_index=True)

st.markdown("---")

# Data Loading Functions
st.header("📥 Data Loading Functions by Source")

tab1, tab2, tab3 = st.tabs(["📊 Database", "🌐 API", "📁 CSV/Excel"])

with tab1:
    st.subheader("Database Sources")
    db_sources = [
        {
            "Function": "load_session_data_from_db()",
            "Table": "teampact_sessions_complete",
            "Data Type": "Session data",
            "Update Method": "Nightly cron job"
        },
        {
            "Function": "load_endline_from_db() [nmb_assessments]",
            "Table": "teampact_assessment_endline_2025",
            "Data Type": "Endline assessments",
            "Update Method": "Django management"
        },
        {
            "Function": "load_endline_from_db() [cohort_analysis]",
            "Table": "teampact_assessment_endline_2025",
            "Data Type": "Endline assessments",
            "Update Method": "Django management"
        },
        {
            "Function": "get_ta_sessions()",
            "Table": "api_tasession",
            "Data Type": "TA mentor visits",
            "Update Method": "Django app"
        },
        {
            "Function": "load_assessments_2026()",
            "Table": "assessments_2026",
            "Data Type": "2026 baseline/midline assessments",
            "Update Method": "Nightly via sync_assessments_2026"
        },
        {
            "Function": "load_sessions_2026()",
            "Table": "sessions_2026",
            "Data Type": "2026 session data",
            "Update Method": "Nightly via sync_teampact_sessions_2026"
        },
        {
            "Function": "load_mentor_visits_2026()",
            "Table": "mentor_visits_2026",
            "Data Type": "2026 mentor visits",
            "Update Method": "Nightly via sync_mentor_visits_2026"
        }
    ]
    st.dataframe(pd.DataFrame(db_sources), use_container_width=True, hide_index=True)
    
    st.info("💡 Database sources provide real-time data that auto-updates nightly. No manual refresh needed.")

with tab2:
    st.subheader("TeamPact API Sources")
    st.warning("⚠️ API functions are available but CSV/database sources are preferred for stability")
    
    api_sources = [
        {
            "Function": "load_zazi_izandi_2025_tp_api()",
            "Survey IDs": "575, 578, 576",
            "Languages": "Xhosa, English, Afrikaans",
            "Purpose": "NMB Baseline 2025",
            "Status": "Available but CSV preferred"
        },
        {
            "Function": "load_zazi_izandi_nmb_2025_endline_tp()",
            "Survey IDs": "725, 726, 727",
            "Languages": "Xhosa, English, Afrikaans",
            "Purpose": "NMB Endline 2025",
            "Status": "Available but database preferred"
        },
        {
            "Function": "load_zazi_izandi_east_london_2025_tp_api()",
            "Survey IDs": "644, 646, 647",
            "Languages": "Xhosa, English, Afrikaans",
            "Purpose": "BCM Baseline 2025",
            "Status": "Available but CSV preferred"
        }
    ]
    st.dataframe(pd.DataFrame(api_sources), use_container_width=True, hide_index=True)

with tab3:
    st.subheader("CSV/Excel File Sources")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**TeamPact CSV Exports**")
        tp_csv = [
            {"Function": "load_zazi_izandi_2025_tp()", "Files": "3 CSV (surveys 575/578/576)", "Purpose": "NMB Baseline 2025"},
            {"Function": "load_zazi_izandi_nmb_2025_endline_tp_csv()", "Files": "3 CSV (surveys 725/726/727)", "Purpose": "NMB Endline 2025"},
            {"Function": "load_zazi_izandi_east_london_2025_tp()", "Files": "3 CSV (surveys 644/646/647)", "Purpose": "BCM Baseline 2025"},
            {"Function": "load_zazi_izandi_ecd_endline()", "Files": "1 CSV (survey 723)", "Purpose": "ECD Endline 2025"},
            {"Function": "load_mentor_visits_2025_tp()", "Files": "1 CSV (survey 612)", "Purpose": "Mentor Visits"},
        ]
        st.dataframe(pd.DataFrame(tp_csv), use_container_width=True, hide_index=True)
        
        st.markdown("**SurveyCTO CSV Exports**")
        sct_csv = [
            {"Function": "load_zazi_izandi_2025()", "Files": "2 CSV files", "Purpose": "2025 Midline/Baseline (Cohort 1)"},
        ]
        st.dataframe(pd.DataFrame(sct_csv), use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("**Excel Files**")
        excel = [
            {"Function": "load_zazi_izandi_new_schools_2024()", "Files": "1 Excel", "Purpose": "2024 New Schools"},
            {"Function": "load_zazi_izandi_2024()", "Files": "6 Excel/Parquet", "Purpose": "2024 All assessments"},
            {"Function": "load_zazi_izandi_2023()", "Files": "2 Excel/Parquet", "Purpose": "2023 All assessments"},
        ]
        st.dataframe(pd.DataFrame(excel), use_container_width=True, hide_index=True)
        
        st.success("✅ 2024 and 2023 data prefer Parquet files (10-50x faster) with automatic Excel fallback")

st.markdown("---")

# Page-by-Page Data Sources
st.header("📄 Page-by-Page Data Sources")

page_tabs = st.tabs(["2023", "2024", "2025 Public", "2025 Internal", "2026", "Research", "Project Mgmt"])

with page_tabs[0]:  # 2023
    st.subheader("2023 Results Pages")
    pages_2023 = [
        {"Page": "2023 Results", "Data Source": "2023 assessments & sessions", "Function": "load_zazi_izandi_2023()", "Type": "📁 Parquet/Excel"}
    ]
    st.dataframe(pd.DataFrame(pages_2023), use_container_width=True, hide_index=True)

with page_tabs[1]:  # 2024
    st.subheader("2024 Results Pages")
    pages_2024 = [
        {"Page": "2024 Letter Knowledge", "Data Source": "2024 assessments", "Function": "load_zazi_izandi_2024()", "Type": "📁 Parquet/Excel"},
        {"Page": "2024 Word Reading", "Data Source": "2024 assessments", "Function": "load_zazi_izandi_2024()", "Type": "📁 Parquet/Excel"},
        {"Page": "2024 New Schools", "Data Source": "New schools endline", "Function": "load_zazi_izandi_new_schools_2024()", "Type": "📁 Excel"},
        {"Page": "2024 Session Analysis", "Data Source": "2024 sessions", "Function": "load_zazi_izandi_2024()", "Type": "📁 Parquet/Excel"}
    ]
    st.dataframe(pd.DataFrame(pages_2024), use_container_width=True, hide_index=True)

with page_tabs[2]:  # 2025 Public
    st.subheader("2025 Results Pages (Public Access)")
    pages_2025_pub = [
        {"Page": "2025 Baseline NMB (Cohort 1)", "Data Source": "SurveyCTO exports", "Function": "load_zazi_izandi_2025()", "Type": "📁 CSV", "Notes": "Jan-Jun cohort"},
        {"Page": "2025 Midline NMB (Cohort 1)", "Data Source": "SurveyCTO exports", "Function": "load_zazi_izandi_2025()", "Type": "📁 CSV", "Notes": "Jan-Jun cohort"},
        {"Page": "2025 ECD NMB Results", "Data Source": "ECD-specific + midline", "Function": "load_zazi_izandi_ecd_endline()", "Type": "📁 CSV", "Notes": "Combined ECD"}
    ]
    st.dataframe(pd.DataFrame(pages_2025_pub), use_container_width=True, hide_index=True)

with page_tabs[3]:  # 2025 Internal
    st.subheader("2025 Results Pages (Internal Access)")
    pages_2025_int = [
        {"Page": "2025 Baseline NMB (Cohort 2)", "Data Source": "teampact_assessment_endline_2025", "Function": "load_endline_from_db()", "Type": "📊 Database"},
        {"Page": "2025 Endline NMB (Cohort 2)", "Data Source": "teampact_assessment_endline_2025", "Function": "load_endline_from_db()", "Type": "📊 Database"},
        {"Page": "2025 Baseline BCM (Cohort 2)", "Data Source": "TeamPact CSV exports", "Function": "load_zazi_izandi_east_london_2025_tp()", "Type": "📁 CSV"},
        {"Page": "2025 Sessions NMB (Cohort 2)", "Data Source": "teampact_sessions_complete", "Function": "load_session_data_from_db()", "Type": "📊 Database"},
        {"Page": "2025 Sessions BCM (Cohort 2)", "Data Source": "teampact_sessions_complete", "Function": "load_session_data_from_db()", "Type": "📊 Database"},
        {"Page": "2025 Mentor Visits (Cohort 2)", "Data Source": "Merged CSV", "Function": "load_mentor_visits_2025_tp()", "Type": "📁 CSV"}
    ]
    st.dataframe(pd.DataFrame(pages_2025_int), use_container_width=True, hide_index=True)
    st.info("💡 Most 2025 Cohort 2 pages use the database with nightly auto-updates")

with page_tabs[4]:  # 2026
    st.subheader("2026 Results Pages")
    pages_2026 = [
        {"Page": "2026 Baseline Primary Schools", "Data Source": "assessments_2026", "Function": "Direct SQL / load_assessments_2026()", "Type": "📊 Database", "Notes": "Surveys 815/816/817; baseline only"},
        {"Page": "2026 Midline Primary School", "Data Source": "assessments_2026", "Function": "Direct SQL + midline_primary_helpers_2026.py", "Type": "📊 Database", "Notes": "Compares baseline 815/816/817 with midline 880/881/882"},
        {"Page": "2026 ECD Baseline", "Data Source": "assessments_2026", "Function": "Direct SQL", "Type": "📊 Database", "Notes": "Survey 805; ECD midline not included yet"},
        {"Page": "2026 Sessions", "Data Source": "sessions_2026", "Function": "load_sessions_2026()", "Type": "📊 Database", "Notes": "Auto-updated nightly"},
        {"Page": "2026 Mentor Visits", "Data Source": "mentor_visits_2026", "Function": "load_mentor_visits_2026()", "Type": "📊 Database", "Notes": "Survey 824"}
    ]
    st.dataframe(pd.DataFrame(pages_2026), use_container_width=True, hide_index=True)

with page_tabs[5]:  # Research
    st.subheader("Research & Benchmarks Pages")
    pages_research = [
        {"Page": "Research & Benchmarks", "Data Source": "2024 assessments", "Function": "load_zazi_izandi_2024()", "Type": "📁 Parquet/Excel"},
        {"Page": "Zazi Bot (AI Assistant)", "Data Source": "Context-based", "Function": "Various", "Type": "🤖 Multiple"},
        {"Page": "Year Comparisons", "Data Source": "2023, 2024, 2025 data", "Function": "Multiple loaders", "Type": "📁 Multiple"}
    ]
    st.dataframe(pd.DataFrame(pages_research), use_container_width=True, hide_index=True)

with page_tabs[6]:  # Project Management
    st.subheader("Project Management Pages (Internal Only)")
    pages_pm = [
        {"Page": "Letter Progress (Cohort 2)", "Data Source": "teampact_sessions_complete", "Function": "Direct SQL query", "Type": "📊 Database"},
        {"Page": "Letter Progress Detailed (Cohort 2)", "Data Source": "teampact_sessions_complete", "Function": "Direct SQL query", "Type": "📊 Database"},
        {"Page": "Check: Same Letter Groups", "Data Source": "teampact_sessions_complete", "Function": "Direct SQL query", "Type": "📊 Database"},
        {"Page": "Check: Moving Too Fast", "Data Source": "teampact_sessions_complete", "Function": "Direct SQL query", "Type": "📊 Database"},
        {"Page": "2025 Mentor Visits", "Data Source": "Mentor visit CSV", "Function": "load_mentor_visits_2025_tp()", "Type": "📁 CSV"}
    ]
    st.dataframe(pd.DataFrame(pages_pm), use_container_width=True, hide_index=True)
    st.success("✅ All session-based project management tools use the database for real-time data")

st.markdown("---")

# Architecture Evolution
st.header("🏗️ Architecture Evolution")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### Phase 1")
    st.markdown("**Manual CSV/Excel**")
    st.caption("2023-2024")
    st.markdown("""
    - Local CSV/Excel files
    - Manual exports
    - Files in repository
    """)

with col2:
    st.markdown("### Phase 2")
    st.markdown("**API Integration**")
    st.caption("Mid-2025")
    st.markdown("""
    - TeamPact API functions
    - Optional API toggle
    - CSV still default
    """)

with col3:
    st.markdown("### Phase 3")
    st.markdown("**Database**")
    st.caption("Oct 2025")
    st.markdown("""
    - Nightly auto-updates
    - PostgreSQL storage
    - No manual refresh
    """)

with col4:
    st.markdown("### Phase 4")
    st.markdown("**Optimization**")
    st.caption("Nov 2024")
    st.markdown("""
    - Parquet conversion
    - 10-50x faster loads
    - Smart caching
    """)

st.markdown("---")

# Current Best Practices
st.header("✅ Current Best Practices")

practice_col1, practice_col2 = st.columns(2)

with practice_col1:
    st.success("**✅ DO USE**")
    st.markdown("""
    - **Sessions Data (2025 Cohort 2)**: Database (`teampact_sessions_complete`)
    - **Endline Data (2025 Cohort 2)**: Database (`teampact_assessment_endline_2025`)
    - **2026 Baseline/Midline Assessments**: Database (`assessments_2026`, `assessment_cells_2026`)
    - **2026 Sessions and Mentor Visits**: Database (`sessions_2026`, `mentor_visits_2026`)
    - **Historical Data (2023-2024)**: Parquet files with Excel fallback
    - **Assessment Data (Cohort 1 & 2 Baseline)**: CSV exports
    """)

with practice_col2:
    st.error("**❌ DON'T USE**")
    st.markdown("""
    - Manual API calls for sessions (use database)
    - CSV exports for Cohort 2 sessions (use database)
    - Legacy table `teampact_nmb_sessions`
    - Direct Excel files when Parquet available
    """)

st.markdown("---")

# Database Architecture Diagram
st.header("🔄 Database Table Relationships")

st.code("""
teampact_sessions_complete (Session Data)
├── Used by: Session analysis pages
├── Used by: Letter progress tracking
├── Used by: Quality check tools
└── Updated: Nightly via cron job

teampact_assessment_endline_2025 (Assessment Data)
├── Used by: Endline analysis pages
├── Used by: Cohort analysis pages
└── Updated: Via Django management command

assessments_2026 + assessment_cells_2026 (Assessment Data)
├── Used by: 2026 baseline primary page
├── Used by: 2026 midline primary page
├── Used by: 2026 ECD baseline page
└── Updated: Nightly via sync_assessments_2026 + sync_assessment_cells_2026

sessions_2026 + mentor_visits_2026 (Operations Data)
├── Used by: 2026 sessions and project management pages
└── Updated: Nightly via Django management commands

api_tasession (TA Visits - Separate System)
├── Used by: Early implementation tracking
└── Updated: Via Django app directly
""", language="")

st.markdown("---")

# Summary Statistics
st.header("📈 Summary Statistics")

stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

with stat_col1:
    st.metric("Database Tables", "7", help="Active production database tables")

with stat_col2:
    st.metric("Data Loading Functions", "15", help="Total unique data loading functions")

with stat_col3:
    st.metric("Pages Using Database", "13", help="2025 Cohort 2, 2026, and project management pages")

with stat_col4:
    st.metric("Pages Using CSV/Excel", "11", help="2023, 2024, and 2025 Cohort 1 pages")

st.markdown("---")

# Migration Status
st.header("🔄 Migration Status")

migration_col1, migration_col2, migration_col3 = st.columns(3)

with migration_col1:
    st.success("**✅ Completed**")
    st.markdown("""
    - Sessions → Database
    - Nightly auto-updates
    - Endline → Database
    - 2026 baseline/midline → Database
    - Parquet optimization
    """)

with migration_col2:
    st.warning("**⚠️ Pending**")
    st.markdown("""
    - Remove legacy table refs
    - Update test files
    - Consolidate API functions
    - Archive old CSVs
    """)

with migration_col3:
    st.info("**📋 Future**")
    st.markdown("""
    - Mentor visits → Database?
    - Full API retirement?
    - Automated backups
    """)

st.markdown("---")

# Environment Variables
st.header("🔐 Environment Variables Required")

env_vars = [
    {"Variable": "TEAMPACT_API_TOKEN", "Purpose": "TeamPact API access", "Required For": "API functions (optional use)"},
    {"Variable": "RENDER_DATABASE_URL", "Purpose": "PostgreSQL connection", "Required For": "All database access"},
    {"Variable": "DATABASE_URL", "Purpose": "Django database", "Required For": "TA session tracking"}
]

st.dataframe(pd.DataFrame(env_vars), use_container_width=True, hide_index=True)

st.markdown("---")

# File Locations
with st.expander("📁 File Locations Reference"):
    st.markdown("""
    #### CSV Files
    - `data/` - SurveyCTO exports
    - `data/Teampact/` - TeamPact survey exports
    - `data/mentor_visit_tracker/` - Mentor observation data
    
    #### Excel Files
    - `data/*.xlsx` - Assessment databases (2023-2024)
    
    #### Parquet Files (Optimized)
    - `data/parquet/raw/` - Optimized versions of Excel data
    """)

# Footer
st.markdown("---")
st.caption("**Document Maintained By:** Data Team | **Review Frequency:** Quarterly or when major changes occur")
