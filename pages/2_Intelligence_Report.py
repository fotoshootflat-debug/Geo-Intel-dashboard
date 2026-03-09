import streamlit as st
import pandas as pd
import os

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

# -----------------------------
# CLEAN DATA
# -----------------------------
if "COUNTRY" not in df.columns:
    st.error("Country column missing in dataset.")
    st.stop()

countries = sorted(df["COUNTRY"].dropna().unique())

country_selected = st.selectbox("Select Country", countries)

if "EVENT_TYPE" in df.columns:
    event_types = df["EVENT_TYPE"].dropna().unique()
    event_selected = st.selectbox("Select Event Type", event_types)
else:
    event_selected = None

# -----------------------------
# FILTER DATA
# -----------------------------
filtered_df = df[df["COUNTRY"] == country_selected]

if event_selected:
    filtered_df = filtered_df[filtered_df["EVENT_TYPE"] == event_selected]

# -----------------------------
# GENERATE REPORT
# -----------------------------
if st.button("Generate Intelligence Report"):

    total_events = len(filtered_df)

    if "FATALITIES" in filtered_df.columns:
        fatalities = filtered_df["FATALITIES"].sum()
    else:
        fatalities = 0

    report = f"""
### Intelligence Report

**Country:** {country_selected}

**Event Type:** {event_selected}

**Total Events:** {total_events}

**Total Fatalities:** {fatalities}

### Assessment

Recent data indicates ongoing **{event_selected}** activity in **{country_selected}**.

The dataset records **{total_events} events**, with **{fatalities} fatalities** reported.

Further monitoring is recommended to identify escalation patterns, actor involvement, and geographic clustering of incidents.
"""

    st.markdown(report)
