import streamlit as st

st.title("🔎 Geopolitical Search Engine")

query = st.text_input("Search country or event")

if query:
    st.write("Results for:", query)
