import streamlit as st
import pandas as pd
import os

st.title("📊 Global Conflict Analytics")

# Load Political Violence dataset
file_path = "data/political_violence.csv"

if not os.path.exists(file_path):
    st.error("Political Violence dataset not found.")
    st.stop()

df = pd.read_csv(file_path)

st.subheader("Raw Dataset")
st.dataframe(df.head())

# Try to detect columns automatically
columns = df.columns

# Country analysis
if "country" in columns:
    st.subheader("Top Countries by Political Violence")

    country_counts = df["country"].value_counts().head(10)

    st.bar_chart(country_counts)

# Timeline analysis
date_cols = [c for c in columns if "year" in c.lower() or "month" in c.lower()]

if date_cols:
    st.subheader("Violence Events Over Time")

    timeline = df.groupby(date_cols[0]).size()

    st.line_chart(timeline)

st.success("Analytics loaded successfully")
