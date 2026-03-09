# pages/Live_Geopolitical_Insights.py
import streamlit as st
import pandas as pd
import requests
import pydeck as pdk
from io import BytesIO
from fpdf import FPDF

st.set_page_config(page_title="Live Geopolitical Insights", layout="wide")
st.title("🌍 Live Geopolitical Insights Dashboard")

# -----------------------------
# LIVE GDELT FEED
# -----------------------------
GDELT_URL = "https://api.gdeltproject.org/api/v2/events/geocoded?query=&mode=CSV&format=CSV&maxrecords=1000"

@st.cache_data(ttl=300)  # cache 5 min
def load_gdelt():
    try:
        df = pd.read_csv(GDELT_URL)
        if "ActionGeo_Lat" in df.columns and "ActionGeo_Long" in df.columns:
            df = df.rename(columns={
                "ActionGeo_Lat": "LATITUDE",
                "ActionGeo_Long": "LONGITUDE",
                "Actor1Name": "ACTOR1",
                "Actor2Name": "ACTOR2",
                "EventRootCode": "EVENT_TYPE",
                "EventCode": "SUB_EVENT_TYPE",
                "GoldsteinScale": "SCORE"
            })
        return df
    except Exception as e:
        st.error(f"Failed to load GDELT: {e}")
        return pd.DataFrame()

gdelt_df = load_gdelt()

if gdelt_df.empty:
    st.warning("No live events available right now.")
    st.stop()
# -----------------------------
# GLOBAL HOTSPOT OVERVIEW
# -----------------------------
st.subheader("🌐 Global Event Hotspots (Last 1000 events)")

hotspot_df = gdelt_df.dropna(subset=["LATITUDE", "LONGITUDE"])

# Assign colors by event type (example)
event_colors = {
    "14": [255, 0, 0, 180],    # war
    "13": [0, 0, 255, 180],    # protest
    "19": [0, 255, 0, 180],    # cybercrime
}

hotspot_df["color"] = hotspot_df["EVENT_TYPE"].map(event_colors)
hotspot_df["color"] = hotspot_df["color"].apply(lambda x: x if isinstance(x, list) else [128,128,128,140])

hotspot_layer = pdk.Layer(
    "ScatterplotLayer",
    data=hotspot_df,
    get_position=["LONGITUDE","LATITUDE"],
    get_fill_color="color",
    get_radius=20000,
    pickable=True
)

hotspot_deck = pdk.Deck(
    map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    initial_view_state=pdk.ViewState(
        latitude=0,
        longitude=0,
        zoom=1.5,
        pitch=0
    ),
    layers=[hotspot_layer],
    tooltip={
        "html": "<b>Country:</b> {ActionGeo_CountryCode} <br/>"
                "<b>Event Type:</b> {EVENT_TYPE} <br/>"
                "<b>Sub-event:</b> {SUB_EVENT_TYPE} <br/>"
                "<b>Actor1:</b> {ACTOR1} <br/>"
                "<b>Actor2:</b> {ACTOR2} <br/>"
                "<b>Score:</b> {SCORE}",
        "style": {"backgroundColor": "white","color":"black"}
    }
)

st.pydeck_chart(hotspot_deck)
# -----------------------------
# FILTER BY COUNTRY
# -----------------------------
countries = gdelt_df["ActionGeo_CountryCode"].dropna().unique()
country_selected = st.selectbox("Select Country (ISO Code)", countries)

country_df = gdelt_df[gdelt_df["ActionGeo_CountryCode"] == country_selected]

# -----------------------------
# METRICS
# -----------------------------
total_events = len(country_df)
st.subheader(f"Metrics for {country_selected}")
col1, col2 = st.columns(2)
col1.metric("Total Events (Last 1000)", total_events)
col2.metric("Average Goldstein Score", round(country_df["SCORE"].mean(),2) if "SCORE" in country_df.columns else "N/A")

# -----------------------------
# MAP VIEW
# -----------------------------
# -----------------------------
# MAP VIEW with color-coded events
# -----------------------------
if not country_df.empty:
    country_df = country_df.dropna(subset=["LATITUDE", "LONGITUDE"])

    # Define colors for event types
    event_colors = {
        "14": [255, 0, 0, 180],    # Example: war = red
        "13": [0, 0, 255, 180],    # protest = blue
        "19": [0, 255, 0, 180],    # cybercrime = green
    }
    # Default color if event type not in dict
    country_df["color"] = country_df["EVENT_TYPE"].map(event_colors)
    country_df["color"] = country_df["color"].apply(lambda x: x if isinstance(x, list) else [128,128,128,140])

    layer = pdk.Layer(
        "ScatterplotLayer",
        data=country_df,
        get_position=["LONGITUDE","LATITUDE"],
        get_fill_color="color",
        get_radius=15000,  # smaller radius for clarity
        pickable=True
    )

    deck = pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        initial_view_state=pdk.ViewState(
            latitude=country_df["LATITUDE"].mean(),
            longitude=country_df["LONGITUDE"].mean(),
            zoom=2,
            pitch=0
        ),
        layers=[layer],
        tooltip={
            "html": "<b>Event Type:</b> {EVENT_TYPE} <br/>"
                    "<b>Sub-event:</b> {SUB_EVENT_TYPE} <br/>"
                    "<b>Actor1:</b> {ACTOR1} <br/>"
                    "<b>Actor2:</b> {ACTOR2} <br/>"
                    "<b>Score:</b> {SCORE}",
            "style": {"backgroundColor": "white","color":"black"}
        }
    )
    st.pydeck_chart(deck)
else:
    st.info("No events with coordinates for this country.")

# -----------------------------
# RECENT EVENTS FEED
# -----------------------------
st.subheader("Recent Events")
st.dataframe(country_df[["EVENT_TYPE","SUB_EVENT_TYPE","ACTOR1","ACTOR2","SCORE","LATITUDE","LONGITUDE"]].head(20))

# -----------------------------
# DOWNLOAD PDF REPORT
# -----------------------------
if st.button("Download Country Report PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial","B",16)
    pdf.cell(0,10,f"Geopolitical Report — {country_selected}",ln=True,align="C")
    pdf.ln(10)
    pdf.set_font("Arial","",12)
    pdf.multi_cell(0,8,f"Total Events: {total_events}")
    pdf.multi_cell(0,8,f"Average Goldstein Score: {round(country_df['SCORE'].mean(),2) if 'SCORE' in country_df.columns else 'N/A'}")
    pdf.ln(5)
    pdf.multi_cell(0,8,"Recent Events:")
    for i,row in country_df.head(10).iterrows():
        pdf.multi_cell(0,8,f"{row['EVENT_TYPE']} — {row['SUB_EVENT_TYPE']} — {row['ACTOR1']} vs {row['ACTOR2']} (Score: {row['SCORE']})")

    pdf_buffer = BytesIO()
    pdf.output(pdf_buffer)
    pdf_buffer.seek(0)

    st.download_button(
        label="Download PDF",
        data=pdf_buffer,
        file_name=f"{country_selected}_LiveReport.pdf",
        mime="application/pdf"
    )
