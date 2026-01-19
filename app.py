import streamlit as st
import pandas as pd
from views import scout, registro, historico, dashboard

st.set_page_config(page_title="Master Luciano - Banca", layout="wide")

# Carregamento seguro
def carregar_dados(file):
    df = pd.read_csv(file)
    df.columns = [c.strip() for c in df.columns] 
    return df

st.sidebar.title("🏆 Master Luciano")

# --- VOLTANDO COM A BANCA ---
banca_inicial = st.sidebar.number_input("Banca Inicial (R$)", value=1000.0)
arquivo = st.sidebar.file_uploader("Carregue a Base CSV", type=["csv"])

menu = st.sidebar.radio("Navegação", ["🔎 Scout", "📝 Registro", "📜 Histórico", "📊 Dashboard"])

if arquivo:
    df_csv = carregar_dados(arquivo)
    if menu == "🔎 Scout":
        scout.mostrar_scout(df_csv)
    elif menu == "📝 Registro":
        registro.mostrar_registro(df_csv)
    elif menu == "📜 Histórico":
        historico.mostrar_historico()
    elif menu == "📊 Dashboard":
        dashboard.mostrar_dashboard(banca_inicial) # Volta a banca aqui
else:
    st.info("Aguardando carregamento do CSV...")
