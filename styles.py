import streamlit as st

def apply_styles():
    st.markdown("""
        <style>
        /* Fundo principal */
        .main { background-color: #0e1117; }
        
        /* Estilização das Métricas */
        [data-testid="stMetricValue"] { font-size: 24px; color: #00ffcc; }
        
        /* Ajustes das Abas (Tabs) */
        .stTabs [data-baseweb="tab-list"] { gap: 24px; }
        .stTabs [data-baseweb="tab"] { 
            height: 50px; 
            white-space: pre-wrap; 
            background-color: #161b22; 
            border-radius: 5px; 
            color: white; 
        }
        
        /* Cor da aba selecionada */
        .stTabs [aria-selected="true"] { border-bottom: 2px solid #00ffcc !important; }
        
        /* Melhoria na legibilidade de tabelas Streamlit */
        .stDataFrame { background-color: #161b22; border-radius: 10px; }
        </style>
    """, unsafe_allow_html=True)
