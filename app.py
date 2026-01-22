import streamlit as st
import pandas as pd
import os
import shutil
from datetime import datetime
from views import scout, registro, historico, dashboard, bancas, jogos
import styles

# --- FUNÇÃO DE BACKUP (MANTIDA) ---
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

def carregar_dados_csv():
    try:
        df = pd.read_csv('dados_25_26.csv')
        df.columns = [c.strip() for c in df.columns] 
        return df
    except Exception as e:
        return pd.DataFrame()

df_csv = carregar_dados_csv()

st.sidebar.title("🏆 Master Luciano")

# --- LÓGICA DE NAVEGAÇÃO REFORÇADA ---
opcoes_menu = ["📊 Dashboard", "📅 Jogos", "🔎 Scout", "📝 Registro", "📂 Histórico", "🏦 Bancas"]

# Inicializa se for a primeira vez
if 'menu_ativo' not in st.session_state:
    st.session_state.menu_ativo = "📊 Dashboard"

# Encontra a posição da página atual na lista
index_atual = opcoes_menu.index(st.session_state.menu_ativo)

# O segredo: usamos o parâmetro 'index' para forçar a posição
menu = st.sidebar.radio(
    "Navegação", 
    opcoes_menu, 
    index=index_atual
)

# Se o usuário clicar manualmente, atualizamos a variável
if menu != st.session_state.menu_ativo:
    st.session_state.menu_ativo = menu

# --- RENDERIZAÇÃO ---
if st.session_state.menu_ativo == "📊 Dashboard":
    dashboard.mostrar_dashboard() 
elif st.session_state.menu_ativo == "📅 Jogos":
    jogos.mostrar_jogos()
elif st.session_state.menu_ativo == "🔎 Scout":
    if not df_csv.empty:
        scout.mostrar_scout(df_csv)
    else:
        st.error("Arquivo 'dados_25_26.csv' não encontrado.")
elif st.session_state.menu_ativo == "📝 Registro":
    registro.mostrar_registro(df_csv)
elif st.session_state.menu_ativo == "📂 Histórico":
    historico.mostrar_historico()
elif st.session_state.menu_ativo == "🏦 Bancas":
    bancas.mostrar_bancas()
