"""
One-time script to export 2025 DB tables to parquet files.
Also exports a full backup of all non-Django tables.
Run with: python export_2025_to_parquet.py
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

def get_engine():
    database_url = os.getenv('RENDER_DATABASE_URL')
    if not database_url:
        raise ValueError("RENDER_DATABASE_URL not found in .env")
    return create_engine(database_url, connect_args={"connect_timeout": 30})

def export_table(engine, query, output_path, description):
    """Export a SQL query result to parquet."""
    print(f"  Exporting {description}...")
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
        df.to_parquet(output_path, index=False)
        print(f"    -> {len(df):,} rows -> {output_path}")
        return len(df)
    except Exception as e:
        print(f"    ERROR: {e}")
        return 0

def main():
    engine = get_engine()

    # Ensure output directories exist
    raw_dir = Path("data/parquet/raw")
    backup_dir = Path("data/parquet/backup")
    raw_dir.mkdir(parents=True, exist_ok=True)
    backup_dir.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("EXPORTING 2025 DATA TO PARQUET")
    print("="*60)
    print()

    # --- 2025 Sessions (filter out 2026 data) ---
    print("[1/3] 2025 Sessions (from teampact_sessions_complete, session_started_at < 2026)")
    export_table(
        engine,
        "SELECT * FROM teampact_sessions_complete WHERE session_started_at < '2026-01-01' ORDER BY session_started_at DESC",
        raw_dir / "2025_sessions.parquet",
        "2025 sessions"
    )

    # --- 2025 Assessment Endline ---
    print("[2/3] 2025 Assessment Endline")
    export_table(
        engine,
        "SELECT * FROM teampact_assessment_endline_2025 ORDER BY response_date DESC",
        raw_dir / "2025_assessment_endline.parquet",
        "2025 endline assessments"
    )

    # --- 2025 Assessment Baseline ---
    print("[3/3] 2025 Assessment Baseline")
    export_table(
        engine,
        "SELECT * FROM teampact_assessment_baseline_2025 ORDER BY response_date DESC",
        raw_dir / "2025_assessment_baseline.parquet",
        "2025 baseline assessments"
    )

    print()
    print("="*60)
    print("FULL TABLE BACKUPS (before cleanup)")
    print("="*60)
    print()

    # Backup all data tables (not Django infra)
    backup_tables = [
        ("teampact_sessions_complete", "Full sessions table including 2026 data"),
        ("teampact_nmb_sessions", "Legacy NMB sessions (will be dropped)"),
        ("api_teampactsession", "Legacy TeamPact sessions (will be dropped)"),
        ("teampact_assessment_endline_2025", "2025 endline assessments"),
        ("teampact_assessment_baseline_2025", "2025 baseline assessments"),
        ("teampact_participants", "TeamPact participants"),
        ("api_tasession", "Legacy TA sessions (SurveyCTO 2024)"),
        ("api_egraassessment", "EGRA assessments (SurveyCTO)"),
        ("api_egralearnerscore", "EGRA learner scores (SurveyCTO)"),
        ("api_egraresponsedetail", "EGRA response details (SurveyCTO)"),
        ("api_mentorvisit", "Mentor visits (SurveyCTO)"),
        ("api_taprofile", "TA profiles"),
    ]

    for table_name, desc in backup_tables:
        export_table(
            engine,
            f'SELECT * FROM "{table_name}"',
            backup_dir / f"{table_name}_backup.parquet",
            f"{table_name} ({desc})"
        )

    print()
    print("Done! All exports saved to data/parquet/")

if __name__ == "__main__":
    main()
