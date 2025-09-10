import requests
import json
import pandas as pd
from datetime import datetime
import os
import sys

# Add the project root to the path so we can import database utilities
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from database_utils import get_database_engine, check_table_exists
import psycopg2
from sqlalchemy import text

def fetch_and_save_data():
    """Fetch data from API and save to file with comprehensive data extraction"""
    try:
        # API configuration
        api_url = os.getenv('API_URL', 'https://teampact.co/api/analytics/v1/sessions/attendance')
        api_token = os.getenv('TEAMPACT_API_TOKEN', '')
        
        headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
        
        # Fetch all pages of data
        all_data = []
        page = 1
        per_page = 100  # Use maximum allowed per page for efficiency
        total_records = 0
        
        print(f"Starting data fetch with pagination...")
        
        while True:
            # Add pagination parameters
            params = {
                'page': page,
                'per_page': per_page
            }
            
            print(f"Fetching page {page}...")
            
            # Add retry logic for network issues
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = requests.get(api_url, headers=headers, params=params, timeout=30)
                    response.raise_for_status()
                    break  # Success, exit retry loop
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * 5  # 5, 10, 15 seconds
                        print(f"Network error on attempt {attempt + 1}, retrying in {wait_time}s: {e}")
                        import time
                        time.sleep(wait_time)
                    else:
                        print(f"Failed after {max_retries} attempts: {e}")
                        raise
            
            data = response.json()
            page_records = data.get('data', [])
            all_data.extend(page_records)
            
            # Get pagination metadata
            meta = data.get('meta', {})
            current_page = meta.get('current_page', page)
            last_page = meta.get('last_page', 1)
            total = meta.get('total', 0)
            
            print(f"Page {current_page}/{last_page} - {len(page_records)} records (Total so far: {len(all_data)}/{total})")
            
            # Check if we've reached the last page
            if current_page >= last_page:
                break
                
            page += 1
        
        print(f"Completed pagination - fetched {len(all_data)} total records")
        
        # Create complete data structure for saving
        complete_data = {
            'data': all_data,
            'meta': {
                'total_records': len(all_data),
                'total_pages_fetched': page,
                'fetched_at': datetime.now().isoformat()
            }
        }
        
        # Save raw JSON with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = f'data/ecd_data_{timestamp}.json'
        
        # Ensure data directory exists
        os.makedirs('data', exist_ok=True)
        
        with open(json_file, 'w') as f:
            json.dump(complete_data, f, indent=2)
        
        # Also save as latest.json for easy access
        with open('data/latest.json', 'w') as f:
            json.dump(complete_data, f, indent=2)
        
        # Convert to CSV for easy loading with comprehensive data extraction
        records = []
        skipped_records = 0
        
        for i, record in enumerate(all_data):
            try:
                # Extract main record data with null safety
                session_data = record.get('session') or {}
                participant_data = record.get('participant') or {}
                user_data = record.get('user') or {}
                class_data = record.get('class') or {}
                program_data = record.get('program') or {}
                org_data = record.get('organization') or {}
                
                # Handle session tags - extract all letter names and group IDs
                session_tags = session_data.get('session_tags', [])
                letters_taught = []
                tag_ids = []
                group_ids = []
                
                for tag in session_tags:
                    if tag.get('name'):
                        letters_taught.append(tag.get('name'))
                        tag_ids.append(str(tag.get('id', '')))
                        
                        # Extract group_id from pivot
                        pivot = tag.get('pivot', {})
                        if pivot.get('group_id'):
                            group_ids.append(str(pivot.get('group_id')))
                
                # Join as comma-separated strings
                letters_taught_str = ','.join(letters_taught) if letters_taught else ''
                tag_ids_str = ','.join(tag_ids) if tag_ids else ''
                group_ids_str = ','.join(set(group_ids)) if group_ids else ''  # Use set to avoid duplicates
                
                # Extract location data with null safety
                location = session_data.get('location') or {}
                latitude = location.get('lat') if location else session_data.get('latitude')
                longitude = location.get('lng') if location else session_data.get('longitude')
                
                # Handle roll call records with null safety
                roll_call = record.get('roll_call_records') or {}
                pre_status = (roll_call.get('pre') or {}).get('status', '') if roll_call else ''
                post_status = (roll_call.get('post') or {}).get('status', '') if roll_call else ''
                
                # Create comprehensive flat record
                flat_record = {
                    # Main identifiers
                    'attendance_id': record.get('id', ''),
                    'session_id': record.get('session_id', ''),
                    'participant_id': record.get('participant_id', ''),
                    'user_id': record.get('user_id', ''),
                    'class_id': record.get('class_id', ''),
                    'program_id': record.get('program_id', ''),
                    'org_id': record.get('org_id', ''),
                    
                    # Participant information
                    'participant_name': record.get('participant_name', ''),
                    'participant_firstname': participant_data.get('firstname', ''),
                    'participant_lastname': participant_data.get('lastname', ''),
                    'participant_gender': participant_data.get('gender', ''),
                    
                    # Attendance information
                    'attendance_status': record.get('attendance_status', ''),
                    'roll_call_pre_status': pre_status,
                    'roll_call_post_status': post_status,
                    'is_flagged': record.get('is_flagged', False),
                    'flag_reason': record.get('flag_reason', ''),
                    
                    # Session timing
                    'session_started_at': record.get('session_started_at', ''),
                    'session_ended_at': record.get('session_ended_at', ''),
                    'check_in_time': record.get('check_in_time', ''),
                    'total_duration_minutes': record.get('total_duration_minutes', 0),
                    'session_duration_seconds': session_data.get('session_duration', 0),
                    
                    # Class/Program information
                    'class_name': record.get('class_name', ''),
                    'program_name': record.get('program_name', ''),
                    'organisation_name': record.get('organisation_name', ''),
                    
                    # User/Teacher information
                    'user_name': record.get('user_name', ''),
                    'user_email': user_data.get('email', ''),
                    'user_gender': user_data.get('gender', ''),
                    
                    # Session content and attendance metrics
                    'session_text': session_data.get('text', ''),
                    'attended_percentage': float(session_data.get('attended_percentage', 0)) if session_data.get('attended_percentage') else 0.0,
                    'participant_total': session_data.get('participant_total', 0),
                    'attended_total': session_data.get('attended_total', 0),
                    'attended_male_total': session_data.get('attended_male_total', 0),
                    'attended_female_total': session_data.get('attended_female_total', 0),
                    'attended_male_percentage': float(session_data.get('attended_male_percentage', 0)) if session_data.get('attended_male_percentage') else 0.0,
                    'attended_female_percentage': float(session_data.get('attended_female_percentage', 0)) if session_data.get('attended_female_percentage') else 0.0,
                    
                    # Location data
                    'latitude': latitude,
                    'longitude': longitude,
                    
                    # Curriculum/Letters data
                    'letters_taught': letters_taught_str,
                    'session_tag_ids': tag_ids_str,
                    'session_tag_group_ids': group_ids_str,
                    'num_letters_taught': len(letters_taught),
                    
                    # Additional session metadata
                    'mobile_app_id': session_data.get('mobile_app_id', ''),
                    'batch_id': session_data.get('batch_id', ''),
                    'rollcall_pre_present_count': session_data.get('rollcall_pre_present_count', 0),
                    'rollcall_post_present_count': session_data.get('rollcall_post_present_count', 0),
                    
                    # Class details
                    'class_description': class_data.get('description', ''),
                    'target_attended_percentage': class_data.get('target_attended_percentage', ''),
                    'target_attended_female_percentage': class_data.get('target_attended_female_percentage', ''),
                    
                    # Program details
                    'program_description': program_data.get('description', ''),
                    'program_is_archived': program_data.get('is_archived', False),
                    
                    # Timestamps
                    'record_created_at': record.get('created_at', ''),
                    'record_updated_at': record.get('updated_at', ''),
                    'last_activity_at': record.get('last_activity_at', ''),
                    'fetched_at': datetime.now().isoformat()
                }
                
                records.append(flat_record)
                
            except Exception as e:
                print(f"Skipping record {i+1} due to error: {e}")
                print(f"  Record keys: {list(record.keys()) if isinstance(record, dict) else 'Not a dict'}")
                if isinstance(record, dict):
                    # Check what's None vs what exists
                    session_val = record.get('session')
                    participant_val = record.get('participant')
                    user_val = record.get('user')
                    class_val = record.get('class')
                    program_val = record.get('program')
                    roll_call_val = record.get('roll_call_records')
                    
                    print(f"  Data availability:")
                    print(f"    session: {'None' if session_val is None else 'Present' if session_val else 'Empty dict'}")
                    print(f"    participant: {'None' if participant_val is None else 'Present' if participant_val else 'Empty dict'}")
                    print(f"    user: {'None' if user_val is None else 'Present' if user_val else 'Empty dict'}")
                    print(f"    class: {'None' if class_val is None else 'Present' if class_val else 'Empty dict'}")
                    print(f"    program: {'None' if program_val is None else 'Present' if program_val else 'Empty dict'}")
                    print(f"    roll_call_records: {'None' if roll_call_val is None else 'Present' if roll_call_val else 'Empty dict'}")
                    
                    # Show what basic fields are available
                    basic_fields = ['id', 'session_id', 'participant_id', 'user_id', 'attendance_status', 'participant_name']
                    available_basics = [f for f in basic_fields if record.get(f) is not None]
                    print(f"    Available basic fields: {available_basics}")
                    
                    # Show if any nested data exists
                    if session_val and isinstance(session_val, dict):
                        session_keys = list(session_val.keys())[:5]  # First 5 keys
                        print(f"    Session keys (first 5): {session_keys}")
                
                skipped_records += 1
                continue
        
        if skipped_records > 0:
            print(f"Skipped {skipped_records} problematic records out of {len(all_data)} total")
        
        # Create DataFrame
        df = pd.DataFrame(records)
        
        if df.empty:
            print("No valid records to save")
            return False
        
        print(f"Processed {len(records)} records with {len(df.columns)} columns")
        
        # Add data_refresh_timestamp to all records (ensure timezone-aware)
        refresh_timestamp = datetime.now()
        df['data_refresh_timestamp'] = pd.to_datetime(refresh_timestamp).tz_localize('UTC')
        
        # Clean up datetime columns to ensure proper format
        datetime_columns = [
            'session_started_at', 'session_ended_at', 'check_in_time', 
            'record_created_at', 'record_updated_at', 'last_activity_at', 'fetched_at'
        ]
        
        for col in datetime_columns:
            if col in df.columns:
                # Convert to datetime and handle timezone
                df[col] = pd.to_datetime(df[col], errors='coerce')
                # If the column has timezone-naive values, make them UTC
                if df[col].dt.tz is None:
                    try:
                        df[col] = df[col].dt.tz_localize('UTC')
                    except Exception as tz_error:
                        print(f"Warning: Could not localize timezone for {col}: {tz_error}")
                        # Keep as naive datetime if timezone localization fails
                        pass
        
        # Save to database
        success = save_to_database(df, refresh_timestamp)
        
        if success:
            # Also save as CSV backup (optional - can be removed later)
            try:
                df.to_csv('data/latest.csv', index=False)
                print("✅ Also saved CSV backup to data/latest.csv")
            except Exception as csv_error:
                print(f"⚠️ CSV backup failed (not critical): {csv_error}")
            
            # Create letters summary (optional)
            if 'letters_taught' in df.columns:
                try:
                    letters_summary = create_letters_summary(df)
                    letters_summary.to_csv('data/letters_summary.csv', index=False)
                    print(f"✅ Created letters summary with {len(letters_summary)} unique letter combinations")
                except Exception as summary_error:
                    print(f"⚠️ Letters summary failed (not critical): {summary_error}")
            
            print(f"🎉 Successfully saved {len(records)} records to database at {datetime.now()}")
            return True
        else:
            print("❌ Database save failed")
            return False
        
    except Exception as e:
        print(f"Sync failed: {e}")
        return False

