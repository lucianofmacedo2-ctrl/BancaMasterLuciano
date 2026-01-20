import streamlit as st
import pandas as pd
from views import scout, registro, historico, dashboard, bancas
import styles

st.set_page_config(page_title="Banca Master", layout="wide", page_icon="⚽")

# Aplica o estilo visual customizado
styles.apply_styles()

def carregar_dados():
    try:
        df = pd.read_csv('dados_25_26.csv')
        # Normaliza nomes de colunas: remove espaços e garante padrão
        df.columns = [c.strip() for c in df.columns]
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados_25_26.csv: {e}")
        return pd.DataFrame()

df_csv = carregar_dados()

st.sidebar.image("https://cdn-icons-png.flaticon.com/512/5329/5329304.png", width=100)
st.sidebar.title("Banca Master")

menu = st.sidebar.radio(
    "Navegação",
    ["📊 Dashboard", "⚽ Scout", "📝 Registro", "📂 Histórico", "🏦 Bancas"]
)

if not df_csv.empty:
    if menu == "📊 Dashboard":
        dashboard.mostrar_dashboard()
    elif menu == "⚽ Scout":
        scout.mostrar_scout(df_csv)
    elif menu == "📝 Registro":
        registro.mostrar_registro(df_csv)
    elif menu == "📂 Histórico":
        historico.mostrar_historico()
    elif menu == "🏦 Bancas":
        bancas.mostrar_bancas()
else:
    st.warning("Arquivo de dados não encontrado ou vazio.")
