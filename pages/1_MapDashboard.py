# pages/1_MapDashboard.py
import streamlit as st
import pandas as pd
import pydeck as pdk

st.title("🌍 Global Conflict Intelligence Map")

# --- Load ACLED dataset ---
try:
    df = pd.read_csv("acled_data.csv")
except FileNotFoundError:
    st.error("Error: acled_data.csv not found in repository.")
    st.stop()
except pd.errors.ParserError:
    st.error("Error: Could not parse CSV file.")
    st.stop()

# --- Analyst Metrics ---
total_events = df["EVENTS"].sum()
total_fatalities = df["FATALITIES"].sum()
countries_affected = df["COUNTRY"].nunique()
most_common_event = df["EVENT_TYPE"].mode()[0]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Events", int(total_events))
col2.metric("Total Fatalities", int(total_fatalities))
col3.metric("Countries Affected", countries_affected)
col4.metric("Most Common Event", most_common_event)

# --- Detect coordinate columns ---
if "CENTROID_LATITUDE" in df.columns and "CENTROID_LONGITUDE" in df.columns:
    lat_col, lon_col = "CENTROID_LATITUDE", "CENTROID_LONGITUDE"
elif "latitude" in df.columns and "longitude" in df.columns:
    lat_col, lon_col = "latitude", "longitude"
elif "LATITUDE" in df.columns and "LONGITUDE" in df.columns:
    lat_col, lon_col = "LATITUDE", "LONGITUDE"
else:
    st.error("Latitude/Longitude columns not found in dataset.")
    st.stop()

# --- Clean coordinates ---
df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
df = df.dropna(subset=[lat_col, lon_col])

# --- Simulate live feeds for Crime and Cybercrime ---
crime_feed = pd.DataFrame(columns=df.columns)  # placeholder
cyber_feed = pd.DataFrame(columns=df.columns)  # placeholder

# You can replace above placeholders with real API calls later

# --- Combine datasets ---
combined_df = pd.concat([df, crime_feed, cyber_feed], ignore_index=True)

# --- Event color mapping ---
color_map = {
    "Battles": [255, 0, 0],                       # Red
    "Violence against civilians": [255, 140, 0],  # Orange
    "Protests": [0, 102, 255],                    # Blue
    "Riots": [255, 215, 0],                       # Yellow
    "Strategic developments": [160, 32, 240],    # Purple
    "War": [128, 0, 0],                           # Dark red
    "Crime": [0, 128, 0],                         # Green
    "Cybercrime": [0, 255, 255]                   # Cyan
}

combined_df["color"] = combined_df["EVENT_TYPE"].map(color_map)
combined_df["color"] = combined_df["color"].apply(lambda x: x if isinstance(x, list) else [200, 200, 200])

# --- Event type filter ---
selected_types = st.multiselect(
    "Select event types to display:",
    combined_df["EVENT_TYPE"].unique(),
    default=combined_df["EVENT_TYPE"].unique()
)

filtered_df = combined_df[combined_df["EVENT_TYPE"].isin(selected_types)]
filtered_df = filtered_df.dropna(subset=[lat_col, lon_col])

# --- Prepare PyDeck layer ---
layer = pdk.Layer(
    "ScatterplotLayer",
    data=filtered_df,
    get_position=[lon_col, lat_col],
    get_fill_color="color",
    get_radius=50000,
    pickable=True
)

# --- Tooltip ---
tooltip = {
    "html": "<b>Country:</b> {COUNTRY} <br/>"
            "<b>Region:</b> {ADMIN1} <br/>"
            "<b>Event Type:</b> {EVENT_TYPE} <br/>"
            "<b>Sub-event:</b> {SUB_EVENT_TYPE} <br/>"
            "<b>Fatalities:</b> {FATALITIES}",
    "style": {"backgroundColor": "white", "color": "black"}
}

# --- Render Map ---
deck = pdk.Deck(
    map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    initial_view_state=pdk.ViewState(
        latitude=filtered_df[lat_col].mean(),
        longitude=filtered_df[lon_col].mean(),
        zoom=2,
        pitch=0
    ),
    layers=[layer],
    tooltip=tooltip
)

st.pydeck_chart(deck)
