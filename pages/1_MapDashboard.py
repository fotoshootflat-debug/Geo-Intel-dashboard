import streamlit as st
import pandas as pd

st.title("🌍 Global Conflict Intelligence Map")

# Load dataset
try:
    df = pd.read_csv("acled_data.csv", nrows=5000)
except FileNotFoundError:
    st.error("Error: acled_data.csv not found in root folder.")
    st.stop()
except pd.errors.ParserError:
    st.error("Error: Could not parse CSV.")
    st.stop()

# Determine coordinate columns
if "CENTROID_LATITUDE" in df.columns and "CENTROID_LONGITUDE" in df.columns:
    lat_col, lon_col = "CENTROID_LATITUDE", "CENTROID_LONGITUDE"
elif "latitude" in df.columns and "longitude" in df.columns:
    lat_col, lon_col = "latitude", "longitude"
elif "LATITUDE" in df.columns and "LONGITUDE" in df.columns:
    lat_col, lon_col = "LATITUDE", "LONGITUDE"
else:
    st.error("Latitude/Longitude columns not found in dataset.")
    st.stop()

# Convert coordinates to numeric
df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
df = df.dropna(subset=[lat_col, lon_col])

# --- Interactive filter ---
event_types = df["EVENT_TYPE"].unique()
selected_types = st.multiselect("Select event types to display:", event_types, default=event_types)

filtered_df = df[df["EVENT_TYPE"].isin(selected_types)]

# --- Prepare map data ---
map_data = filtered_df[[lat_col, lon_col]]
map_data.columns = ["lat", "lon"]

# --- Show map ---
st.map(map_data)

st.write(f"Showing {len(filtered_df)} conflict events for selected types.")
