import pandas as pd
import sqlalchemy as sa, os, streamlit as st
from dotenv import load_dotenv
load_dotenv()

engine = sa.create_engine(os.getenv("DATABASE_URL"))

df = pd.read_sql("SELECT * FROM public.api_teampactsession LIMIT 10;", engine)
st.dataframe(df)