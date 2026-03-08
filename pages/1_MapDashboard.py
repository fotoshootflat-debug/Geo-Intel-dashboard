import streamlit as st
import pandas as pd

st.title("🌍 Global Conflict Intelligence Map")

# ---- Safe loading of large ACLED dataset ----
try:
    # Only read first 5000 rows to avoid memory issues
    df = pd.read_csv("acled_data.csv", nrows=5000)
except FileNotFoundError:
    st.error("Error: acled_data.csv not found in the root folder.")
    st.stop()
except pd.errors.ParserError:
    st.error("Error: Could not parse the CSV file. It may be too large or corrupted.")
    st.stop()

# ---- Inspect columns ----
st.write("Columns in dataset:")
columns = list(df.columns)
st.write(columns)

# ---- Determine coordinate columns ----
if "CENTROID_LATITUDE" in df.columns and "CENTROID_LONGITUDE" in df.columns:
    lat_col, lon_col = "CENTROID_LATITUDE", "CENTROID_LONGITUDE"
elif "latitude" in df.columns and "longitude" in df.columns:
    lat_col, lon_col = "latitude", "longitude"
elif "LATITUDE" in df.columns and "LONGITUDE" in df.columns:
    lat_col, lon_col = "LATITUDE", "LONGITUDE"
else:
    st.error("Latitude/Longitude columns not found in dataset.")
    st.stop()

# ---- Convert coordinates to numeric ----
df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")

# ---- Remove rows without coordinates ----
df = df.dropna(subset=[lat_col, lon_col])

# ---- Prepare map data ----
map_data = df[[lat_col, lon_col]]
map_data.columns = ["lat", "lon"]

# ---- Show map ----
st.map(map_data)

st.write(f"Showing {len(df)} conflict events from the dataset.")
