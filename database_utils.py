"""
Database utilities for TeamPact Sessions
Provides connection management and common database operations.
"""

import os
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
from dotenv import load_dotenv
import streamlit as st
from datetime import datetime

# Load environment variables
load_dotenv()

# ECD Classification
ecd_list = [
    "Bavumeleni ECD",
    "Emmanuel Day Care",
    "Green Apple ECD",
    "Ilitha Lethu Day Care",
    "Kids College ECD",
    "Libhongolwethu ECD",
    "Livuse ECD",
    "Lukhanyo ECD",
    "Njongozabantu Day Care",
    "Sakha Bantwana ECD",
    "Siyabulela Pre-School",
    "St Mary Magdelene ECD",
    "Thembalethu Day Care",
    "Msobomvu ECD",
    "Mzamomhle Edu-care",
    "Nceduluntu Edu-care",
    "Ekhaya Pre-School",
    "Future Angels ECD",
    "Koester Day Care",
    "Khusta ECD",
    "Rise and Shine ECD",
    "Arise and Shine ECD"
]

def get_school_type(program_name):
    """Classify programs as ECD or Primary School"""
    if program_name in ecd_list:
        return 'ECD'
    else:
        return 'Primary School'

def get_mentor(program_name):
    """Assign mentor based on school name"""
    try:
        # Import here to avoid circular imports
        from data.mentor_schools import mentors_to_schools
        for mentor, schools in mentors_to_schools.items():
            if program_name in schools:
                return mentor
        return 'Unknown'
    except ImportError:
        # Fallback if mentor_schools module is not available
        return 'Unknown'

@st.cache_resource
def get_database_engine():
    """Get SQLAlchemy database engine with connection pooling"""
    database_url = os.getenv('RENDER_DATABASE_URL')
    if not database_url:
        raise ValueError("RENDER_DATABASE_URL environment variable not found")
    
    # Create engine with connection pooling and retry logic
    engine = create_engine(
        database_url,
        pool_pre_ping=True,      # Verify connections before use
        pool_recycle=3600,       # Recycle connections after 1 hour
        connect_args={
            "connect_timeout": 10,  # 10 second connection timeout
            "options": "-c statement_timeout=30000"  # 30 second query timeout
        },
        echo=False               # Set to True for SQL debugging
    )
    return engine

def get_database_connection():
    """Get raw psycopg2 database connection"""
    database_url = os.getenv('RENDER_DATABASE_URL')
    if not database_url:
        raise ValueError("RENDER_DATABASE_URL environment variable not found")
    
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        st.error(f"Database connection failed: {e}")
        raise

def check_table_exists(table_name="teampact_sessions_complete"):
    """Check if the teampact_sessions_complete table exists"""
    try:
        conn = get_database_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = %s
                );
            """, (table_name,))
            exists = cursor.fetchone()[0]
        conn.close()
        return exists
    except Exception as e:
        st.error(f"Error checking table existence: {e}")
        return False

def get_last_refresh_timestamp():
    """Get the timestamp of the last data refresh"""
    try:
        if not check_table_exists():
            return None
            
        engine = get_database_engine()
        query = """
            SELECT MAX(data_refresh_timestamp) as last_refresh
            FROM teampact_sessions_complete
        """
        
        df = pd.read_sql(query, engine)
        if not df.empty and df['last_refresh'].iloc[0] is not None:
            return pd.to_datetime(df['last_refresh'].iloc[0])
        return None
        
    except Exception as e:
        st.error(f"Error getting last refresh timestamp: {e}")
        return None

def get_data_summary():
    """Get summary statistics about the data in the database"""
    try:
        if not check_table_exists():
            return None
            
        engine = get_database_engine()
        query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT session_id) as unique_sessions,
                COUNT(DISTINCT user_name) as unique_users,
                COUNT(DISTINCT program_name) as unique_programs,
                MIN(session_started_at) as earliest_session,
                MAX(session_started_at) as latest_session,
                MAX(data_refresh_timestamp) as last_refresh
            FROM teampact_sessions_complete
        """
        
        df = pd.read_sql(query, engine)
        return df.iloc[0].to_dict()
        
    except Exception as e:
        st.error(f"Error getting data summary: {e}")
        return None

@st.cache_data
def load_session_data_from_db():
    """
    Load session data from database with intelligent caching
    Cache automatically resets once per day (at midnight) using date-based cache key
    
    Returns:
        pandas.DataFrame: Session data with school_type and mentor columns added
    """
    try:
        if not check_table_exists():
            st.error("Database table 'teampact_sessions_complete' does not exist. Please run the migration first.")
            return pd.DataFrame()
            
        engine = get_database_engine()
        
        # First get the latest refresh timestamp to use as cache key
        refresh_timestamp = get_last_refresh_timestamp()
        if refresh_timestamp is None:
            st.warning("No data found in database. Please refresh data from API.")
            return pd.DataFrame()
        
        # Use both the current date AND refresh timestamp as cache key
        # This ensures cache resets daily at midnight regardless of database updates
        current_date = datetime.now().date().isoformat()
        cache_key = f"{current_date}_{refresh_timestamp}"
        
        # Use the combined cache key by calling the cached internal function
        return _load_session_data_internal(cache_key)
        
    except Exception as e:
        st.error(f"Error loading data from database: {e}")
        return pd.DataFrame()

@st.cache_data
def _load_session_data_internal(_cache_key):
    """
    Internal function to load data with caching based on date + refresh timestamp
    
    Args:
        _cache_key: Combined cache key (date + refresh timestamp) that ensures daily cache reset
    
    Returns:
        pandas.DataFrame: Raw session data with derived columns
    """
    try:
        engine = get_database_engine()
        
        # Load all data from the table
        query = "SELECT * FROM teampact_sessions_complete ORDER BY session_started_at DESC"
        df = pd.read_sql(query, engine)
        
        if df.empty:
            return df
        
        # Add the derived columns that the app expects
        df['school_type'] = df['program_name'].apply(get_school_type)
        df['mentor'] = df['program_name'].apply(get_mentor)
        
        return df
        
    except Exception as e:
        st.error(f"Error loading session data: {e}")
        return pd.DataFrame()

def test_database_connection():
    """Test database connection and return status"""
    try:
        conn = get_database_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        conn.close()
        return True, "Database connection successful"
    except Exception as e:
        return False, f"Database connection failed: {e}"

if __name__ == "__main__":
    # Test the database connection
    success, message = test_database_connection()
    print(f"Connection test: {message}")
    
    if success:
        # Test table existence
        exists = check_table_exists()
        print(f"Table exists: {exists}")
        
        if exists:
            # Get data summary
            summary = get_data_summary()
            if summary:
                print("Data summary:")
                for key, value in summary.items():
                    print(f"  {key}: {value}")
