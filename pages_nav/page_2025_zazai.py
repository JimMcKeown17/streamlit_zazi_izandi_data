import streamlit as st
import pandas as pd
import os
from datetime import datetime as dt
from dotenv import load_dotenv
from process_survey_cto_updated import process_egra_data

load_dotenv()


def show():
    # Ensure user is set in session state for consistency with other pages
    if 'user' not in st.session_state:
        st.session_state.user = None

    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    @st.cache_data
    def load_egra_data(children_filename: str, ta_filename: str):
        """Load and cache EGRA data files."""
        children_path = os.path.join(ROOT_DIR, "data", children_filename)
        ta_path = os.path.join(ROOT_DIR, "data", ta_filename)
        df, _ = process_egra_data(children_file=children_path, ta_file=ta_path)
        return df

    st.title("🤖 ZazAI – 2025 Midline Data Analyst")

    try:
        # Load and prepare midline dataset (same cut-off as original Midline page)
        df_full = load_egra_data(
            children_filename="EGRA form [Eastern Cape]-assessment_repeat - June 4.csv",
            ta_filename="EGRA form [Eastern Cape] - June 4.csv"
        )
        df_full['submission_date'] = pd.to_datetime(df_full['date'])
        midline_df = df_full[df_full['submission_date'] >= pd.Timestamp('2025-04-15')]

        # ---------------------- AI Analysis Section ----------------------
        st.divider()
        with st.container():
            st.header("ZazAI Data Analysis")
            st.write("Get insights from our super AI analyst, ZazAI.")

            # Model selection
            model_choice = st.selectbox(
                "Select AI Model:",
                ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
                help="gpt-4o-mini is faster and cheaper, gpt-4o is more capable"
            )

            # Capabilities description & question input
            st.info("""
            **ZazAI Analysis Capabilities:**
            - 🎯 Dynamic data exploration and drill-downs
            - 📊 Benchmark analysis with midline context
            - 🔍 Top/underperformer identification
            - 📈 Variance analysis across schools/TAs/classes
            - 🚨 At-risk student identification
            - 🔄 Interactive Q&A with follow-up questions
            """)
            
            custom_questions_input = st.text_area(
                "Ask Specific Questions (optional):",
                placeholder="e.g., 'Which schools need the most support?' or 'How do our top TAs compare?'",
                help="The AI can answer specific questions using dynamic data analysis tools"
            )

            # Parse custom questions
            custom_questions = None
            if custom_questions_input.strip():
                custom_questions = [q.strip() for q in custom_questions_input.split('\n') if q.strip()]

            # Generate analysis
            if st.button("🚀 Generate AI Analysis", type="primary"):
                if not os.getenv('OPENAI_API_KEY'):
                    st.error("⚠️ OPENAI_API_KEY not found in environment variables. Please add it to your .env file.")
                else:
                    with st.spinner("🤔 ZazAI is analyzing your data..."):
                        try:
                            import sys
                            sys.path.append('..')
                            from AI_Tools.openai_tools_analysis import analyze_with_tools

                            if custom_questions:
                                analysis = analyze_with_tools(
                                    midline_df,
                                    analysis_type="question",
                                    question="\n".join(custom_questions),
                                    model=model_choice
                                )
                            else:
                                analysis = analyze_with_tools(
                                    midline_df,
                                    analysis_type="initial",
                                    model=model_choice
                                )

                            if analysis:
                                st.success("✅ Analysis Complete!")
                                with st.expander("📋 AI Analysis Results", expanded=True):
                                    st.markdown(analysis)

                                st.download_button(
                                    label="📥 Download Analysis",
                                    data=analysis,
                                    file_name=f"ai_analysis_tools_{dt.today().strftime('%Y-%m-%d')}.txt",
                                    mime="text/plain"
                                )
                            else:
                                st.error("❌ Failed to generate analysis. Please check your API key and try again.")
                                
                        except Exception as e:
                            st.error(f"❌ Error during analysis: {str(e)}")
                            st.info("💡 Try asking more specific questions or check the debug section below for troubleshooting.")

            # Debug & Diagnostics
            with st.expander("🔧 Debug & Diagnostics", expanded=False):
                st.markdown("### 🔍 Debug Information")
                st.write("Use this section to troubleshoot AI analysis issues:")

                debug_col1, debug_col2 = st.columns([1, 3])
                with debug_col1:
                    if st.button("🔧 Run System Diagnostics", type="secondary", key="debug_btn"):
                        st.session_state.run_diagnostics = True

                if st.session_state.get('run_diagnostics', False):
                    with debug_col2:
                        try:
                            import sys
                            sys.path.append('..')
                            from AI_Tools import debug_ai_analysis
                            import json
                            debug_results = debug_ai_analysis.run_comprehensive_diagnostics(midline_df)
                            if debug_results:
                                report_json = json.dumps(debug_results, indent=2)
                                st.download_button(
                                    label="📥 Download Diagnostics Report",
                                    data=report_json,
                                    file_name=f"ai_analysis_diagnostics_{dt.now().strftime('%Y%m%d_%H%M%S')}.json",
                                    mime="application/json",
                                    key="download_debug"
                                )
                        except Exception as e:
                            st.error(f"❌ Debug system failed: {str(e)}")
                            st.code(f"Error details: {str(e)}")
                    st.session_state.run_diagnostics = False

                st.divider()
                st.markdown("### 📊 Data Quick Info")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("DataFrame Shape", f"{midline_df.shape[0]} rows × {midline_df.shape[1]} cols")
                with col2:
                    st.metric("Available Columns", len(midline_df.columns))
                with col3:
                    api_key_status = "✅ Set" if os.getenv('OPENAI_API_KEY') else "❌ Missing"
                    st.metric("API Key Status", api_key_status)

                if st.checkbox("Show column names", key="show_cols"):
                    st.write("**DataFrame Columns:**")
                    st.write(list(midline_df.columns))
        # ----------------------------------------------------------------

    except Exception as e:
        st.error(f"Error loading data: {e}") 