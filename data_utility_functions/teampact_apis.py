import streamlit as st
import requests
import time
import os
import dotenv
import pandas as pd

dotenv.load_dotenv()

api_token = os.getenv("TEAMPACT_API_TOKEN")

def fetch_all_survey_responses(survey_id, api_token, base_url="https://teampact.co/api/analytics/v1"):
    """
    Fetch all survey responses with automatic pagination handling
    """
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    all_responses = []
    page = 1
    per_page = 100  # Max allowed per page
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    while True:
        url = f"{base_url}/surveys/{survey_id}/responses"
        params = {"page": page, "per_page": per_page}
        
        status_text.text(f"Fetching page {page}...")
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Add current page data to our collection
            if 'data' in data and data['data']:
                all_responses.extend(data['data'])
                
                # Update progress
                if 'meta' in data:
                    total_pages = data['meta'].get('last_page', 1)
                    progress_bar.progress(page / total_pages)
                
                # Check if we have more pages
                if 'links' in data and data['links'].get('next'):
                    page += 1
                    time.sleep(0.1)  # Small delay to be nice to the API
                else:
                    break
            else:
                break
                
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {str(e)}")
            return None
        except Exception as e:
            st.error(f"Error processing data: {str(e)}")
            return None
    
    progress_bar.progress(1.0)
    status_text.text(f"✅ Completed! Fetched {len(all_responses)} responses")
    
    return all_responses

def fetch_survey_responses_nested(survey_id, api_token, base_url="https://teampact.co/api/analytics/v1"):
    """
    Fetch all survey responses with nested structure (data.survey_responses)
    Used for EGRA assessments with complex answer structures
    Returns both responses and questions metadata
    """
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json"
    }
    
    all_responses = []
    questions_data = None
    page = 1
    per_page = 100
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    while True:
        url = f"{base_url}/surveys/{survey_id}/responses"
        params = {"page": page, "per_page": per_page}
        
        status_text.text(f"Fetching page {page}...")
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract questions metadata from first page
            if page == 1 and 'data' in data and 'survey_questions' in data['data']:
                questions_data = data['data']['survey_questions']
            
            # Handle nested survey responses API structure
            if 'data' in data and 'survey_responses' in data['data']:
                page_responses = data['data']['survey_responses']
                if page_responses:
                    all_responses.extend(page_responses)
                    
                    # Update progress
                    if 'meta' in data:
                        total_pages = data['meta'].get('last_page', 1)
                        progress_bar.progress(page / total_pages)
                    
                    # Check if we have more pages
                    if 'links' in data and data['links'].get('next'):
                        page += 1
                        time.sleep(0.1)
                    else:
                        break
                else:
                    break
            else:
                st.warning(f"No survey_responses found in API response for page {page}")
                break
                
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {str(e)}")
            return None, None
        except Exception as e:
            st.error(f"Error processing data: {str(e)}")
            return None, None
    
    progress_bar.progress(1.0)
    status_text.text(f"✅ Completed! Fetched {len(all_responses)} responses")
    
    return all_responses, questions_data

def process_egra_survey_data(survey_responses, survey_id):
    """
    Process EGRA survey responses by flattening the nested answer structure
    Extracts EGRA assessment metrics from the cells data
    """
    if not survey_responses:
        return pd.DataFrame()
    
    flattened_records = []
    for response in survey_responses:
        # Start with basic response metadata
        record = {
            'response_id': response.get('response_id'),
            'response_uuid': response.get('response_uuid'),
            'survey_id': response.get('survey_id'),
            'participant_id': response.get('participant_id'),
            'participant_name': response.get('participant_name'),
            'group_id': response.get('group_id'),
            'group_name': response.get('group_name'),
            'user_id': response.get('user_id'),
            'user_name': response.get('user_name'),
            'response_start_at': response.get('response_start_at'),
            'response_end_at': response.get('response_end_at'),
            'response_capture_date': response.get('response_capture_date'),
            'duration_minutes': response.get('duration_minutes'),
            'is_completed': response.get('is_completed'),
            'created_at': response.get('created_at'),
            'updated_at': response.get('updated_at'),
            'notes': response.get('notes'),
        }
        
        # Process answers array
        answers = response.get('answers', [])
        for answer in answers:
            question_id = answer.get('question_id')
            answer_value = answer.get('answer', {})
            
            # Extract EGRA metrics from nested cells structure
            if isinstance(answer_value, dict) and 'cells' in answer_value:
                record['total_correct'] = answer_value.get('total_correct')
                record['total_attempted'] = answer_value.get('total_attempted')
                record['total_incorrect'] = answer_value.get('total_incorrect')
                record['total_incomplete'] = answer_value.get('total_incomplete')
                record['total_time_taken'] = answer_value.get('total_time_taken')
                record['timer_elapsed'] = answer_value.get('timer_elapsed')
                record['stop_rule'] = answer_value.get('stop_rule')
                record['assessment_completed'] = answer_value.get('assessment_completed')
                record['final_attempted'] = answer_value.get('final_attempted')
                record['question_id'] = question_id
        
        flattened_records.append(record)
    
    df = pd.DataFrame(flattened_records)
    
    # Map API column names to match CSV/process_teampact_data expectations
    column_mapping = {
        'response_id': 'Response ID',
        'survey_id': 'Survey ID',
        'user_name': 'Collected By',
        'response_start_at': 'Response Date',
        'participant_id': 'User ID',
        'participant_name': 'Learner First Name',  # Will need to split this
        'total_correct': 'Total cells correct - EGRA Letters',
        'total_incorrect': 'Total cells incorrect - EGRA Letters',
        'total_attempted': 'Total cells attempted - EGRA Letters',
        'total_incomplete': 'Total cells not attempted - EGRA Letters',
        'assessment_completed': 'Assessment Complete? - EGRA Letters',
        'stop_rule': 'Stop rule reached? - EGRA Letters',
        'timer_elapsed': 'Timer elapsed? - EGRA Letters',
        'total_time_taken': 'Time elapsed at completion - EGRA Letters'
    }
    
    df = df.rename(columns=column_mapping)
    
    # Debug: Show what columns we have
    st.info(f"📋 API columns available: {', '.join(df.columns.tolist()[:10])}...")
    
    # Add missing columns that process_teampact_data expects
    if 'First Name' not in df.columns:
        df['First Name'] = ''
    if 'Last Name' not in df.columns:
        df['Last Name'] = ''
    if 'Email' not in df.columns:
        df['Email'] = ''
    if 'Class Name' not in df.columns:
        df['Class Name'] = ''
    if 'Class ID' not in df.columns:
        df['Class ID'] = ''
    if 'Program Name' not in df.columns:
        df['Program Name'] = ''
    if 'Gender' not in df.columns:
        df['Gender'] = ''
    if 'Survey Name' not in df.columns:
        df['Survey Name'] = ''
    if 'Grade ' not in df.columns:  # Note the trailing space
        df['Grade '] = ''
    if 'Class' not in df.columns:
        df['Class'] = ''
    if 'Learner Surname ' not in df.columns:  # Note the trailing space
        df['Learner Surname '] = ''
    if 'Learner Gender' not in df.columns:
        df['Learner Gender'] = ''
    if 'Learner EMIS' not in df.columns:
        df['Learner EMIS'] = ''
    
    return df