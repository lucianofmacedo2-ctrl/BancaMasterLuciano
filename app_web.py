import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Banca Luciano Web", layout="wide")

def conectar_google_sheets():
    try:
        # Puxa a string JSON inteira dos secrets
        json_str = st.secrets["gcp_service_account"]["content"]
        creds_dict = json.loads(json_str)
        
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        return client.open("banca_dados").worksheet("apostas")
    except Exception as e:
        st.error(f"Erro Crítico de Conexão: {e}")
        return None

# --- CARREGAR DADOS CSV ---
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv("dados_25_26.csv", sep=None, engine='python')
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df
    except: return pd.DataFrame()

df_csv = carregar_dados()

# --- CSS ALTO CONTRASTE ---
st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: #1a1c24 !important;
        border: 2px solid #3498db !important;
        padding: 20px !important;
        border-radius: 12px !important;
    }
    div[data-testid="metric-container"] label { color: white !important; font-weight: bold !important; }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #3498db !important; font-weight: 900 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO ---
menu = st.sidebar.radio("Navegação", ["🏠 Dashboard", "📝 Registrar Aposta"])

if menu == "📝 Registrar Aposta":
    st.title("🖊️ Registrar Nova Aposta")
    
    with st.form("form_aposta", clear_on_submit=True):
        col1, col2 = st.columns(2)
        data = col1.date_input("Data da Aposta")
        
        # Filtros baseados no seu CSV
        paises = sorted(df_csv['pais'].unique()) if not df_csv.empty else []
        pais = col2.selectbox("País", paises)
        
        ligas = sorted(df_csv[df_csv['pais'] == pais]['divisao'].unique()) if not df_csv.empty else []
        liga = col1.selectbox("Liga", ligas)
        
        times = sorted(df_csv[(df_csv['pais'] == pais) & (df_csv['divisao'] == liga)]['mandante'].unique()) if not df_csv.empty else []
        mandante = col2.selectbox("Mandante", times)
        visitante = col1.selectbox("Visitante", [t for t in times if t != mandante])
        
        c3, c4, c5 = st.columns(3)
        mercado = c3.text_input("Mercado (Ex: Over 2.5)")
        odd = c4.number_input("Odd", min_value=1.01, step=0.01)
        stake = c5.number_input("Stake (R$)", min_value=1.0)
        
        resultado = st.selectbox("Resultado Final", ["Pendente", "Green", "Red", "Devolvida"])
        
        if st.form_submit_button("SALVAR APOSTA NA NUVEM", use_container_width=True):
            sheet = conectar_google_sheets()
            if sheet:
                try:
                    sheet.append_row([
                        str(data), pais, liga, mandante, visitante, 
                        mercado, odd, stake, resultado
                    ])
                    st.success("✅ Aposta gravada com sucesso na planilha!")
                except Exception as e:
                    st.error(f"Erro ao gravar na planilha: {e}")

elif menu == "🏠 Dashboard":
    st.title("📊 Dashboard")
    st.info("Aqui aparecerão as estatísticas assim que você salvar os dados.")
