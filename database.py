import streamlit as st
import pandas as pd
from supabase import create_client

@st.cache_resource
def conectar():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = conectar()

@st.cache_data
def carregar_csv():
    try:
        df = pd.read_csv("dados_25_26.csv", sep=None, engine='python')
        df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
        return df
    except: return pd.DataFrame()

def carregar_bancas():
    res = supabase.table("bancas").select("*").execute()
    return pd.DataFrame(res.data)

def carregar_apostas():
    res = supabase.table("apostas").select("*").execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        df['data'] = pd.to_datetime(df['data']).dt.date
    return df

def calcular_lucro_real(resultado, odd, stake):
    res = str(resultado).lower()
    if 'green' in res and 'meio' not in res: return (stake * odd) - stake
    if 'meio green' in res: return ((stake * odd) - stake) / 2
    if 'red' in res and 'meio' not in res: return -stake
    if 'meio red' in res: return -stake / 2
    return 0.0