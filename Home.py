import streamlit as st

st.set_page_config(
    page_title="Streamlit Games",
    page_icon="🎮",
    layout="centered"
)

st.title("🎮 Welcome to Streamlit Games")

st.markdown("""
            
Select a game from the sidebar to start playing!

This project demonstrates how to build interactive games using Streamlit.
""")

st.sidebar.success("Select a game above to start playing!")