def save_to_database(df, refresh_timestamp):
    """
    Save DataFrame to database using incremental updates (add new records only)
    
    Args:
        df: DataFrame with session data
        refresh_timestamp: Timestamp when this data was fetched
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"💾 Starting database save for {len(df)} records...")
        
        # Check if table exists
        if not check_table_exists():
            print("❌ Database table 'teampact_nmb_sessions' does not exist. Please run migration first.")
            return False
        
        # Get database engine
        engine = get_database_engine()
        
        # Check what attendance IDs we already have in the database
        print("🔍 Checking for existing records...")
        existing_ids = set()
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT DISTINCT attendance_id FROM teampact_nmb_sessions"))
                existing_ids = {row[0] for row in result.fetchall()}
            print(f"Found {len(existing_ids)} existing records in database")
        except Exception as e:
            print(f"Warning: Could not check existing records: {e}")
            print("Proceeding with full insert...")
        
        # Filter out records we already have
        if existing_ids:
            original_count = len(df)
            df = df[~df['attendance_id'].isin(existing_ids)]
            new_count = len(df)
            print(f"📊 Filtered: {original_count} total → {new_count} new records to insert")
            
            if new_count == 0:
                print("✅ No new records to insert - database is up to date!")
                return True
        
        print(f"📥 Inserting {len(df)} new records in manageable batches...")
        
        # Process in batches to avoid overwhelming the database
        batch_size = 200  # Process 200 records at a time
        total_batches = (len(df) - 1) // batch_size + 1
        successful_inserts = 0
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min((batch_num + 1) * batch_size, len(df))
            batch_df = df.iloc[start_idx:end_idx].copy()
            
            print(f"Processing batch {batch_num + 1}/{total_batches} ({len(batch_df)} records)...")
            
            try:
                batch_df.to_sql(
                    name='teampact_nmb_sessions',
                    con=engine,
                    if_exists='append',
                    index=False,
                    chunksize=50     # Small chunks within each batch
                )
                successful_inserts += len(batch_df)
                print(f"✅ Batch {batch_num + 1} completed ({successful_inserts}/{len(df)} total)")
                
            except Exception as batch_error:
                print(f"❌ Batch {batch_num + 1} failed: {batch_error}")
                
                # Try with smaller chunks for this batch
                try:
                    print(f"Retrying batch {batch_num + 1} with smaller chunks...")
                    batch_df.to_sql(
                        name='teampact_nmb_sessions',
                        con=engine,
                        if_exists='append',
                        index=False,
                        chunksize=10     # Very small chunks
                    )
                    successful_inserts += len(batch_df)
                    print(f"✅ Batch {batch_num + 1} completed on retry ({successful_inserts}/{len(df)} total)")
                    
                except Exception as retry_error:
                    print(f"❌ Batch {batch_num + 1} failed completely: {retry_error}")
                    print("Continuing with next batch...")
                    continue
        
        print(f"✅ Database insert completed - {successful_inserts}/{len(df)} records inserted")
        
        # Verify the insert by counting total records
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM teampact_nmb_sessions")).fetchone()
            total_records = result[0]
            
            # Get the latest refresh timestamp from database
            timestamp_result = conn.execute(text("SELECT MAX(data_refresh_timestamp) FROM teampact_nmb_sessions")).fetchone()
            latest_timestamp = timestamp_result[0] if timestamp_result else None
        
        if successful_inserts == len(df):
            print(f"✅ All {successful_inserts} new records inserted successfully!")
            print(f"✅ Total database records: {total_records}")
            if latest_timestamp:
                print(f"✅ Latest refresh timestamp: {latest_timestamp}")
            return True
        else:
            print(f"⚠️ Partial success: {successful_inserts}/{len(df)} records inserted")
            print(f"✅ Total database records: {total_records}")
            # Still return True if we got most of the data
            return successful_inserts > 0
            
    except Exception as e:
        print(f"❌ Database save failed: {e}")
        
        # Try to provide helpful error information
        if "does not exist" in str(e).lower():
            print("💡 Hint: Run the database migration script first")
        elif "connection" in str(e).lower():
            print("💡 Hint: Check your RENDER_DATABASE_URL environment variable")
        elif "column" in str(e).lower():
            print("💡 Hint: Database schema may be out of sync with CSV columns")
        
        return False

def create_letters_summary(df):
    """Create a summary of letters taught per session for quick curriculum analysis"""
    try:
        # Group by session to get unique sessions and their letter combinations
        session_summary = df.groupby('session_id').agg({
            'session_started_at': 'first',
            'user_name': 'first',
            'class_name': 'first',
            'program_name': 'first',
            'letters_taught': 'first',
            'num_letters_taught': 'first',
            'participant_total': 'first',
            'attended_total': 'first',
            'attended_percentage': 'first',
            'session_text': 'first'
        }).reset_index()
        
        # Add date column for easier analysis
        session_summary['session_date'] = pd.to_datetime(session_summary['session_started_at']).dt.date
        
        # Sort by date and time
        session_summary = session_summary.sort_values('session_started_at', ascending=False)
        
        return session_summary
        
    except Exception as e:
        print(f"Error creating letters summary: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    fetch_and_save_data()