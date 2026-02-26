import streamlit as st
import pandas as pd
import os
import requests
from io import BytesIO
import time

# Importação organizada
try:
    from views2 import (
        dashboard, jogos, scout, ranking, simulador, 
        backtest, registro, historico, bancas, metas, tabelas
    )
except ImportError as e:
    st.error(f"Erro ao carregar módulos da pasta views2: {e}")
    st.stop()

import styles

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Master Luciano - S2", layout="wide", page_icon="⚽")

try:
    styles.apply_styles()
except:
    pass

@st.cache_data(ttl=60)
def carregar_dados_csv():
    url = f"https://github.com/lucianofmacedo2-ctrl/BancaMasterLuciano/raw/main/dados_25_26.csv?v={time.time()}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            df = pd.read_csv(BytesIO(response.content), low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            return df
    except:
        if os.path.exists('dados_25_26.csv'):
            return pd.read_csv('dados_25_26.csv', low_memory=False)
    return pd.DataFrame()

df_csv = carregar_dados_csv()

# --- MENU LATERAL ---
st.sidebar.title("🏆 Master Luciano S2")

opcoes_menu = [
    "📊 Dashboard", "📅 Jogos", "🔎 Scout", "🏆 Ranking", 
    "🎲 Simulador", "🧪 Backtest", "📝 Registro", 
    "📂 Histórico", "🏢 Bancas", "🎯 Metas", "📈 Tabelas S2"
]

if 'menu_ativo_2' not in st.session_state:
    st.session_state.menu_ativo_2 = "📊 Dashboard"

menu = st.sidebar.radio("Navegação", opcoes_menu, index=opcoes_menu.index(st.session_state.menu_ativo_2))
st.session_state.menu_ativo_2 = menu

# --- RENDERIZAÇÃO ---
if not df_csv.empty:
    m = st.session_state.menu_ativo_2
    if m == "📊 Dashboard": dashboard.mostrar_dashboard()
    elif m == "📅 Jogos": jogos.mostrar_jogos(df_csv)
    elif m == "🔎 Scout": scout.mostrar_scout(df_csv)
    elif m == "🏆 Ranking": ranking.mostrar_ranking(df_csv)
    elif m == "🎲 Simulador": simulador.mostrar_simulador(df_csv)
    elif m == "🧪 Backtest": backtest.mostrar_backtest()
    elif m == "📝 Registro": registro.mostrar_registro(df_csv)
    elif m == "📂 Histórico": historico.mostrar_historico()
    elif m == "🏢 Bancas": bancas.mostrar_bancas()
    elif m == "🎯 Metas": metas.mostrar_metas()
    elif m == "📈 Tabelas S2": tabelas.mostrar_tabelas(df_csv)
