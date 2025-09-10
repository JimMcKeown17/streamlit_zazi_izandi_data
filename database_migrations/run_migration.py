#!/usr/bin/env python3
"""
Database Migration Script for TeamPact NMB Sessions Table
Creates the teampact_nmb_sessions table with all necessary columns and indexes.
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_database_connection():
    """Get database connection using RENDER_DATABASE_URL"""
    database_url = os.getenv('RENDER_DATABASE_URL')
    if not database_url:
        raise ValueError("RENDER_DATABASE_URL environment variable not found")
    
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        print(f"Error connecting to database: {e}")
        raise

def read_migration_file():
    """Read the SQL migration file"""
    migration_file = os.path.join(os.path.dirname(__file__), 'create_teampact_sessions_table.sql')
    
    if not os.path.exists(migration_file):
        raise FileNotFoundError(f"Migration file not found: {migration_file}")
    
    with open(migration_file, 'r') as f:
        return f.read()

def run_migration():
    """Run the database migration"""
    print("Starting TeamPact NMB sessions table migration...")
    
    try:
        # Get database connection
        print("Connecting to database...")
        conn = get_database_connection()
        
        # Read migration SQL
        print("Reading migration file...")
        migration_sql = read_migration_file()
        
        # Execute migration
        print("Executing migration...")
        with conn.cursor() as cursor:
            cursor.execute(migration_sql)
            conn.commit()
        
        print("✅ Migration completed successfully!")
        
        # Verify table was created
        print("\nVerifying table creation...")
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Check if table exists
            cursor.execute("""
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'teampact_nmb_sessions' 
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            
            if columns:
                print(f"✅ Table 'teampact_nmb_sessions' created with {len(columns)} columns (showing first 10):")
                for col in columns[:10]:
                    print(f"  - {col['column_name']}: {col['data_type']}")
                if len(columns) > 10:
                    print(f"  ... and {len(columns) - 10} more columns")
            else:
                print("❌ Table not found after migration")
            
            # Check indexes
            cursor.execute("""
                SELECT indexname, indexdef 
                FROM pg_indexes 
                WHERE tablename = 'teampact_nmb_sessions'
            """)
            indexes = cursor.fetchall()
            
            if indexes:
                print(f"\n✅ Created {len(indexes)} indexes:")
                for idx in indexes:
                    print(f"  - {idx['indexname']}")
            else:
                print("\n❌ No indexes found")
        
        conn.close()
        print("\n🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)

def test_connection():
    """Test database connection without running migration"""
    print("Testing database connection...")
    
    try:
        conn = get_database_connection()
        
        with conn.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            print(f"✅ Connected successfully!")
            print(f"Database version: {version}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Test connection only
        test_connection()
    else:
        # Run full migration
        run_migration()
