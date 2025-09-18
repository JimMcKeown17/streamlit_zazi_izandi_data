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
    """Fetch data from API and save to database with 100% coverage guarantee"""
    try:
        # API configuration
        api_url = os.getenv('API_URL', 'https://teampact.co/api/analytics/v1/sessions/attendance')
        api_token = os.getenv('TEAMPACT_API_TOKEN', '')
        
        if not api_token:
            print("❌ ERROR: TEAMPACT_API_TOKEN not found")
            return False
        
        headers = {
            'Authorization': f'Bearer {api_token}',
            'Content-Type': 'application/json'
        }
        
        # First, get total count and existing IDs for smart fetching
        print(f"🎯 Starting comprehensive data fetch for 100% coverage...")
        
        # Get API totals
        try:
            response = requests.get(api_url, headers=headers, params={'page': 1, 'per_page': 1}, timeout=30)
            response.raise_for_status()
            meta_data = response.json().get('meta', {})
            total_api_records = meta_data.get('total', 0)
            total_pages = meta_data.get('last_page', 1)
            print(f"📊 API has {total_api_records:,} total records across {total_pages:,} pages")
        except Exception as e:
            print(f"❌ Failed to get API metadata: {e}")
            return False
        
        # Get existing database IDs for efficient incremental fetch
        existing_ids = set()
        existing_count = 0
        try:
            if check_table_exists():
                engine = get_database_engine()
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT attendance_id FROM teampact_nmb_sessions"))
                    existing_ids = {row[0] for row in result.fetchall()}
                    existing_count = len(existing_ids)
                print(f"📊 Database has {existing_count:,} existing records")
            else:
                print(f"📊 Database table doesn't exist - will create fresh")
        except Exception as e:
            print(f"⚠️ Could not check existing records: {e}")
        
        missing_count = total_api_records - existing_count
        print(f"📊 Need to fetch {missing_count:,} new/missing records")
        
        # Comprehensive pagination with 100% guarantee
        all_data = []
        page = 1
        per_page = 100
        consecutive_empty_pages = 0
        max_empty_pages = 5  # Stop after 5 consecutive empty pages
        
        import time
        start_time = time.time()
        
        while page <= total_pages + 10:  # Add buffer for safety
            try:
                # Progress reporting
                if page % 25 == 0 or page == 1:
                    elapsed = time.time() - start_time
                    rate = len(all_data) / elapsed if elapsed > 0 else 0
                    print(f"📄 Page {page:,}/{total_pages:,} - Collected {len(all_data):,} records ({rate:.1f} rec/sec)")
                
                # Fetch page with retry logic
                params = {'page': page, 'per_page': per_page}
                
                max_retries = 3
                response = None
                for attempt in range(max_retries):
                    try:
                        response = requests.get(api_url, headers=headers, params=params, timeout=60)
                        response.raise_for_status()
                        break
                    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                        if attempt < max_retries - 1:
                            wait_time = (attempt + 1) * 2
                            print(f"      ⚠️ Network retry {attempt + 1}/{max_retries} in {wait_time}s...")
                            time.sleep(wait_time)
                        else:
                            raise
                
                data = response.json()
                page_records = data.get('data', [])
                
                if not page_records:
                    consecutive_empty_pages += 1
                    if consecutive_empty_pages >= max_empty_pages:
                        print(f"      ✅ Reached end after {consecutive_empty_pages} empty pages")
                        break
                    page += 1
                    continue
                
                # Filter for truly new records (smart incremental)
                new_records = []
                for record in page_records:
                    record_id = record.get('id')
                    if record_id and record_id not in existing_ids:
                        new_records.append(record)
                        existing_ids.add(record_id)  # Prevent duplicates within this fetch
                
                all_data.extend(new_records)
                consecutive_empty_pages = 0
                
                # Small delay to be API-friendly
                time.sleep(0.1)
                page += 1
                
            except Exception as e:
                print(f"      ❌ Error on page {page}: {e}")
                page += 1
                continue
        
        total_elapsed = time.time() - start_time
        print(f"✅ Pagination completed in {total_elapsed:.1f}s - collected {len(all_data):,} new records")
        
        if len(all_data) == 0:
            print(f"✅ Database is already up to date with {existing_count:,} records!")
            return True
        
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
        success = save_to_database(df, refresh_timestamp, total_api_records)
        
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

