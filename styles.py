import streamlit as st

def aplicar_estilos():
    st.markdown("""
    <style>
    /* FUNDO PRINCIPAL */
    .stApp { background-color: #0b5754 !important; color: #ffffff !important; }
    
    /* MENU LATERAL */
    [data-testid="stSidebar"] { background-color: #030844 !important; border-right: 1px solid #ffffff33; }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] h1 {
        color: #ffffff !important; font-weight: 600 !important;
    }

    /* CARDS E MÉTRICAS */
    div[data-testid="stMetric"] { background-color: #050f54 !important; border: 1px solid #ffffff33 !important; border-radius: 12px !important; }
    div[data-testid="stMetricValue"] > div { color: #ffffff !important; }
    div[data-testid="stMetricLabel"] > div > p { color: #ffffff !important; }

    /* INPUTS E SELEÇÃO (Fundo Branco, Texto Preto) */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #ffffff !important; color: #000000 !important;
    }
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div { color: #000000 !important; }

    /* TABELAS COM FONTE BRANCA (CONTRASTE TOTAL) */
    div[data-testid="stTable"] table { color: #ffffff !important; }
    div[data-testid="stTable"] td, div[data-testid="stTable"] th { color: #ffffff !important; border-bottom: 1px solid #ffffff22 !important; }
    </style>
    """, unsafe_allow_html=True)