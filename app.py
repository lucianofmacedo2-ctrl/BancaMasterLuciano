import streamlit as st
import pandas as pd
import os
import shutil
from datetime import datetime
from views import scout, registro, historico, dashboard, bancas, jogos
import styles

# --- FUNÇÃO DE BACKUP AUTOMÁTICO ---
def realizar_backup():
    pasta_data = "data"
    pasta_backup = "backups"
    if not os.path.exists(pasta_data): return
    if not os.path.exists(pasta_backup): os.makedirs(pasta_backup)
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    arquivo_zip = os.path.join(pasta_backup, f"backup_{data_hoje}")
    if not os.path.exists(arquivo_zip + ".zip"):
        try:
            shutil.make_archive(arquivo_zip, 'zip', pasta_data)
        except Exception as e:
            print(f"Erro no backup: {e}")

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

# --- LÓGICA DE NAVEGAÇÃO AUTOMÁTICA ---
opcoes_menu = ["📊 Dashboard", "📅 Jogos", "🔎 Scout", "📝 Registro", "📂 Histórico", "🏦 Bancas"]

# Inicializa a página ativa como Dashboard se não existir
if 'menu_ativo' not in st.session_state:
    st.session_state.menu_ativo = "📊 Dashboard"

# O radio agora é controlado pelo 'index' baseado na variável 'menu_ativo'
menu = st.sidebar.radio(
    "Navegação", 
    opcoes_menu, 
    index=opcoes_menu.index(st.session_state.menu_ativo)
)

# Sincroniza a variável caso o usuário clique manualmente no menu
st.session_state.menu_ativo = menu

if menu == "📊 Dashboard":
    dashboard.mostrar_dashboard() 

elif menu == "📅 Jogos":
    jogos.mostrar_jogos()

elif menu == "🔎 Scout":
    if not df_csv.empty:
        scout.mostrar_scout(df_csv)
    else:
        st.error("Arquivo 'dados_25_26.csv' não encontrado para o Scout.")

elif menu == "📝 Registro":
    registro.mostrar_registro(df_csv)

elif menu == "📂 Histórico":
    historico.mostrar_historico()

elif menu == "🏦 Bancas":
    bancas.mostrar_bancas()
