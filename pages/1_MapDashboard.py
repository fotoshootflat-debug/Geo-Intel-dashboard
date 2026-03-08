import streamlit as st
import pandas as pd
import pydeck as pdk
import glob

st.title("🌍 Global Conflict Intelligence Map")

# -----------------------------
# LOAD ALL DATASETS
# -----------------------------
data_files = glob.glob("data/*.csv")
if not data_files:
    st.error("No CSV data files found in /data folder.")
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
# STANDARDIZE COLUMN NAMES
# -----------------------------
combined_df.columns = combined_df.columns.str.lower()

# Detect latitude/longitude columns
lat_options = ["latitude", "lat", "y", "centroid_latitude"]
lon_options = ["longitude", "lon", "lng", "x", "centroid_longitude"]

lat_col = next((col for col in combined_df.columns if col in lat_options), None)
lon_col = next((col for col in combined_df.columns if col in lon_options), None)

if lat_col is None or lon_col is None:
    st.warning("No coordinate data found. Map will not display.")
    map_df = pd.DataFrame()  # empty dataframe
else:
    # Rename detected columns
    combined_df = combined_df.rename(columns={lat_col: "LATITUDE", lon_col: "LONGITUDE"})

    # Standardize optional columns
    combined_df["event_type"] = combined_df.get("event_type", "Unknown")
    combined_df["fatalities"] = combined_df.get("fatalities", 0)
    combined_df["country"] = combined_df.get("country", "Unknown")
    combined_df["admin1"] = combined_df.get("admin1", "")

    # Drop rows without coordinates
    map_df = combined_df.dropna(subset=["LATITUDE", "LONGITUDE"])

# -----------------------------
# ANALYST METRICS
# -----------------------------
if not map_df.empty:
    total_events = map_df["event_type"].count()
    total_fatalities = map_df["fatalities"].sum()
    countries_affected = map_df["country"].nunique()
    most_common_event = map_df["event_type"].mode()[0]

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Events", int(total_events))
    col2.metric("Total Fatalities", int(total_fatalities))
    col3.metric("Countries Affected", countries_affected)
    col4.metric("Most Common Event", most_common_event)
else:
    st.info("No coordinate-based data available for metrics.")

# -----------------------------
# EVENT TYPE FILTER (sidebar)
# -----------------------------
if not map_df.empty:
    event_types = map_df["event_type"].unique()
    selected_types = st.sidebar.multiselect(
        "Select event types to display:", event_types, default=list(event_types)
    )
    filtered_df = map_df[map_df["event_type"].isin(selected_types)]
else:
    filtered_df = pd.DataFrame()

# -----------------------------
# LIMIT ROWS TO AVOID MESSAGE SIZE ERROR
# -----------------------------
MAX_ROWS = 50000
if len(filtered_df) > MAX_ROWS:
    st.warning(f"Dataset too large for map ({len(filtered_df)} rows). Showing first {MAX_ROWS} rows only.")
    filtered_df = filtered_df.head(MAX_ROWS)

# -----------------------------
# COLOR-CODE EVENTS
# -----------------------------
event_colors = {
    "War": [255, 0, 0, 140],
    "Crime": [0, 0, 255, 140],
    "Cybercrime": [0, 255, 0, 140],
    "Political Violence": [255, 165, 0, 140],
    "Unknown": [128, 128, 128, 140]
}

if not filtered_df.empty:
    # Fix TypeError by using apply instead of fillna
    filtered_df["color"] = filtered_df["event_type"].apply(lambda x: event_colors.get(x, [128,128,128,140]))

# -----------------------------
# MAP
# -----------------------------
if not filtered_df.empty:
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=filtered_df,
        get_position=["LONGITUDE", "LATITUDE"],
        get_fill_color="color",
        get_radius=50000,
        pickable=True,
    )

    tooltip = {
        "html": "<b>Country:</b> {country} <br/>"
                "<b>Region:</b> {admin1} <br/>"
                "<b>Event Type:</b> {event_type} <br/>"
                "<b>Fatalities:</b> {fatalities}",
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
