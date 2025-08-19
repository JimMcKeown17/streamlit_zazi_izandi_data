import streamlit as st
import requests
import time
import os
import dotenv

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