import streamlit as st
import pandas as pd
from views import scout, registro, historico, dashboard

st.set_page_config(page_title="Banca Master Luciano", layout="wide")

# Função para normalizar colunas (resolve o erro de KeyError)
def carregar_dados(file):
    df = pd.read_csv(file)
    df.columns = [c.strip() for c in df.columns] # Remove espaços extras
    return df

st.sidebar.title("🏆 Master Luciano")
arquivo = st.sidebar.file_uploader("Carregue o CSV da Base", type=["csv"])

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
        dashboard.mostrar_dashboard()
else:
    st.info("Por favor, carregue o arquivo CSV na barra lateral para começar.")
