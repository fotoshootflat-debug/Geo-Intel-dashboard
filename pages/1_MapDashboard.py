import streamlit as st
import pandas as pd

st.title("🗺️ Intelligence Map")

st.write("This map will display global intelligence data.")

data = pd.DataFrame({
    "lat": [34.0, 40.7, 48.8],
    "lon": [-6.0, -74.0, 2.3]
})

st.map(data)
