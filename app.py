import streamlit as st
from styles import aplicar_estilos
from database import carregar_csv
from views import scout, dashboard, registro, historico, bancas

st.set_page_config(page_title="Banca Master Pro", layout="wide")
aplicar_estilos()
df_csv = carregar_csv()

# Menu lateral com cor #030844
st.sidebar.title("🚀 Banca Master")
menu = st.sidebar.radio("Navegação", [
    "📊 Dashboard", "⚽ Scout", "📝 Registro", "📂 Histórico", "🏦 Bancas"
])

if menu == "📊 Dashboard": dashboard.mostrar_dashboard()
elif menu == "⚽ Scout": scout.mostrar_scout(df_csv)
elif menu == "📝 Registro": registro.mostrar_registro(df_csv)
elif menu == "📂 Histórico": historico.mostrar_historico()
elif menu == "🏦 Bancas": bancas.mostrar_bancas()