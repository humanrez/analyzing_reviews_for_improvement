import os
from dotenv import load_dotenv
import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(
    page_title="HYDRA MVP",
    layout="wide"
)

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.title("HYDRA MVP Dashboard")
st.write("Dashboard sederhana untuk melihat review aplikasi.")

response = supabase.table("reviews").select("*").execute()
data = response.data

if not data:
    st.warning("Belum ada data review.")
else:
    df = pd.DataFrame(data)

    st.metric("Total Reviews", len(df))

    if "rating" in df.columns:
        st.metric("Average Rating", round(df["rating"].mean(), 2))

    st.subheader("Review Data")
    st.dataframe(df)

    if "rating" in df.columns:
        st.subheader("Rating Distribution")
        st.bar_chart(df["rating"].value_counts().sort_index())