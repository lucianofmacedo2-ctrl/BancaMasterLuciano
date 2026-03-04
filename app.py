import streamlit as st
import pandas as pd
import os
import shutil
from datetime import datetime
import requests
from io import BytesIO
import time
# Adicionadas as importações h2h e termometro
from views import scout, registro, historico, dashboard, bancas, jogos, metas, backtest, ranking, simulador, h2h, termometro
import styles

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Master Luciano - Banca", layout="wide", page_icon="⚽")
styles.apply_styles()

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
st.sidebar.title("🏆 Master Luciano")
if st.sidebar.button("🔄 Atualizar Dados"):
    st.cache_data.clear()
    st.rerun()

# Lista de opções atualizada com as novas páginas
opcoes_menu = [
    "📊 Dashboard", 
    "📅 Jogos", 
    "🔎 Scout", 
    "⚔️ Confronto Direto", # Nova
    "🔥 Termômetro de Ligas", # Nova
    "🏆 Ranking", 
    "🎲 Simulador", 
    "🧪 Backtest", 
    "📝 Registro", 
    "📂 Histórico", 
    "🏦 Bancas", 
    "🎯 Metas"
]

if 'menu_ativo' not in st.session_state:
    st.session_state.menu_ativo = "📊 Dashboard"

menu = st.sidebar.radio("Navegação", opcoes_menu, index=opcoes_menu.index(st.session_state.menu_ativo))
st.session_state.menu_ativo = menu

# --- RENDERIZAÇÃO DAS PÁGINAS ---
if st.session_state.menu_ativo == "🔎 Scout":
    scout.mostrar_scout(df_csv)

elif st.session_state.menu_ativo == "⚔️ Confronto Direto":
    h2h.mostrar_h2h(df_csv)

elif st.session_state.menu_ativo == "🔥 Termômetro de Ligas":
    termometro.mostrar_termometro(df_csv)

elif st.session_state.menu_ativo == "🏆 Ranking":
    ranking.mostrar_ranking(df_csv)

elif st.session_state.menu_ativo == "🎲 Simulador":
    simulador.mostrar_simulador(df_csv)

elif st.session_state.menu_ativo == "📊 Dashboard":
    dashboard.mostrar_dashboard()

elif st.session_state.menu_ativo == "📅 Jogos":
    jogos.mostrar_jogos(df_csv) 

elif st.session_state.menu_ativo == "📝 Registro":
    registro.mostrar_registro(df_csv)

elif st.session_state.menu_ativo == "📂 Histórico":
    historico.mostrar_historico()

elif st.session_state.menu_ativo == "🏦 Bancas":
    bancas.mostrar_bancas()

elif st.session_state.menu_ativo == "🎯 Metas":
    metas.mostrar_metas()

elif st.session_state.menu_ativo == "🧪 Backtest":
    backtest.mostrar_backtest()
