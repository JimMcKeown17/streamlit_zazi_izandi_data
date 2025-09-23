import streamlit as st
import sys
import os

# Add the project root to the path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

def main():
    st.title("🧪 Letter Progress Test Page")

    st.write("Testing basic page functionality...")

    try:
        from database_utils import check_table_exists, get_database_engine
        st.write("✅ Database utils imported successfully")

        table_exists = check_table_exists()
        st.write(f"✅ Table exists check: {table_exists}")

        if table_exists:
            engine = get_database_engine()
            st.write("✅ Database engine obtained")

            import pandas as pd
            test_query = "SELECT COUNT(*) as total FROM teampact_nmb_sessions LIMIT 1"
            result = pd.read_sql(test_query, engine)
            st.write(f"✅ Basic query successful: {result['total'].iloc[0]} total records")

        st.success("All basic functionality tests passed!")

    except Exception as e:
        st.error(f"Error in basic tests: {e}")
        import traceback
        st.code(traceback.format_exc())

if __name__ == "__main__":
    main()