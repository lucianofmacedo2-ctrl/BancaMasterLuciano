import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="BancaMaster Pro Web", layout="wide")

def conectar_google_sheets():
    try:
        # Puxa o dicionário dos secrets
        creds_dict = st.secrets["gcp_service_account"].to_dict()
        
        # LIMPEZA DA CHAVE: Remove quebras de linha extras e espaços
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].strip().replace("\\n", "\n")
        
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # Certifique-se que o nome da planilha está correto
        return client.open("banca_dados").worksheet("apostas")
    except Exception as e:
        st.error(f"Erro de Conexão: {e}")
        return None

# --- CSS ALTO CONTRASTE ---
st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: #1a1c24 !important;
        border: 2px solid #3498db !important;
        padding: 20px !important;
        border-radius: 12px !important;
    }
    div[data-testid="metric-container"] label { color: white !important; }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #3498db !important; }
    </style>
    """, unsafe_allow_html=True)

# --- MENU ---
menu = st.sidebar.radio("Navegação", ["🏠 Dashboard", "📝 Registrar Aposta"])

if menu == "📝 Registrar Aposta":
    st.title("📝 Nova Aposta")
    
    with st.form("form_aposta", clear_on_submit=True):
        col1, col2 = st.columns(2)
        data = col1.date_input("Data")
        mercado = col2.text_input("Mercado")
        
        c3, c4 = st.columns(2)
        odd = c3.number_input("Odd", min_value=1.01, step=0.01)
        stake = c4.number_input("Stake (R$)", min_value=1.0)
        
        resultado = st.selectbox("Resultado", ["Pendente", "Green", "Red", "Devolvida"])
        
        if st.form_submit_button("SALVAR NA NUVEM"):
            sheet = conectar_google_sheets()
            if sheet:
                # Usando o cabeçalho simplificado que você pediu inicialmente
                sheet.append_row([str(data), "Evento", mercado, stake, odd, resultado])
                st.success("✅ Salvo com sucesso!")

elif menu == "🏠 Dashboard":
    st.title("📊 Performance")
    col1, col2 = st.columns(2)
    col1.metric("Lucro", "R$ 0,00")
    col2.metric("ROI", "0%")
