import streamlit as st
import pandas as pd
from views import scout, registro, historico, dashboard

st.set_page_config(page_title="Banca Master Luciano", layout="wide", page_icon="⚽")

# Estilização para manter o padrão profissional
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #161b22; padding: 15px; border-radius: 10px; border: 1px solid #30363d; }
    </style>
    """, unsafe_allow_html=True)

def carregar_dados(file):
    df = pd.read_csv(file)
    df.columns = [c.strip() for c in df.columns] # Limpa espaços
    return df

st.sidebar.title("🏆 Master Luciano v2.0")
banca_inicial = st.sidebar.number_input("Minha Banca (R$)", value=1000.0, step=50.0)
arquivo = st.sidebar.file_uploader("📂 Base de Dados (CSV)", type=["csv"])

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
        dashboard.mostrar_dashboard(banca_inicial)
else:
    st.info("🚀 Carregue seu arquivo CSV para começar a análise.")
