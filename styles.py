import streamlit as st

def apply_styles():
    st.markdown("""
        <style>
        .main { background-color: #0e1117; }
        [data-testid="stMetricValue"] { font-size: 24px; color: #00ffcc; }
        .stTabs [data-baseweb="tab-list"] { gap: 24px; }
        .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #161b22; border-radius: 5px; color: white; }
        .stTabs [aria-selected="true"] { border-bottom: 2px solid #00ffcc !important; }
        </style>
    """, unsafe_allow_html=True)
