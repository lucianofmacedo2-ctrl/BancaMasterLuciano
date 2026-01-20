import streamlit as st
from styles import aplicar_estilos
from database import carregar_csv
from views import scout, dashboard, registro, historico, bancas # Importando os módulos

# 1. Configurações iniciais
st.set_page_config(page_title="Banca Master Pro", layout="wide")
aplicar_estilos()
df_csv = carregar_csv()

# 2. Navegação Lateral
st.sidebar.title("🚀 Navegação")
menu = st.sidebar.radio("Ir para:", [
    "📊 Dashboard", 
    "⚽ Análise Scout", 
    "📝 Nova Aposta", 
    "📂 Histórico", 
    "🏦 Gestão de Bancas"
])

# 3. Chamar a página correspondente
if menu == "📊 Dashboard":
    # dashboard.mostrar_dashboard()
    st.write("Em desenvolvimento...")
elif menu == "⚽ Análise Scout":
    scout.mostrar_scout(df_csv)
elif menu == "📝 Nova Aposta":
    # registro.mostrar_formulario()
    st.write("Em desenvolvimento...")
# ... e assim por diante
