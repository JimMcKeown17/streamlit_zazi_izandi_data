import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

# Add the project root to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def main():
    st.title("🧪 EA Sessions Test Page")

    st.write("Testing if the issue is with the project_management folder...")

    try:
        # Import database utilities
        from database_utils import get_database_engine, check_table_exists

        st.write("✅ Imports successful")

        # Check if table exists
        if not check_table_exists('teampact_nmb_sessions'):
            st.error("TeamPact sessions table not found.")
            return

        st.write("✅ Table exists")

        # Get database engine
        engine = get_database_engine()

        # Simple query
        query = """
        SELECT
            user_name as ea_name,
            program_name as school_name,
            letters_taught,
            session_started_at
        FROM teampact_nmb_sessions
        WHERE letters_taught IS NOT NULL
        AND letters_taught <> ''
        ORDER BY session_started_at DESC
        LIMIT 10
        """

        df = pd.read_sql(query, engine)

        st.write(f"✅ Query successful: {len(df)} sessions found")

        if not df.empty:
            st.write("**Recent EA Sessions:**")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.warning("No data found")

        st.success("🎉 Test page working correctly!")

    except Exception as e:
        st.error(f"Error: {e}")
        import traceback
        st.code(traceback.format_exc())

main()