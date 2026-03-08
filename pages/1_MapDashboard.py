import streamlit as st
import pandas as pd
import pydeck as pdk
import os

st.title("🌍 Global Intelligence Map")

# -----------------------------
# LOAD DATASETS
# -----------------------------

data_files = {
    "Latin America": "data/latin_america.csv",
    "US & Canada": "data/us_canada.csv",
    "Europe & Central Asia": "data/europe_central_asia.csv"
}

dataframes = []

for name, path in data_files.items():
    if os.path.exists(path):
        df = pd.read_csv(path)
        df["SOURCE"] = name
        dataframes.append(df)
    else:
        st.warning(f"{path} not found, skipping {name} dataset.")

if not dataframes:
    st.error("No datasets found.")
    st.stop()

combined_df = pd.concat(dataframes, ignore_index=True)

# -----------------------------
# STANDARDIZE COLUMNS
# -----------------------------

combined_df.columns = combined_df.columns.str.lower()

# Standardize column names
column_mapping = {
    "latitude": "LATITUDE",
    "longitude": "LONGITUDE",
    "event_type": "EVENT_TYPE",
    "fatalities": "FATALITIES",
    "country": "COUNTRY"
}

combined_df = combined_df.rename(columns=column_mapping)

required_columns = ["LATITUDE", "LONGITUDE"]

for col in required_columns:
    if col not in combined_df.columns:
        st.error(f"Dataset missing required column: {col}")
        st.stop()
# Ensure event type exists
if "EVENT_TYPE" not in combined_df.columns:
    combined_df["EVENT_TYPE"] = "Unknown"

# Ensure fatalities exists
if "FATALITIES" not in combined_df.columns:
    combined_df["FATALITIES"] = 0

# -----------------------------
# SIDEBAR FILTERS
# -----------------------------

st.sidebar.header("🔎 Intelligence Filters")

event_types = st.sidebar.multiselect(
    "Event Type",
    combined_df["EVENT_TYPE"].dropna().unique(),
    default=combined_df["EVENT_TYPE"].dropna().unique()
)

filtered_df = combined_df[combined_df["EVENT_TYPE"].isin(event_types)]

if "COUNTRY" in filtered_df.columns:
    countries = st.sidebar.multiselect(
        "Country",
        filtered_df["COUNTRY"].dropna().unique()
    )

    if countries:
        filtered_df = filtered_df[filtered_df["COUNTRY"].isin(countries)]

if "FATALITIES" in filtered_df.columns:
    max_fatalities = int(filtered_df["FATALITIES"].max())

    fatality_range = st.sidebar.slider(
        "Fatalities Range",
        0,
        max_fatalities,
        (0, max_fatalities)
    )

    filtered_df = filtered_df[
        (filtered_df["FATALITIES"] >= fatality_range[0]) &
        (filtered_df["FATALITIES"] <= fatality_range[1])
    ]

# -----------------------------
# LIMIT DATA FOR PERFORMANCE
# -----------------------------

MAX_POINTS = 50000

if len(filtered_df) > MAX_POINTS:
    filtered_df = filtered_df.sample(MAX_POINTS)

# -----------------------------
# MAP LAYERS
# -----------------------------

scatter_layer = pdk.Layer(
    "ScatterplotLayer",
    data=filtered_df,
    get_position="[LONGITUDE, LATITUDE]",
    get_radius=5000,
    get_fill_color=[255, 0, 0, 140],
    pickable=True,
)

heatmap_layer = pdk.Layer(
    "HeatmapLayer",
    data=filtered_df,
    get_position="[LONGITUDE, LATITUDE]"
)

view_state = pdk.ViewState(
    latitude=20,
    longitude=0,
    zoom=2,
    pitch=40
)

deck = pdk.Deck(
    layers=[heatmap_layer, scatter_layer],
    initial_view_state=view_state,
    tooltip={"text": "{EVENT_TYPE}"}
)

st.pydeck_chart(deck)

# -----------------------------
# METRICS
# -----------------------------

st.subheader("📊 Event Statistics")

col1, col2 = st.columns(2)

total_events = len(filtered_df)
total_fatalities = int(filtered_df["FATALITIES"].sum())

col1.metric("Total Events", total_events)
col2.metric("Total Fatalities", total_fatalities)

# -----------------------------
# DATA PREVIEW
# -----------------------------

with st.expander("View Filtered Dataset"):
    st.dataframe(filtered_df.head(100))
