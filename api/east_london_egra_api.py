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
            
            # Handle survey responses API structure (different from session API)
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
                
                # Handle different answer types
                if isinstance(answer_value, dict):
                    # This is likely the EGRA assessment data
                    if 'cells' in answer_value:
                        # Extract EGRA summary stats
                        record[f'{column_name} - Total Correct'] = answer_value.get('total_correct')
                        record[f'{column_name} - Total Attempted'] = answer_value.get('total_attempted')
                        record[f'{column_name} - Total Incorrect'] = answer_value.get('total_incorrect')
                        record[f'{column_name} - Total Incomplete'] = answer_value.get('total_incomplete')
                        record[f'{column_name} - Timer Elapsed'] = answer_value.get('timer_elapsed')
                        record[f'{column_name} - Stop Rule'] = answer_value.get('stop_rule')
                        record[f'{column_name} - Assessment Completed'] = answer_value.get('assessment_completed')
                        record[f'{column_name} - Total Time Taken'] = answer_value.get('total_time_taken')
                        record[f'{column_name} - Final Attempted'] = answer_value.get('final_attempted')
                        
                        # Extract individual cell results (optional - creates many columns)
                        # cells = answer_value.get('cells', [])
                        # for i, cell in enumerate(cells):
                        #     cell_id = cell.get('cell_id', f'cell_{i}')
                        #     status = cell.get('status')
                        #     time_taken = cell.get('time_taken', 0)
                        #     
                        #     record[f'{column_name} - Cell {i}_{cell_id} - Status'] = status
                        #     record[f'{column_name} - Cell {i}_{cell_id} - Time'] = time_taken
                    else:
                        # Other dict format, convert to string
                        record[column_name] = str(answer_value)
                else:
                    # Simple answer value
                    record[column_name] = answer_value
        
        flattened_records.append(record)
    
    df = pd.DataFrame(flattened_records)
    print(f"  Processed {len(df)} records with {len(df.columns)} columns")
    
    return df

def fetch_east_london_egra_data():
    """Fetch data from the three East London EGRA surveys and return as DataFrames"""
    try:
        # API configuration
        api_token = os.getenv('TEAMPACT_API_TOKEN', '')
        
        if not api_token:
            print("Error: TEAMPACT_API_TOKEN not found in environment variables")
            return None, None, None
        
        # Survey IDs for each language
        survey_ids = {
            'xhosa': 644,
            'english': 646, 
            'afrikaans': 647
        }
        
        print(f"Starting East London EGRA data fetch...")
        
        # Fetch data for each language
        xhosa_responses, xhosa_questions = fetch_survey_responses(survey_ids['xhosa'], api_token)
        english_responses, english_questions = fetch_survey_responses(survey_ids['english'], api_token)
        afrikaans_responses, afrikaans_questions = fetch_survey_responses(survey_ids['afrikaans'], api_token)
        
        if not all([xhosa_responses, english_responses, afrikaans_responses]):
            print("Failed to fetch data from one or more surveys")
            return None, None, None
        
        # Process and flatten the data for each language
        xhosa_df = process_survey_data(xhosa_responses, xhosa_questions, 644) if xhosa_responses else pd.DataFrame()
        english_df = process_survey_data(english_responses, english_questions, 646) if english_responses else pd.DataFrame()
        afrikaans_df = process_survey_data(afrikaans_responses, afrikaans_questions, 647) if afrikaans_responses else pd.DataFrame()
        
        print(f"✅ East London EGRA data loaded successfully!")
        print(f"Records: isiXhosa ({len(xhosa_df)}), English ({len(english_df)}), Afrikaans ({len(afrikaans_df)})")
        
        return xhosa_df, english_df, afrikaans_df
    
    except Exception as e:
        print(f"Error loading East London EGRA API data: {str(e)}")
        return None, None, None

def save_east_london_data():
    """Fetch and save East London EGRA data to files"""
    try:
        xhosa_df, english_df, afrikaans_df = fetch_east_london_egra_data()
        
        if all(df is not None for df in [xhosa_df, english_df, afrikaans_df]):
            # Ensure data directory exists
            os.makedirs('data/east_london_egra', exist_ok=True)
            
            # Save each DataFrame with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            xhosa_df.to_csv(f'data/east_london_egra/survey644_isixhosa_{timestamp}.csv', index=False)
            english_df.to_csv(f'data/east_london_egra/survey646_english_{timestamp}.csv', index=False)
            afrikaans_df.to_csv(f'data/east_london_egra/survey647_afrikaans_{timestamp}.csv', index=False)
            
            # Also save as latest files for easy access
            xhosa_df.to_csv('data/east_london_egra/latest_isixhosa.csv', index=False)
            english_df.to_csv('data/east_london_egra/latest_english.csv', index=False)
            afrikaans_df.to_csv('data/east_london_egra/latest_afrikaans.csv', index=False)
            
            print(f"Data saved successfully at {datetime.now()}")
            print(f"Files created in data/east_london_egra/ directory")
            
            return True
        else:
            print("Failed to fetch data - no files saved")
            return False
            
    except Exception as e:
        print(f"Error saving East London EGRA data: {str(e)}")
        return False

if __name__ == "__main__":
    save_east_london_data()
