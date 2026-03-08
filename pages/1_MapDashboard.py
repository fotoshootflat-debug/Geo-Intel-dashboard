# pages/1_MapDashboard.py
import streamlit as st
import pandas as pd
import pydeck as pdk
import os

st.title("🌍 Global Conflict Intelligence Map")

# --- Step 1: Load datasets ---
data_files = {
    "ACLED": "acled_data.csv",
    "War": "data/war.csv",
    "Crime": "data/crime.csv",
    "Cybercrime": "data/cyber.csv"
}

dfs = {}
for key, file in data_files.items():
    if os.path.exists(file):
        try:
            dfs[key] = pd.read_csv(file)
        except Exception as e:
            st.error(f"Error reading {file}: {e}")
            dfs[key] = pd.DataFrame()
    else:
        st.warning(f"{file} not found, skipping {key} dataset.")
        dfs[key] = pd.DataFrame()

# --- Step 2: Ensure coordinate columns ---
for key, df in dfs.items():
    if not df.empty:
        if "CENTROID_LATITUDE" in df.columns and "CENTROID_LONGITUDE" in df.columns:
            lat_col, lon_col = "CENTROID_LATITUDE", "CENTROID_LONGITUDE"
        elif "latitude" in df.columns and "longitude" in df.columns:
            lat_col, lon_col = "latitude", "longitude"
        else:
            st.warning(f"{key} dataset has no coordinates, will be ignored.")
            dfs[key] = pd.DataFrame()
    else:
        dfs[key] = pd.DataFrame()

# --- Step 3: Clean coordinates ---
for df in dfs.values():
    if not df.empty:
        df[lat_col] = pd.to_numeric(df[lat_col], errors="coerce")
        df[lon_col] = pd.to_numeric(df[lon_col], errors="coerce")
        df.dropna(subset=[lat_col, lon_col], inplace=True)

# --- Step 4: Combine datasets ---
combined_df = pd.concat([df for df in dfs.values() if not df.empty], ignore_index=True)

# --- Step 5: Ensure required columns ---
for col in ["EVENTS","FATALITIES","COUNTRY","EVENT_TYPE","ADMIN1","SUB_EVENT_TYPE"]:
    if col not in combined_df.columns:
        combined_df[col] = 0 if col in ["EVENTS","FATALITIES"] else "Unknown"

combined_df["EVENTS"] = combined_df["EVENTS"].apply(lambda x: int(x) if pd.notna(x) else 1)

# --- Step 6: Analyst Metrics ---
total_events = combined_df["EVENTS"].sum()
total_fatalities = combined_df["FATALITIES"].sum()
countries_affected = combined_df["COUNTRY"].nunique()
most_common_event = combined_df["EVENT_TYPE"].mode()[0] if not combined_df["EVENT_TYPE"].empty else "Unknown"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Events", int(total_events))
col2.metric("Total Fatalities", int(total_fatalities))
col3.metric("Countries Affected", countries_affected)
col4.metric("Most Common Event", most_common_event)

# --- Step 7: Event color mapping ---
color_map = {
    "Battles": [255, 0, 0],
    "Violence against civilians": [255, 140, 0],
    "Protests": [0, 102, 255],
    "Riots": [255, 215, 0],
    "Strategic developments": [160, 32, 240],
    "War": [128, 0, 0],
    "Crime": [0, 128, 0],
    "Cybercrime": [0, 255, 255]
}

combined_df["color"] = combined_df["EVENT_TYPE"].map(color_map)
combined_df["color"] = combined_df["color"].apply(lambda x: x if isinstance(x, list) else [200, 200, 200])

# --- Step 8: Event type filter ---
selected_types = st.multiselect(
    "Select event types to display:",
    combined_df["EVENT_TYPE"].unique(),
    default=combined_df["EVENT_TYPE"].unique()
)

filtered_df = combined_df[combined_df["EVENT_TYPE"].isin(selected_types)]
filtered_df = filtered_df.dropna(subset=[lat_col, lon_col])

# --- Step 9: Build PyDeck map ---
layer = pdk.Layer(
    "ScatterplotLayer",
    data=filtered_df,
    get_position=[lon_col, lat_col],
    get_fill_color="color",
    get_radius=50000,
    pickable=True
)

tooltip = {
    "html": "<b>Country:</b> {COUNTRY} <br/>"
            "<b>Region:</b> {ADMIN1} <br/>"
            "<b>Event Type:</b> {EVENT_TYPE} <br/>"
            "<b>Sub-event:</b> {SUB_EVENT_TYPE} <br/>"
            "<b>Fatalities:</b> {FATALITIES}",
    "style": {"backgroundColor": "white", "color": "black"}
}

deck = pdk.Deck(
    map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    initial_view_state=pdk.ViewState(
        latitude=filtered_df[lat_col].mean() if not filtered_df.empty else 0,
        longitude=filtered_df[lon_col].mean() if not filtered_df.empty else 0,
        zoom=2,
        pitch=0
    ),
    layers=[layer],
    tooltip=tooltip
)

st.pydeck_chart(deck)
