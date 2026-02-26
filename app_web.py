import streamlit as st
import pandas as pd
import os
import requests
from io import BytesIO
import time
# Importando as views da pasta views2 (Sistema 2)
from views2 import scout, simulador, tabelas
import styles

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Master Luciano - Sistema 2", layout="wide", page_icon="⚽")

# Aplicando estilos
try:
    styles.apply_styles()
except:
    pass

# --- FUNÇÃO DE CARREGAMENTO DE DADOS ---
@st.cache_data(ttl=60)
def carregar_dados_csv():
    url = f"https://github.com/lucianofmacedo2-ctrl/BancaMasterLuciano/raw/main/dados_25_26.csv?v={time.time()}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            df = pd.read_csv(BytesIO(response.content), low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            if 'Liga' in df.columns:
                df['Liga'] = df['Liga'].astype(str).str.strip().str.upper()
            return df
    except Exception:
        if os.path.exists('dados_25_26.csv'):
            return pd.read_csv('dados_25_26.csv', low_memory=False)
    return pd.DataFrame()

df_csv = carregar_dados_csv()

# --- SIDEBAR E NAVEGAÇÃO ---
st.sidebar.title("🏆 Master Luciano S2")

if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

# Lista de opções para o Sistema 2 (Somente as que já temos os arquivos prontos)
opcoes_menu = [
    "📈 Tabelas Dinâmicas", 
    "🔎 Scout Avançado", 
    "🎲 Simulador Poisson"
]

if 'menu_ativo_2' not in st.session_state:
    st.session_state.menu_ativo_2 = "📈 Tabelas Dinâmicas"

menu = st.sidebar.radio("Navegação", opcoes_menu, index=opcoes_menu.index(st.session_state.menu_ativo_2))
st.session_state.menu_ativo_2 = menu

# --- RENDERIZAÇÃO ---
if df_csv.empty:
    st.error("Erro ao carregar a base de dados.")
else:
    if st.session_state.menu_ativo_2 == "🔎 Scout Avançado":
        scout.mostrar_scout(df_csv)

    elif st.session_state.menu_ativo_2 == "🎲 Simulador Poisson":
        simulador.mostrar_simulador(df_csv)

    elif st.session_state.menu_ativo_2 == "📈 Tabelas Dinâmicas":
        tabelas.mostrar_tabelas(df_csv)