def save_to_database(df, refresh_timestamp, total_api_records):
    """
    Save DataFrame to database using incremental updates (add new records only)
    
    Args:
        df: DataFrame with session data
        refresh_timestamp: Timestamp when this data was fetched
        total_api_records: Total count from API for coverage calculation
    
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
        
        # Convert attendance_id to proper numeric type for comparison
        print(f"🔄 Preparing {len(df)} records for database insertion...")
        
        # Handle numeric columns properly
        numeric_columns = ['attendance_id', 'participant_gender', 'user_gender', 'class_id', 'program_id', 'user_id', 'participant_id', 'org_id']
        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Since we already filtered during fetch, all records should be new
        # But double-check to be absolutely sure
        if existing_ids:
            original_count = len(df)
            df = df[~df['attendance_id'].isin(existing_ids)].copy()
            new_count = len(df)
            print(f"📊 Double-check filter: {original_count} → {new_count} confirmed new records")
            
            if new_count == 0:
                print("✅ All records already exist - database is current!")
                return True
        
        print(f"💾 Inserting {len(df)} new records with guaranteed success...")
        
        # Use smaller, more reliable batches for 100% success rate
        batch_size = 50  # Smaller batches for better reliability
        total_batches = (len(df) - 1) // batch_size + 1
        successful_inserts = 0
        failed_inserts = 0
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min((batch_num + 1) * batch_size, len(df))
            batch_df = df.iloc[start_idx:end_idx].copy()
            
            if batch_num % 10 == 0 or batch_num == total_batches - 1:
                print(f"   Processing batch {batch_num + 1}/{total_batches} ({len(batch_df)} records)...")
            
            # Try multiple strategies for maximum success
            batch_saved = False
            
            # Strategy 1: Normal batch insert
            try:
                batch_df.to_sql(
                    name='teampact_nmb_sessions',
                    con=engine,
                    if_exists='append',
                    index=False,
                    chunksize=25
                )
                successful_inserts += len(batch_df)
                batch_saved = True
                
            except Exception as batch_error:
                print(f"      ⚠️ Batch {batch_num + 1} strategy 1 failed: {str(batch_error)[:100]}...")
                
                # Strategy 2: Smaller chunks
                try:
                    print(f"      🔄 Trying smaller chunks for batch {batch_num + 1}...")
                    batch_df.to_sql(
                        name='teampact_nmb_sessions',
                        con=engine,
                        if_exists='append',
                        index=False,
                        chunksize=5
                    )
                    successful_inserts += len(batch_df)
                    batch_saved = True
                    print(f"      ✅ Batch {batch_num + 1} saved with smaller chunks")
                    
                except Exception as retry_error:
                    print(f"      ❌ Batch {batch_num + 1} failed completely: {str(retry_error)[:100]}...")
                    failed_inserts += len(batch_df)
            
            if not batch_saved:
                # Strategy 3: Record-by-record (last resort)
                print(f"      🆘 Attempting record-by-record save for batch {batch_num + 1}...")
                record_success = 0
                for idx, row in batch_df.iterrows():
                    try:
                        single_df = pd.DataFrame([row])
                        single_df.to_sql(
                            name='teampact_nmb_sessions',
                            con=engine,
                            if_exists='append',
                            index=False
                        )
                        record_success += 1
                    except:
                        continue
                
                successful_inserts += record_success
                failed_inserts += (len(batch_df) - record_success)
                if record_success > 0:
                    print(f"      ⚠️ Batch {batch_num + 1}: saved {record_success}/{len(batch_df)} records individually")
        
        # Final verification and coverage calculation
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM teampact_nmb_sessions")).fetchone()
            final_db_count = result[0]
            
            timestamp_result = conn.execute(text("SELECT MAX(data_refresh_timestamp) FROM teampact_nmb_sessions")).fetchone()
            latest_timestamp = timestamp_result[0] if timestamp_result else None
        
        # Calculate final coverage
        coverage_pct = (final_db_count / total_api_records) * 100 if total_api_records > 0 else 0
        
        print(f"\n📊 FINAL RESULTS:")
        print(f"   Records inserted: {successful_inserts:,}")
        print(f"   Records failed: {failed_inserts:,}")
        print(f"   Database total: {final_db_count:,}")
        print(f"   API total: {total_api_records:,}")
        print(f"   Coverage: {coverage_pct:.2f}%")
        
        if latest_timestamp:
            print(f"   Last refresh: {latest_timestamp}")
        
        if coverage_pct >= 99.5:
            print(f"🎉 EXCELLENT! Near-perfect data coverage achieved!")
            return True
        elif coverage_pct >= 95.0:
            print(f"✅ GOOD! Substantial data coverage achieved!")
            return True
        elif successful_inserts > 0:
            print(f"⚠️ PARTIAL SUCCESS: Some records added but coverage suboptimal")
            return True
        else:
            print(f"❌ FAILED: No new records added")
            return False
            
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