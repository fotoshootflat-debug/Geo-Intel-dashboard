# 1_MapDashboard.py
import streamlit as st
import pandas as pd
import pydeck as pdk
import os
import requests
import io

st.set_page_config(page_title="🌍 Global Conflict Intelligence Map", layout="wide")

st.title("🌍 Global Conflict Intelligence Map")

# -----------------------------
# LOAD REGIONAL CSV FILES
# -----------------------------
data_path = "data"  # folder where CSVs are uploaded

def load_csv(file_name):
    file_path = os.path.join(data_path, file_name)
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    else:
        return pd.DataFrame()

africa_df = load_csv("africa.csv")
asia_df = load_csv("asia_pacific.csv")
europe_df = load_csv("europe_central_asia.csv")
latin_df = load_csv("latin_america_the_caribbean.csv")
us_df = load_csv("us_and_canada.csv")
political_df = load_csv("political_violence.csv")  # optional

# -----------------------------
# FETCH LIVE GDELT EVENTS
# -----------------------------
def fetch_gdelt_events():
    try:
        url = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
        latest_file = requests.get(url).text.split()[-1]
        csv_url = f"http://data.gdeltproject.org/gdeltv2/{latest_file}"

        r = requests.get(csv_url)
        if r.status_code != 200:
            return pd.DataFrame()

        df = pd.read_csv(io.StringIO(r.text), sep="\t", header=None, dtype=str, error_bad_lines=False)
        df = df[[0, 50, 51, 27, 1]]
        df.columns = ["COUNTRY", "LATITUDE", "LONGITUDE", "EVENT_TYPE", "DATE"]
        df = df.dropna(subset=["LATITUDE", "LONGITUDE"])
        df["LATITUDE"] = pd.to_numeric(df["LATITUDE"], errors="coerce")
        df["LONGITUDE"] = pd.to_numeric(df["LONGITUDE"], errors="coerce")
        return df
    except:
        return pd.DataFrame()

gdelt_df = fetch_gdelt_events()

# -----------------------------
# COMBINE CSVs AND GDELT
# -----------------------------
map_df = pd.concat([africa_df, asia_df, europe_df, latin_df, us_df], ignore_index=True)

if not gdelt_df.empty:
    gdelt_df = gdelt_df[gdelt_df["EVENT_TYPE"].str.contains("WAR|CRIME|CYBER", case=False, na=False)]
    map_df = pd.concat([map_df, gdelt_df], ignore_index=True)

# -----------------------------
# CHECK FOR COORDINATES
# -----------------------------
lat_candidates = ["LATITUDE", "latitude", "CENTROID_LATITUDE", "centroid_latitude"]
lon_candidates = ["LONGITUDE", "longitude", "CENTROID_LONGITUDE", "centroid_longitude"]

lat_col = next((c for c in lat_candidates if c in map_df.columns), None)
lon_col = next((c for c in lon_candidates if c in map_df.columns), None)

if not lat_col or not lon_col:
    st.error("Dataset does not contain recognizable latitude/longitude columns.")
    st.stop()

map_df[lat_col] = pd.to_numeric(map_df[lat_col], errors="coerce")
map_df[lon_col] = pd.to_numeric(map_df[lon_col], errors="coerce")
map_df = map_df.dropna(subset=[lat_col, lon_col])

# -----------------------------
# ANALYST METRICS
# -----------------------------
total_events = len(map_df)
total_fatalities = map_df.get("FATALITIES", pd.Series([0]*len(map_df))).sum()
countries_affected = map_df["COUNTRY"].nunique() if "COUNTRY" in map_df.columns else 0
most_common_event = map_df["EVENT_TYPE"].mode()[0] if "EVENT_TYPE" in map_df.columns else "N/A"

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Events", int(total_events))
col2.metric("Total Fatalities", int(total_fatalities))
col3.metric("Countries Affected", countries_affected)
col4.metric("Most Common Event", most_common_event)

# -----------------------------
# EVENT TYPE FILTER (sidebar)
# -----------------------------
if not map_df.empty:
    event_types = map_df["EVENT_TYPE"].unique()
    selected_types = st.sidebar.multiselect(
        "Select event types to display:", event_types, default=list(event_types)
    )
    filtered_df = map_df[map_df["EVENT_TYPE"].isin(selected_types)]
else:
    filtered_df = pd.DataFrame()

# -----------------------------
# SIDEBAR: LATEST LIVE EVENTS
# -----------------------------
if not gdelt_df.empty:
    st.sidebar.subheader("Latest Events (GDELT)")
    latest_events = gdelt_df.sort_values("DATE", ascending=False).head(10)
    for _, row in latest_events.iterrows():
        st.sidebar.write(f"{row['COUNTRY']} — {row['EVENT_TYPE']} — {row['DATE']}")

# -----------------------------
# PREPARE MAP LAYER
# -----------------------------
# Assign colors by event type
event_colors = {}
unique_events = filtered_df["EVENT_TYPE"].unique() if not filtered_df.empty else []
import random
for ev in unique_events:
    event_colors[ev] = [random.randint(50, 255), random.randint(50, 255), random.randint(50, 255), 140]

filtered_df["color"] = filtered_df["EVENT_TYPE"].map(event_colors)
filtered_df["color"] = filtered_df["color"].apply(lambda x: x if isinstance(x, list) else [128, 128, 128, 140])

# Limit rows to prevent browser overload
MAX_ROWS = 50000
if len(filtered_df) > MAX_ROWS:
    st.warning(f"Dataset too large for map ({len(filtered_df)} rows). Showing first {MAX_ROWS} rows only.")
    filtered_df = filtered_df.head(MAX_ROWS)

layer = pdk.Layer(
    "ScatterplotLayer",
    data=filtered_df,
    get_position=[lon_col, lat_col],
    get_fill_color="color",
    get_radius=20000,
    pickable=True,
)

tooltip = {
    "html": "<b>Country:</b> {COUNTRY} <br/>"
            "<b>Event Type:</b> {EVENT_TYPE} <br/>"
            "<b>Fatalities:</b> {FATALITIES} <br/>"
            "<b>Date:</b> {DATE}",
    "style": {"backgroundColor": "white", "color": "black"},
}

deck = pdk.Deck(
    map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    initial_view_state=pdk.ViewState(
        latitude=filtered_df[lat_col].mean() if not filtered_df.empty else 0,
        longitude=filtered_df[lon_col].mean() if not filtered_df.empty else 0,
        zoom=2,
        pitch=0,
    ),
    layers=[layer],
    tooltip=tooltip,
)

st.pydeck_chart(deck)
