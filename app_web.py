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
st.set_page_config(page_title="Master Luciano - Sistema 2", layout="wide", page_icon="🧪")

# Aplicando estilos (reutilizando o styles.py da raiz)
try:
    styles.apply_styles()
except:
    pass

# --- FUNÇÃO DE CARREGAMENTO DE DADOS (Mesma base do Sistema 1) ---
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

# --- SIDEBAR E NAVEGAÇÃO DO SISTEMA 2 ---
st.sidebar.title("🧪 Sistema de Análise 2")
st.sidebar.markdown("---")

if st.sidebar.button("🔄 Atualizar Base de Dados"):
    st.cache_data.clear()
    st.rerun()

# Menu específico do Sistema 2
opcoes_menu_2 = [
    "📈 Tabelas Dinâmicas",
    "🔎 Scout Avançado",
    "🎲 Simulador Poisson"
]

if 'menu_ativo_2' not in st.session_state:
    st.session_state.menu_ativo_2 = "📈 Tabelas Dinâmicas"

menu = st.sidebar.radio("Navegação S2", opcoes_menu_2, index=opcoes_menu_2.index(st.session_state.menu_ativo_2))
st.session_state.menu_ativo_2 = menu

# --- RENDERIZAÇÃO DAS PÁGINAS DO SISTEMA 2 ---
if df_csv.empty:
    st.error("Erro ao carregar a base de dados. Verifique a conexão ou o arquivo CSV.")
else:
    if st.session_state.menu_ativo_2 == "🔎 Scout Avançado":
        scout.mostrar_scout(df_csv)

    elif st.session_state.menu_ativo_2 == "🎲 Simulador Poisson":
        simulador.mostrar_simulador(df_csv)

    elif st.session_state.menu_ativo_2 == "📈 Tabelas Dinâmicas":
        tabelas.mostrar_tabelas(df_csv)

# Rodapé lateral para diferenciar os sistemas
st.sidebar.markdown("---")
st.sidebar.caption("Modo: Sistema 2 (Independente)")
