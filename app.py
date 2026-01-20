import streamlit as st
import pandas as pd
from views import scout, registro, historico, dashboard, bancas
import styles

st.set_page_config(page_title="Master Luciano - Banca", layout="wide", page_icon="⚽")

# Aplica o visual profissional
styles.apply_styles()

def carregar_dados():
    try:
        df = pd.read_csv('dados_25_26.csv')
        df.columns = [c.strip() for c in df.columns] # Remove espaços extras das colunas
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
        return pd.DataFrame()

df_csv = carregar_dados()

st.sidebar.title("🏆 Master Luciano")
# Recupera a banca configurada
banca_inicial = st.sidebar.number_input("Banca Inicial (R$)", value=1000.0, step=50.0)

menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "🔎 Scout", "📝 Registro", "📂 Histórico", "🏦 Bancas"])

if not df_csv.empty:
    if menu == "📊 Dashboard":
        dashboard.mostrar_dashboard(banca_inicial)
    elif menu == "🔎 Scout":
        scout.mostrar_scout(df_csv)
    elif menu == "📝 Registro":
        registro.mostrar_registro(df_csv)
    elif menu == "📂 Histórico":
        historico.mostrar_historico()
    elif menu == "🏦 Bancas":
        bancas.mostrar_bancas()
