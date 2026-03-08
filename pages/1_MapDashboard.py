import streamlit as st
import pandas as pd

st.title("🌍 Global Conflict Intelligence Map")

# Load ACLED dataset
df = pd.read_csv("acled_data.csv")

# Ensure coordinates are numbers
df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

# Remove rows without coordinates
df = df.dropna(subset=["latitude", "longitude"])

st.write("Conflict events from ACLED dataset")

map_data = df[["latitude","longitude"]]
map_data.columns = ["lat","lon"]

st.map(map_data)
