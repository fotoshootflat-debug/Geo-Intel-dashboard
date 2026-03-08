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

import pydeck as pdk

# --- Prepare PyDeck map ---
deck = pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v10",
    initial_view_state=pdk.ViewState(
        latitude=filtered_df[lat_col].mean(),
        longitude=filtered_df[lon_col].mean(),
        zoom=2,
        pitch=0,
    ),
    layers=[
        pdk.Layer(
            "ScatterplotLayer",
            data=filtered_df,
            get_position=[lon_col, lat_col],
            get_fill_color="[255*(FATALITIES/10 + 0.5), 0, 0, 200]",
            get_radius="FATALITIES*5000 + 10000",
            pickable=True,
        )
    ],
    tooltip={
        "html": "<b>Country:</b> {COUNTRY} <br/>"
                "<b>Region:</b> {ADMIN1} <br/>"
                "<b>Event Type:</b> {EVENT_TYPE} <br/>"
                "<b>Sub-event:</b> {SUB_EVENT_TYPE} <br/>"
                "<b>Fatalities:</b> {FATALITIES}",
        "style": {"backgroundColor": "white", "color": "black"},
    },
)

st.pydeck_chart(deck)
