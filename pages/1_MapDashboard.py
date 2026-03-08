import streamlit as st
import pandas as pd
import pydeck as pdk
import glob
import os

st.title("🌍 Global Conflict Intelligence Map")

# -----------------------------
# LOAD ALL DATASETS FROM /data
# -----------------------------
data_files = glob.glob("data/*.csv")
if not data_files:
    st.error("No data files found in /data folder.")
    st.stop()

df_list = []
for file in data_files:
    try:
        df = pd.read_csv(file)
        df_list.append(df)
    except Exception as e:
        st.warning(f"Could not load {file}: {e}")

if not df_list:
    st.error("No datasets could be loaded.")
    st.stop()

# Combine all datasets
combined_df = pd.concat(df_list, ignore_index=True)

# -----------------------------
# COLUMN STANDARDIZATION
# -----------------------------
combined_df.columns = combined_df.columns.str.lower()

# Possible coordinate columns
lat_options = ["latitude", "lat", "y", "centroid_latitude"]
lon_options = ["longitude", "lon", "lng", "x", "centroid_longitude"]

lat_col = None
lon_col = None

for col in combined_df.columns:
    if col in lat_options:
        lat_col = col
    if col in lon_options:
        lon_col = col

# Handle datasets without coordinates
if lat_col is None or lon_col is None:
    st.warning("No datasets have coordinates. Map will not display.")
    map_df = pd.DataFrame()  # empty dataframe
else:
    # Rename detected columns
    combined_df = combined_df.rename(columns={lat_col: "LATITUDE", lon_col: "LONGITUDE"})

    # Optional columns
    combined_df["EVENT_TYPE"] = combined_df.get("event_type", "Unknown")
    combined_df["FATALITIES"] = combined_df.get("fatalities", 0)
    combined_df["COUNTRY"] = combined_df.get("country", "Unknown")
    combined_df["ADMIN1"] = combined_df.get("admin1", "")

    # Drop rows without coordinates
    map_df = combined_df.dropna(subset=["LATITUDE", "LONGITUDE"])

# -----------------------------
# ANALYST METRICS
# -----------------------------
if not map_df.empty:
    total_events = map_df["EVENT_TYPE"].count()
    total_fatalities = map_df["FATALITIES"].sum()
    countries_affected = map_df["COUNTRY"].nunique()
    most_common_event = map_df["EVENT_TYPE"].mode()[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Events", int(total_events))
    col2.metric("Total Fatalities", int(total_fatalities))
    col3.metric("Countries Affected", countries_affected)
    col4.metric("Most Common Event", most_common_event)
else:
    st.info("No coordinate-based data available for metrics.")

# -----------------------------
# EVENT TYPE FILTER
# -----------------------------
if not map_df.empty:
    event_types = map_df["EVENT_TYPE"].unique()
    selected_types = st.multiselect(
        "Select event types to display:", event_types, default=list(event_types)
    )
    filtered_df = map_df[map_df["EVENT_TYPE"].isin(selected_types)]
else:
    filtered_df = pd.DataFrame()

# -----------------------------
# MAP
# -----------------------------
if not filtered_df.empty:
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=filtered_df,
        get_position=["LONGITUDE", "LATITUDE"],
        get_fill_color=[255, 0, 0, 140],
        get_radius=50000,
        pickable=True,
    )

    tooltip = {
        "html": "<b>Country:</b> {COUNTRY} <br/>"
                "<b>Region:</b> {ADMIN1} <br/>"
                "<b>Event Type:</b> {EVENT_TYPE} <br/>"
                "<b>Fatalities:</b> {FATALITIES}",
        "style": {"backgroundColor": "white", "color": "black"},
    }

    deck = pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        initial_view_state=pdk.ViewState(
            latitude=filtered_df["LATITUDE"].mean(),
            longitude=filtered_df["LONGITUDE"].mean(),
            zoom=2,
            pitch=0,
        ),
        layers=[layer],
        tooltip=tooltip,
    )

    st.pydeck_chart(deck)
else:
    st.info("No data with coordinates available for the map.")
