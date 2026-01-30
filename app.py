import streamlit as st
import pandas as pd
import os
import shutil
from datetime import datetime
import requests
from io import BytesIO
import time
from views import scout, registro, historico, dashboard, bancas, jogos, metas, backtest
import styles

# --- FUNÇÃO DE BACKUP ---
def realizar_backup():
    pasta_data = "data"
    pasta_backup = "backups"
    if not os.path.exists(pasta_data): return
    if not os.path.exists(pasta_backup): os.makedirs(pasta_backup)
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    arquivo_zip = os.path.join(pasta_backup, f"backup_{data_hoje}")
    if not os.path.exists(arquivo_zip + ".zip"):
        try: shutil.make_archive(arquivo_zip, 'zip', pasta_data)
        except Exception as e: print(f"Erro no backup: {e}")

realizar_backup()

st.set_page_config(page_title="Master Luciano - Banca", layout="wide", page_icon="⚽")
styles.apply_styles()

# --- CARREGAMENTO FORÇADO DO GITHUB (IGNORA ARQUIVO LOCAL ANTIGO) ---
def carregar_dados_csv():
    # URL RAW oficial do seu repositório
    url = f"https://github.com/lucianofmacedo2-ctrl/BancaMasterLuciano/raw/main/dados_25_26.csv?v={time.time()}"
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            # Lemos os dados brutos para garantir que nada seja pulado
            df = pd.read_csv(BytesIO(response.content), low_memory=False)
            df.columns = [c.strip() for c in df.columns]
            # Limpeza rigorosa para garantir que Portugal 3 e outras apareçam
            if 'Liga' in df.columns:
                df['Liga'] = df['Liga'].astype(str).str.strip().str.upper()
            return df
    except Exception as e:
        st.sidebar.error(f"Erro ao baixar do GitHub: {e}")
        # Só usa o local se o GitHub falhar totalmente
        if os.path.exists('dados_25_26.csv'):
            return pd.read_csv('dados_25_26.csv', low_memory=False)
    return pd.DataFrame()

df_csv = carregar_dados_csv()

st.sidebar.title("🏆 Master Luciano")

# Botão de pânico para limpar cache
if st.sidebar.button("🗑️ Limpar Cache e Atualizar Ligas"):
    st.cache_data.clear()
    st.rerun()

opcoes_menu = ["📊 Dashboard", "📅 Jogos", "🔎 Scout", "🧪 Backtest", "📝 Registro", "📂 Histórico", "🏦 Bancas", "🎯 Metas"]

if 'menu_ativo' not in st.session_state:
    st.session_state.menu_ativo = "📊 Dashboard"

index_atual = opcoes_menu.index(st.session_state.menu_ativo) if st.session_state.menu_ativo in opcoes_menu else 0
menu = st.sidebar.radio("Navegação", opcoes_menu, index=index_atual)

if menu != st.session_state.menu_ativo:
    st.session_state.menu_ativo = menu

# --- RENDERIZAÇÃO DAS PÁGINAS ---
if st.session_state.menu_ativo == "📊 Dashboard":
    dashboard.mostrar_dashboard() 
elif st.session_state.menu_ativo == "📅 Jogos":
    jogos.mostrar_jogos()
elif st.session_state.menu_ativo == "🔎 Scout":
    if not df_csv.empty:
        scout.mostrar_scout(df_csv)
    else:
        st.error("Não foi possível carregar as ligas do CSV.")
elif st.session_state.menu_ativo == "🧪 Backtest":
    backtest.mostrar_backtest()
elif st.session_state.menu_ativo == "📝 Registro":
    registro.mostrar_registro(df_csv)
elif st.session_state.menu_ativo == "📂 Histórico":
    historico.mostrar_historico()
elif st.session_state.menu_ativo == "🏦 Bancas":
    bancas.mostrar_bancas()
elif st.session_state.menu_ativo == "🎯 Metas":
    metas.mostrar_metas()
