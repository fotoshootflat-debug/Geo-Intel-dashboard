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
# SIDEBAR INTELLIGENCE FILTERS
# -----------------------------
if not map_df.empty:

    st.sidebar.header("Intelligence Filters")

    # Country filter
    countries = sorted(map_df["country"].dropna().unique())
    selected_countries = st.sidebar.multiselect(
        "Select Countries",
        countries,
        default=countries
    )

    # Event type filter
    event_types = sorted(map_df["event_type"].dropna().unique())
    selected_events = st.sidebar.multiselect(
        "Select Event Types",
        event_types,
        default=event_types
    )

    # Fatality threshold
    min_fatalities = st.sidebar.slider(
        "Minimum Fatalities",
        0,
        int(map_df["fatalities"].max()),
        0
    )

    # Apply filters
    filtered_df = map_df[
        (map_df["country"].isin(selected_countries)) &
        (map_df["event_type"].isin(selected_events)) &
        (map_df["fatalities"] >= min_fatalities)
    ]

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
# ROBUST COLOR-CODE EVENTS
# -----------------------------
# First, detect the correct event column
for col_candidate in ["event_type", "eventtype", "type", "EVENT_TYPE"]:
    if col_candidate in filtered_df.columns:
        event_col = col_candidate
        break
else:
    filtered_df["event_type"] = "Unknown"
    event_col = "event_type"

# Define event color mapping
event_colors = {
    "war": [255, 0, 0, 140],
    "crime": [0, 0, 255, 140],
    "cybercrime": [0, 255, 0, 140],
    "political violence": [255, 165, 0, 140],
}

# Function to normalize and map any event type to color
def map_event_color(event_value):
    if pd.isna(event_value):
        return [128,128,128,140]  # gray
    e = str(event_value).lower()
    if "war" in e:
        return event_colors["war"]
    elif "cyber" in e:
        return event_colors["cybercrime"]
    elif "crime" in e:
        return event_colors["crime"]
    elif "political" in e:
        return event_colors["political violence"]
    else:
        return [128,128,128,140]  # gray for unknown

# Apply mapping
filtered_df["color"] = filtered_df[event_col].apply(map_event_color)
# -----------------------------
# MAP
# -----------------------------
if not filtered_df.empty:
    heatmap_layer = pdk.Layer(
    "HeatmapLayer",
    data=filtered_df,
    get_position=["LONGITUDE", "LATITUDE"],
    aggregation=pdk.types.String("MEAN"),
    get_weight=1,
    radiusPixels=20,
)
    layer = pdk.Layer(
        "ScatterplotLayer",
        data=filtered_df,
        get_position=["LONGITUDE", "LATITUDE"],
        get_fill_color="color",
        get_radius=8000,
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
       deck = pdk.Deck(
    map_style="light",
    initial_view_state=pdk.ViewState(
        latitude=20,
        longitude=0,
        zoom=1.6,
        pitch=0,
    ),
    layers=[heatmap_layer, layer],
    tooltip=tooltip,
)
    )

    st.pydeck_chart(deck)
else:
    st.info("No data with coordinates available for the map.")
