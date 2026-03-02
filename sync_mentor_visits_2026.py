"""
Sync script for mentor_visits_2026 database table.
Fetches Survey 824 from TeamPact API and writes to PostgreSQL.

Run manually or via cron/Render job:
    python sync_mentor_visits_2026.py
"""

import os
import sys
import requests
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

SURVEY_ID = 824
BASE_URL = "https://teampact.co/api/analytics/v1"
TABLE_NAME = "mentor_visits_2026"

# Map question_id → snake_case DB column name
# Derived from survey 824 questions endpoint
QUESTION_ID_TO_COL = {
    28270: "mentor_name",
    28271: "school_name",
    28272: "ea_name",
    28273: "grade",
    28274: "class_name",
    28275: "grouping_correct",
    28276: "grouping_explanation",
    28277: "letter_tracker_correct",
    28278: "comment_section_usage",
    28279: "teaching_correct_letters",
    28280: "mastery_before_blending",
    28281: "learner_engagement",
    28282: "ea_energy_preparation",
    28283: "session_quality",
    28284: "sessions_per_day",
    28285: "teacher_relationship",
    28286: "trouble_getting_children",
    28287: "additional_commentary",
}


def fetch_all_responses(api_token):
    """Fetch all responses from survey 824 with pagination."""
    headers = {
        "Authorization": f"Bearer {api_token}",
        "Content-Type": "application/json",
    }
    all_responses = []
    page = 1

    while True:
        url = f"{BASE_URL}/surveys/{SURVEY_ID}/responses"
        params = {"page": page, "per_page": 100}
        try:
            r = requests.get(url, headers=headers, params=params, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"API error on page {page}: {e}")
            break

        survey_responses = data.get("data", {}).get("survey_responses", [])
        if not survey_responses:
            break

        all_responses.extend(survey_responses)

        meta = data.get("meta", {})
        total_pages = meta.get("last_page", 1)
        print(f"  Fetched page {page}/{total_pages} — {len(survey_responses)} records")

        if page >= total_pages or not data.get("links", {}).get("next"):
            break
        page += 1

    print(f"Total responses fetched: {len(all_responses)}")
    return all_responses


def process_responses(responses):
    """Flatten API responses into a DataFrame using the question_id → col mapping."""
    records = []
    now_utc = datetime.now(timezone.utc)

    for resp in responses:
        record = {
            "response_id": resp.get("response_id"),
            "survey_id": resp.get("survey_id"),
            "user_id": resp.get("user_id"),
            "user_name": resp.get("user_name"),
            "response_start_at": resp.get("response_start_at"),
            "response_end_at": resp.get("response_end_at"),
            "duration_minutes": resp.get("duration_minutes"),
            "is_completed": resp.get("is_completed"),
            "data_refresh_timestamp": now_utc,
        }
        # Initialize all question columns to empty string
        for col in QUESTION_ID_TO_COL.values():
            record[col] = ""

        # Map each answer by question_id
        for answer in resp.get("answers", []):
            q_id = answer.get("question_id")
            col = QUESTION_ID_TO_COL.get(q_id)
            if col:
                val = answer.get("answer")
                record[col] = val if val is not None else ""

        records.append(record)

    df = pd.DataFrame(records)
    for col in ["response_start_at", "response_end_at"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", utc=True)
    return df


def write_to_db(df):
    """Write DataFrame to mentor_visits_2026, replacing all rows."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from database_utils import get_database_engine

    engine = get_database_engine()
    df.to_sql(TABLE_NAME, engine, if_exists="replace", index=False)
    print(f"Wrote {len(df)} rows to {TABLE_NAME}")


def main():
    api_token = os.getenv("TEAMPACT_API_TOKEN", "")
    if not api_token:
        print("ERROR: TEAMPACT_API_TOKEN not set")
        sys.exit(1)

    print(f"=== Syncing survey {SURVEY_ID} → {TABLE_NAME} ===")
    print(f"Started at {datetime.now()}")
    print()

    print("Fetching responses from API...")
    responses = fetch_all_responses(api_token)
    if not responses:
        print("No responses returned — aborting.")
        sys.exit(1)

    print("\nProcessing responses...")
    df = process_responses(responses)
    print(f"Processed {len(df)} rows × {len(df.columns)} columns")

    # Quick sanity check
    non_empty_mentor = (df["mentor_name"].str.strip() != "").sum()
    print(f"Rows with non-empty mentor_name: {non_empty_mentor}")

    print("\nWriting to database...")
    write_to_db(df)

    print(f"\nDone at {datetime.now()}")


if __name__ == "__main__":
    main()
