"""
One-time database audit script.
Connects to Render PostgreSQL and lists all tables with row counts, column counts, and sizes.
Run with: python db_audit.py
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def get_engine():
    database_url = os.getenv('RENDER_DATABASE_URL')
    if not database_url:
        raise ValueError("RENDER_DATABASE_URL not found in .env")
    return create_engine(database_url, connect_args={"connect_timeout": 30})

def audit_tables():
    engine = get_engine()

    # Get all user tables with row counts and sizes
    query = text("""
        SELECT
            t.table_name,
            pg_total_relation_size(quote_ident(t.table_name)) as total_bytes,
            pg_size_pretty(pg_total_relation_size(quote_ident(t.table_name))) as total_size,
            (SELECT count(*) FROM information_schema.columns c WHERE c.table_name = t.table_name AND c.table_schema = 'public') as column_count
        FROM information_schema.tables t
        WHERE t.table_schema = 'public'
        AND t.table_type = 'BASE TABLE'
        ORDER BY pg_total_relation_size(quote_ident(t.table_name)) DESC
    """)

    with engine.connect() as conn:
        tables_df = pd.read_sql(query, conn)

    print(f"\n{'='*80}")
    print(f"DATABASE AUDIT - Render PostgreSQL")
    print(f"{'='*80}\n")

    # Get row counts for each table (separate connections to avoid transaction errors)
    results = []
    for _, row in tables_df.iterrows():
        table_name = row['table_name']
        with engine.connect() as conn:
            try:
                count_query = text(f'SELECT COUNT(*) as cnt FROM "{table_name}"')
                count_result = conn.execute(count_query).fetchone()
                row_count = count_result[0]
            except Exception:
                row_count = "?"

            latest = "N/A"
            for ts_col in ['data_refresh_timestamp', 'updated_at', 'created_at', 'submission_date', 'session_started_at']:
                try:
                    ts_query = text(f'SELECT MAX("{ts_col}") as latest FROM "{table_name}"')
                    ts_result = conn.execute(ts_query).fetchone()
                    if ts_result[0] is not None:
                        latest = str(ts_result[0])[:19]
                        break
                except:
                    continue

        results.append({
            'table': table_name,
            'rows': row_count,
            'columns': row['column_count'],
            'size': row['total_size'],
            'latest_data': latest
        })

        # Print results
        print(f"{'Table':<45} {'Rows':>10} {'Cols':>6} {'Size':>12} {'Latest Data':>20}")
        print(f"{'-'*45} {'-'*10} {'-'*6} {'-'*12} {'-'*20}")

        for r in results:
            print(f"{r['table']:<45} {str(r['rows']):>10} {str(r['columns']):>6} {r['size']:>12} {r['latest_data']:>20}")

        print(f"\nTotal tables: {len(results)}")
        print()

        # Also check for Django migration tables
        django_tables = [r for r in results if r['table'].startswith('django_') or r['table'].startswith('auth_')]
        if django_tables:
            print(f"Django infrastructure tables: {len(django_tables)}")
            for t in django_tables:
                print(f"  - {t['table']} ({t['rows']} rows)")

if __name__ == "__main__":
    audit_tables()
