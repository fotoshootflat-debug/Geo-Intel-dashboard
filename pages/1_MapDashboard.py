import streamlit as st
import pandas as pd

st.title("🌍 Global Conflict Intelligence Map")

# Load dataset
df = pd.read_csv("acled_data.csv")

# Show column names
st.write("Columns in dataset:")
st.write(df.columns)

# Show first rows
st.write("Preview of dataset:")
st.dataframe(df.head())
