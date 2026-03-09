import streamlit as st
import pandas as pd
import pydeck as pdk
import requests
from io import BytesIO
from fpdf import FPDF

st.set_page_config(page_title="Live Geopolitical Insights", layout="wide")

st.title("🌍 Live Geopolitical Intelligence Dashboard")

# ------------------------------------------------
# LOAD LIVE GDELT DATA
# ------------------------------------------------
@st.cache_data(ttl=600)
def load_gdelt():

    try:

        update_url = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
        r = requests.get(update_url)

        lines = r.text.split("\n")
        latest_line = lines[0]
        zip_url = latest_line.split(" ")[2]

        response = requests.get(zip_url)

        df = pd.read_csv(
            zip_url,
            compression="zip",
            sep="\t",
            header=None,
            low_memory=False
        )

        df = df.rename(columns={
            53: "LATITUDE",
            54: "LONGITUDE",
            7: "ACTOR1",
            17: "ACTOR2",
            26: "EVENT_TYPE",
            27: "SUB_EVENT_TYPE",
            30: "SCORE",
            51: "COUNTRY"
        })

        df = df.dropna(subset=["LATITUDE","LONGITUDE"])

        return df.head(5000)

    except Exception as e:

        st.error(f"GDELT feed error: {e}")
        return pd.DataFrame()

gdelt_df = load_gdelt()

# Convert coordinates safely
gdelt_df["LATITUDE"] = pd.to_numeric(gdelt_df["LATITUDE"], errors="coerce")
gdelt_df["LONGITUDE"] = pd.to_numeric(gdelt_df["LONGITUDE"], errors="coerce")

# Remove rows with invalid coordinates
gdelt_df = gdelt_df.dropna(subset=["LATITUDE", "LONGITUDE"])

gdelt_df = gdelt_df.reset_index(drop=True)

# Convert to pure python types
gdelt_df = gdelt_df.reset_index(drop=True)
# ------------------------------------------------
# GLOBAL HOTSPOT MAP
# ------------------------------------------------

st.subheader("🌐 Global Event Hotspots")

layer = pdk.Layer(
    "ScatterplotLayer",
    data=gdelt_df,
    get_position=["LONGITUDE","LATITUDE"],
    get_fill_color=[255,0,0,160],
    get_radius=20000,
    pickable=True
)

view_state = pdk.ViewState(latitude=20, longitude=0, zoom=1.5)

deck = pdk.Deck(
    map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    initial_view_state=view_state,
    layers=[layer],
    tooltip={
        "html": "<b>{ACTOR1}</b> vs <b>{ACTOR2}</b><br/>Event: {EVENT_TYPE}",
        "style": {"backgroundColor": "white","color": "black"}
    }
)

st.pydeck_chart(deck)

# ------------------------------------------------
# COUNTRY SELECTION
# ------------------------------------------------

st.subheader("Country Intelligence")

countries = sorted(gdelt_df["COUNTRY"].dropna().unique())

country_selected = st.selectbox("Select Country", countries)

country_df = gdelt_df[gdelt_df["COUNTRY"] == country_selected].copy()
country_df["LATITUDE"] = pd.to_numeric(country_df["LATITUDE"], errors="coerce")
country_df["LONGITUDE"] = pd.to_numeric(country_df["LONGITUDE"], errors="coerce")

country_df = country_df.dropna(subset=["LATITUDE", "LONGITUDE"])

country_df["LATITUDE"] = country_df["LATITUDE"].astype(float)
country_df["LONGITUDE"] = country_df["LONGITUDE"].astype(float)

# ------------------------------------------------
# METRICS
# ------------------------------------------------

st.subheader("Country Metrics")

col1,col2 = st.columns(2)

col1.metric("Total Events", len(country_df))

if "SCORE" in country_df.columns:
    col2.metric("Average Score", round(country_df["SCORE"].mean(),2))
else:
    col2.metric("Average Score","N/A")

# ------------------------------------------------
# COUNTRY MAP
# ------------------------------------------------

st.subheader("Country Event Map")

country_layer = pdk.Layer(
    "ScatterplotLayer",
    data=country_df,
    get_position=["LONGITUDE","LATITUDE"],
    get_fill_color=[255,0,0,160],
    get_radius=15000,
    pickable=True
)

country_view = pdk.ViewState(
    latitude=country_df["LATITUDE"].mean() if not country_df.empty else 0,
    longitude=country_df["LONGITUDE"].mean() if not country_df.empty else 0,
    zoom=3
)

country_deck = pdk.Deck(
    map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
    initial_view_state=country_view,
    layers=[country_layer]
)

st.pydeck_chart(country_deck)

# ------------------------------------------------
# RECENT EVENTS TABLE
# ------------------------------------------------

st.subheader("Recent Events")

st.dataframe(
    country_df[["ACTOR1","ACTOR2","EVENT_TYPE","SUB_EVENT_TYPE","SCORE"]].head(20)
)

# ------------------------------------------------
# PDF REPORT
# ------------------------------------------------

st.subheader("Download Intelligence Report")

if st.button("Generate PDF Report"):

    pdf = FPDF()
    pdf.add_page()

    pdf.set_font("Arial","B",16)
    pdf.cell(0,10,f"Country Intelligence Report: {country_selected}",ln=True)

    pdf.set_font("Arial","",12)

    pdf.cell(0,10,f"Total Events: {len(country_df)}",ln=True)

    if "SCORE" in country_df.columns:
        pdf.cell(0,10,f"Average Score: {round(country_df['SCORE'].mean(),2)}",ln=True)

    pdf.ln(10)

    pdf.cell(0,10,"Recent Events:",ln=True)

    for i,row in country_df.head(10).iterrows():
        pdf.multi_cell(
            0,
            8,
            f"{row['ACTOR1']} vs {row['ACTOR2']} | Event {row['EVENT_TYPE']} | Score {row['SCORE']}"
        )

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)

    st.download_button(
        "Download PDF",
        buffer,
        file_name=f"{country_selected}_report.pdf",
        mime="application/pdf"
    )
