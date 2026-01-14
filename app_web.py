import streamlit as st
import pandas as pd
import math
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="BancaMaster Pro Web", layout="wide", initial_sidebar_state="expanded")

# --- FUNÇÃO: CONEXÃO COM GOOGLE SHEETS (CORREÇÃO DE CHAVE) ---
def conectar_google_sheets():
    try:
        # Puxa os segredos e converte explicitamente para um dicionário editável
        creds_dict = st.secrets["gcp_service_account"].to_dict()
        
        # CORREÇÃO CRÍTICA: Garante que as quebras de linha da chave privada sejam lidas corretamente
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        client = gspread.authorize(creds)
        
        # Abre a planilha pelo nome exato
        return client.open("banca_dados").worksheet("apostas")
    except Exception as e:
        st.error(f"Erro na conexão com Google Sheets: {e}")
        return None

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

# --- MOTOR POISSON ---
class Engine:
    @staticmethod
    def poisson(k, lamb):
        if lamb <= 0: return 1 if k == 0 else 0
        return (math.exp(-lamb) * (lamb**k)) / math.factorial(k)

    @staticmethod
    def calcular_stats(df, time, local):
        df_t = df[df[local] == time].copy()
        if df_t.empty: return None
        p = "mandante" if local == "mandante" else "visitante"
        return {
            "gols": df_t[f'gols_{p}_ft'].mean(),
            "cantos": df_t[f'{p}_cantos'].mean(),
            "chutes": df_t[f'{p}_chute_ao_gol'].mean(),
            "cartoes": df_t[f'{p}_cartao_amarelo'].mean() + df_t[f'{p}_cartao_vermelho'].mean()
        }

# --- CARREGAR DADOS DO CSV ---
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv("dados_25_26.csv", sep=None, engine='python')
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

df_csv = carregar_dados()

# --- NAVEGAÇÃO LATERAL ---
st.sidebar.title("🏆 BancaMaster Pro")
menu = st.sidebar.radio("Ir para:", ["🏠 Dashboard", "⚽ Análise Preditiva", "📝 Registrar Aposta"])

# --- TELA: DASHBOARD ---
if menu == "🏠 Dashboard":
    st.title("📊 Dashboard de Performance")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Lucro Total", "R$ 0,00")
    col2.metric("ROI", "0%")
    col3.metric("Win Rate", "0%")
    col4.metric("Banca Atual", "R$ 0,00")
    st.info("O dashboard exibirá dados reais assim que você registrar as primeiras apostas.")

# --- TELA: REGISTRAR APOSTA ---
elif menu == "📝 Registrar Aposta":
    st.title("🖊️ Registrar Nova Aposta")
    
    with st.form("form_aposta", clear_on_submit=True):
        col_data, col_pais = st.columns(2)
        data_aposta = col_data.date_input("Data da Aposta")
        
        paises_lista = sorted(df_csv['pais'].unique()) if not df_csv.empty else []
        pais_sel = col_pais.selectbox("País", paises_lista)
        
        ligas_lista = sorted(df_csv[df_csv['pais'] == pais_sel]['divisao'].unique()) if not df_csv.empty else []
        liga_sel = st.selectbox("Liga", ligas_lista)
        
        times_lista = sorted(df_csv[(df_csv['pais'] == pais_sel) & (df_csv['divisao'] == liga_sel)]['mandante'].unique()) if not df_csv.empty else []
        col_m, col_v = st.columns(2)
        mandante_sel = col_m.selectbox("Mandante", times_lista)
        visitante_sel = col_v.selectbox("Visitante", [t for t in times_lista if t != mandante_sel])
        
        col_mer, col_odd, col_stk = st.columns(3)
        mercado = col_mer.text_input("Mercado")
        odd = col_odd.number_input("Odd", min_value=1.01, step=0.01)
        stake = col_stk.number_input("Stake (R$)", min_value=1.0)
        
        resultado = st.selectbox("Resultado Final", ["Pendente", "Green", "Red", "Devolvida"])
        
        if st.form_submit_button("SALVAR APOSTA NA NUVEM", use_container_width=True):
            sheet = conectar_google_sheets()
            if sheet:
                try:
                    sheet.append_row([
                        str(data_aposta), pais_sel, liga_sel, mandante_sel, 
                        visitante_sel, mercado, odd, stake, resultado
                    ])
                    st.success("✅ Aposta salva com sucesso no Google Sheets!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
