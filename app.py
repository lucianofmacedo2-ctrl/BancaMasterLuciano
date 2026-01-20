import streamlit as st
import pandas as pd
import os
import shutil
from datetime import datetime
from views import scout, registro, historico, dashboard, bancas
import styles

# --- FUNÇÃO DE BACKUP AUTOMÁTICO ---
def realizar_backup():
    pasta_data = "data"
    pasta_backup = "backups"
    if not os.path.exists(pasta_data): return
    if not os.path.exists(pasta_backup): os.makedirs(pasta_backup)
    
    hoje = datetime.now().strftime("%Y-%m-%d")
    nome_zip = os.path.join(pasta_backup, f"backup_{hoje}")
    
    if not os.path.exists(nome_zip + ".zip"):
        try:
            shutil.make_archive(nome_zip, 'zip', pasta_data)
        except: pass

# Executa o backup ao iniciar
realizar_backup()

st.set_page_config(page_title="Master Luciano - Banca", layout="wide", page_icon="⚽")
styles.apply_styles()

def carregar_dados():
    try:
        df = pd.read_csv('dados_25_26.csv')
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
        return pd.DataFrame()

df_csv = carregar_dados()

st.sidebar.title("🏆 Master Luciano")
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "🔎 Scout", "📝 Registro", "📂 Histórico", "🏦 Bancas"])

if not df_csv.empty:
    if menu == "📊 Dashboard":
        dashboard.mostrar_dashboard() 
    elif menu == "🔎 Scout":
        scout.mostrar_scout(df_csv)
    elif menu == "📝 Registro":
        registro.mostrar_registro(df_csv)
    elif menu == "📂 Histórico":
        historico.mostrar_historico()
    elif menu == "🏦 Bancas":
        bancas.mostrar_bancas()
