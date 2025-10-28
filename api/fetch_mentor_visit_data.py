import requests
import json
import pandas as pd
from datetime import datetime
import os

def fetch_survey_responses(survey_id, api_token, base_url="https://teampact.co/api/analytics/v1"):
    """
    Fetch all survey responses for a specific survey with automatic pagination handling
    Returns both the response data and questions metadata
    """
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    all_responses = []
    questions_data = None
    page = 1
    per_page = 100  # Max allowed per page
    
    print(f"Fetching survey {survey_id} data...")
    
    while True:
        url = f"{base_url}/surveys/{survey_id}/responses"
        params = {"page": page, "per_page": per_page}
        
        print(f"  Fetching page {page}...")
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract questions metadata from first page
            if page == 1 and 'questions' in data:
                questions_data = data['questions']
            
            # Handle survey responses API structure
            if 'data' in data and 'survey_responses' in data['data']:
                page_responses = data['data']['survey_responses']
                if page_responses:
                    all_responses.extend(page_responses)
                    
                    # Get pagination metadata
                    if 'meta' in data:
                        total_pages = data['meta'].get('last_page', 1)
                        current_page = data['meta'].get('current_page', page)
                        total = data['meta'].get('total', 0)
                        
                        print(f"  Page {current_page}/{total_pages} - {len(page_responses)} records (Total so far: {len(all_responses)}/{total})")
                    
                    # Check if we have more pages
                    if 'links' in data and data['links'].get('next'):
                        page += 1
                    else:
                        break
                else:
                    break
            else:
                print(f"  No survey_responses found in API response for page {page}")
                break
                
        except requests.exceptions.RequestException as e:
            print(f"API request failed for survey {survey_id}: {str(e)}")
            return None, None
        except Exception as e:
            print(f"Error processing data for survey {survey_id}: {str(e)}")
            return None, None
    
    print(f"  Completed survey {survey_id} - fetched {len(all_responses)} total responses")
    return all_responses, questions_data

def process_survey_data(survey_responses, questions_data, survey_id):
    """
    Process survey responses by flattening answers using question mappings
    """
    if not survey_responses or not questions_data:
        return pd.DataFrame()
    
    print(f"Processing survey {survey_id} data...")
    
    # Create question ID to column name mapping
    question_mapping = {}
    for q in questions_data:
        question_id = str(q.get('question_id'))
        column_name = q.get('column_name', f'question_{question_id}')
        question_mapping[question_id] = column_name
    
    print(f"  Found {len(question_mapping)} question mappings")
    
    # Process each response
    flattened_records = []
    for response in survey_responses:
        # Start with basic response metadata
        record = {
            'response_id': response.get('response_id'),
            'response_uuid': response.get('response_uuid'),
            'survey_id': response.get('survey_id'),
            'user_id': response.get('user_id'),
            'user_name': response.get('user_name'),
            'response_start_at': response.get('response_start_at'),
            'response_end_at': response.get('response_end_at'),
            'duration_minutes': response.get('duration_minutes'),
            'is_completed': response.get('is_completed'),
            'created_at': response.get('created_at'),
            'updated_at': response.get('updated_at')
        }
        
        # Process answers array
        answers = response.get('answers', [])
        for answer in answers:
            question_id = str(answer.get('question_id'))
            answer_value = answer.get('answer')
            
            if question_id in question_mapping:
                column_name = question_mapping[question_id]
                record[column_name] = answer_value
        
        flattened_records.append(record)
    
    df = pd.DataFrame(flattened_records)
    print(f"  Processed {len(df)} records with {len(df.columns)} columns")
    
    return df

def fetch_mentor_visit_data():
    """Fetch data from both old and new mentor visit tracker surveys"""
    try:
        # API configuration
        api_token = os.getenv('TEAMPACT_API_TOKEN', '')
        
        if not api_token:
            print("Error: TEAMPACT_API_TOKEN not found in environment variables")
            return None, None
        
        # Survey IDs
        old_survey_id = 612  # "Mentor Visit Tracker (Copy)"
        new_survey_id = 677  # "New Mentor Visit Tracker."
        
        print(f"Starting Mentor Visit Tracker data fetch...")
        print(f"Old Survey: {old_survey_id}")
        print(f"New Survey: {new_survey_id}")
        print()
        
        # Fetch data for both surveys
        old_responses, old_questions = fetch_survey_responses(old_survey_id, api_token)
        new_responses, new_questions = fetch_survey_responses(new_survey_id, api_token)
        
        if not old_responses and not new_responses:
            print("Failed to fetch data from both surveys")
            return None, None
        
        # Process and flatten the data
        old_df = process_survey_data(old_responses, old_questions, old_survey_id) if old_responses else pd.DataFrame()
        new_df = process_survey_data(new_responses, new_questions, new_survey_id) if new_responses else pd.DataFrame()
        
        print()
        print(f"✅ Mentor Visit Tracker data loaded successfully!")
        print(f"Old Survey Records: {len(old_df)}")
        print(f"New Survey Records: {len(new_df)}")
        
        return old_df, new_df
    
    except Exception as e:
        print(f"Error loading Mentor Visit Tracker API data: {str(e)}")
        return None, None

def save_mentor_visit_data():
    """Fetch and save mentor visit tracker data to files"""
    try:
        old_df, new_df = fetch_mentor_visit_data()
        
        if old_df is not None or new_df is not None:
            # Ensure data directory exists
            os.makedirs('data/mentor_visit_tracker', exist_ok=True)
            
            # Save each DataFrame with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if old_df is not None and not old_df.empty:
                old_df.to_csv(f'data/mentor_visit_tracker/survey612_old_{timestamp}.csv', index=False)
                old_df.to_csv('data/mentor_visit_tracker/latest_old.csv', index=False)
                print(f"Old survey data saved: {len(old_df)} records")
            
            if new_df is not None and not new_df.empty:
                new_df.to_csv(f'data/mentor_visit_tracker/survey677_new_{timestamp}.csv', index=False)
                new_df.to_csv('data/mentor_visit_tracker/latest_new.csv', index=False)
                print(f"New survey data saved: {len(new_df)} records")
            
            print()
            print(f"Data saved successfully at {datetime.now()}")
            print(f"Files created in data/mentor_visit_tracker/ directory")
            
            return True
        else:
            print("Failed to fetch data - no files saved")
            return False
            
    except Exception as e:
        print(f"Error saving Mentor Visit Tracker data: {str(e)}")
        return False

if __name__ == "__main__":
    save_mentor_visit_data()
