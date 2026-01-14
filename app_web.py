import streamlit as st
import pandas as pd
import gspread
import json
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Banca Master Luciano", layout="wide")

# --- FUNÇÃO: CONEXÃO COM GOOGLE SHEETS ---
def conectar_google_sheets():
    try:
        # Puxa o conteúdo bruto do segredo
        json_text = st.secrets["gcp_service_account"]["json_data"]
        
        # REMOÇÃO DE ESCAPE: Corrige o erro "Invalid \escape" limpando barras duplicadas
        # que o Streamlit ou editores de texto podem inserir automaticamente
        json_text = json_text.replace('\\\\', '\\')
        
        # Converte a string limpa para um dicionário Python
        creds_dict = json.loads(json_text)
        
        # Garante que as quebras de linha da chave privada sejam lidas corretamente pelo Google
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # Abre a planilha pelo nome exato (deve ser 'banca_dados' com aba 'apostas')
        return client.open("banca_dados").worksheet("apostas")
    except Exception as e:
        st.error(f"Erro Crítico de Conexão: {e}")
        return None

# --- CARREGAR DADOS DO CSV (PARA FILTROS DINÂMICOS) ---
@st.cache_data
def carregar_dados_csv():
    try:
        df = pd.read_csv("dados_25_26.csv", sep=None, engine='python')
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

df_csv = carregar_dados_csv()

# --- CSS: ALTO CONTRASTE ---
st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: #1a1c24 !important;
        border: 2px solid #3498db !important;
        padding: 20px !important;
        border-radius: 12px !important;
    }
    div[data-testid="metric-container"] label { color: #ffffff !important; font-weight: bold !important; }
    div[data-testid="metric-container"] [data-testid="stMetricValue"] { color: #3498db !important; font-weight: 900 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO LATERAL ---
st.sidebar.title("🏆 BancaMaster")
menu = st.sidebar.radio("Ir para:", ["🏠 Dashboard", "📝 Registrar Aposta"])

# --- TELA: DASHBOARD ---
if menu == "🏠 Dashboard":
    st.title("📊 Dashboard de Performance")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Lucro Total", "R$ 0,00")
    col2.metric("ROI", "0%")
    col3.metric("Win Rate", "0%")
    col4.metric("Banca Atual", "R$ 0,00")
    st.info("Os dados acima serão atualizados assim que você salvar a primeira aposta com sucesso.")

# --- TELA: REGISTRAR APOSTA (FORMULÁRIO COMPLETO) ---
elif menu == "📝 Registrar Aposta":
    st.title("🖊️ Registrar Nova Entrada")
    
    with st.form("form_aposta", clear_on_submit=True):
        col1, col2 = st.columns(2)
        data = col1.date_input("Data da Aposta")
        
        # Filtros automáticos baseados no seu arquivo CSV
        paises = sorted(df_csv['pais'].unique()) if not df_csv.empty else []
        pais = col2.selectbox("País", paises)
        
        ligas = sorted(df_csv[df_csv['pais'] == pais]['divisao'].unique()) if not df_csv.empty else []
        liga = col1.selectbox("Liga", ligas)
        
        times = sorted(df_csv[(df_csv['pais'] == pais) & (df_csv['divisao'] == liga)]['mandante'].unique()) if not df_csv.empty else []
        col_m, col_v = st.columns(2)
        mandante = col_m.selectbox("Mandante", times)
        visitante = col_v.selectbox("Visitante", [t for t in times if t != mandante])
        
        c3, c4, c5 = st.columns(3)
        mercado = c3.text_input("Mercado (Ex: Over 2.5)")
        odd = c4.number_input("Odd", min_value=1.01, step=0.01)
        stake = c5.number_input("Stake (R$)", min_value=1.0)
        
        resultado = st.selectbox("Resultado Final", ["Pendente", "Green", "Red", "Devolvida"])
        
        if st.form_submit_button("SALVAR APOSTA NA NUVEM", use_container_width=True):
            sheet = conectar_google_sheets()
            if sheet:
                try:
                    # Adiciona a nova linha na planilha do Google
                    sheet.append_row([
                        str(data), pais, liga, mandante, visitante, 
                        mercado, odd, stake, resultado
                    ])
                    st.success("✅ Aposta gravada com sucesso no Google Sheets!")
                except Exception as e:
                    st.error(f"Erro ao gravar dados: {e}")
