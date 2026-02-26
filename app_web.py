import streamlit as st
import pandas as pd
import os
import requests
from io import BytesIO
import time
import styles

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Master Luciano - Sistema 2", layout="wide", page_icon="⚽")

try:
    styles.apply_styles()
except:
    pass

# --- NAVEGAÇÃO (IDÊNTICA À SUA IMAGEM) ---
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

# --- CARREGAMENTO DE DADOS ---
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
        return pd.DataFrame()

df_csv = carregar_dados_csv()

# --- IMPORTAÇÃO SOB DEMANDA (Evita o SyntaxError global) ---
if not df_csv.empty:
    try:
        if menu == "📊 Dashboard":
            from views2 import dashboard
            dashboard.mostrar_dashboard()
        elif menu == "📅 Jogos":
            from views2 import jogos
            jogos.mostrar_jogos(df_csv)
        elif menu == "🔎 Scout":
            from views2 import scout
            scout.mostrar_scout(df_csv)
        elif menu == "🏆 Ranking":
            from views2 import ranking
            ranking.mostrar_ranking(df_csv)
        elif menu == "🎲 Simulador":
            from views2 import simulador
            simulador.mostrar_simulador(df_csv)
        elif menu == "🧪 Backtest":
            from views2 import backtest
            backtest.mostrar_backtest()
        elif menu == "📝 Registro":
            from views2 import registro
            registro.mostrar_registro(df_csv)
        elif menu == "📂 Histórico":
            from views2 import historico
            historico.mostrar_historico()
        elif menu == "🏢 Bancas":
            from views2 import bancas
            bancas.mostrar_bancas()
        elif menu == "🎯 Metas":
            from views2 import metas
            metas.mostrar_metas()
        elif menu == "📈 Tabelas S2":
            from views2 import tabelas
            tabelas.mostrar_tabelas(df_csv)
    except Exception as e:
        st.error(f"Erro ao carregar a página {menu}: {e}")
