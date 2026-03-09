# 2_Intelligence_Report.py
import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
from io import BytesIO
from fpdf import FPDF

st.set_page_config(page_title="Intelligence Report Generator", layout="wide")
st.title("🧠 Intelligence Report Generator")

# -----------------------------
# LOAD DATA
# -----------------------------
data_path = "data"

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

df = pd.concat([africa_df, asia_df, europe_df, latin_df, us_df], ignore_index=True)

if "COUNTRY" not in df.columns:
    st.error("Country column missing in dataset.")
    st.stop()

countries = sorted(df["COUNTRY"].dropna().unique())
country_selected = st.selectbox("Select Country", countries)

event_selected = None
if "EVENT_TYPE" in df.columns:
    event_types = df["EVENT_TYPE"].dropna().unique()
    event_selected = st.selectbox("Select Event Type", event_types)

# -----------------------------
# FILTER DATA
# -----------------------------
filtered_df = df[df["COUNTRY"] == country_selected]
if event_selected:
    filtered_df = filtered_df[filtered_df["EVENT_TYPE"] == event_selected]

# -----------------------------
# METRICS
# -----------------------------
total_events = len(filtered_df)
fatalities = filtered_df.get("FATALITIES", pd.Series([0]*len(filtered_df))).sum()

st.subheader("Metrics")
col1, col2 = st.columns(2)
col1.metric("Total Events", total_events)
col2.metric("Total Fatalities", fatalities)

# -----------------------------
# EVENT TREND CHART (LAST 30 DAYS)
# -----------------------------
if "DATE" in filtered_df.columns:
    filtered_df["DATE"] = pd.to_datetime(filtered_df["DATE"], errors="coerce")
    recent_df = filtered_df[filtered_df["DATE"] >= (pd.Timestamp.today() - pd.Timedelta(days=30))]
    trend = recent_df.groupby("DATE").size()
    
    fig, ax = plt.subplots(figsize=(8,3))
    trend.plot(ax=ax, color="red")
    ax.set_title(f"Events Trend (Last 30 days) for {country_selected}")
    ax.set_ylabel("Number of Events")
    ax.set_xlabel("Date")
    st.pyplot(fig)
else:
    st.info("No date column available to plot trends.")

# -----------------------------
# GENERATE PDF REPORT
# -----------------------------
if st.button("Generate PDF Report"):

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Intelligence Report — {country_selected}", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 8, f"Event Type: {event_selected}")
    pdf.multi_cell(0, 8, f"Total Events: {total_events}")
    pdf.multi_cell(0, 8, f"Total Fatalities: {fatalities}")
    pdf.ln(5)
    pdf.multi_cell(0, 8, "Assessment:")
    pdf.multi_cell(0, 8, f"Recent data indicates ongoing {event_selected} activity in {country_selected}.")

    # Add trend chart to PDF
    if "DATE" in filtered_df.columns:
        img_buffer = BytesIO()
        fig.savefig(img_buffer, format='png')
        img_buffer.seek(0)
        pdf.image(img_buffer, x=10, y=pdf.get_y(), w=180)
    
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    st.download_button(
        label="Download PDF",
        data=pdf_output,
        file_name=f"{country_selected}_{event_selected}_Report.pdf",
        mime="application/pdf"
    )
