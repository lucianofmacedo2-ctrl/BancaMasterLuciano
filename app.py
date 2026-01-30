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

st.sidebar.title("🏆 Master Luciano")

opcoes_menu = ["📊 Dashboard", "📅 Jogos", "🔎 Scout", "🧪 Backtest", "📝 Registro", "📂 Histórico", "🏦 Bancas", "🎯 Metas"]

if 'menu_ativo' not in st.session_state:
    st.session_state.menu_ativo = "📊 Dashboard"

menu = st.sidebar.radio("Navegação", opcoes_menu, index=opcoes_menu.index(st.session_state.menu_ativo))
st.session_state.menu_ativo = menu

if st.session_state.menu_ativo == "🔎 Scout":
    scout.mostrar_scout(df_csv)
elif st.session_state.menu_ativo == "📊 Dashboard":
    dashboard.mostrar_dashboard()
# ... (demais elifs mantidos conforme seu app.py original)
