import streamlit as st
import pandas as pd
from supabase import create_client

@st.cache_resource
def conectar():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

@st.cache_data
def carregar_csv():
    try:
        df = pd.read_csv("dados_25_26.csv", sep=None, engine='python')
        df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
        return df
    except: return pd.DataFrame()

supabase = conectar()
