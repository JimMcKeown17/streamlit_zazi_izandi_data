import sqlalchemy as sa, os, streamlit as st
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

engine = sa.create_engine(os.getenv("DATABASE_URL"))



df = pd.read_sql("""
SELECT schemaname, relname AS table_name, n_live_tup AS estimated_rows
FROM pg_stat_user_tables
ORDER BY n_live_tup DESC
LIMIT 20;
""", engine)
st.dataframe(df)