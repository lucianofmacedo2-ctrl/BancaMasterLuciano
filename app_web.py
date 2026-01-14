import streamlit as st
import pandas as pd
import math
import gspread
from google.oauth2.service_account import Credentials

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="BancaMaster Pro Web", layout="wide", initial_sidebar_state="expanded")

# --- FUNÇÃO: CONEXÃO COM GOOGLE SHEETS ---
def conectar_google_sheets():
    try:
        # Puxa as credenciais formatadas como TOML dos Secrets do Streamlit
        creds_info = st.secrets["gcp_service_account"]
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        # Tenta abrir a planilha 'banca_dados' na aba 'apostas'
        return client.open("banca_dados").worksheet("apostas")
    except Exception as e:
        st.error(f"Erro na conexão com Google Sheets: {e}")
        return None

# --- CSS: ALTO CONTRASTE (FIXO PARA MODO CLARO E ESCURO) ---
st.markdown("""
    <style>
    /* Estilização dos Cards de Métrica */
    div[data-testid="metric-container"] {
        background-color: #1a1c24 !important; /* Fundo escuro fixo */
        border: 2px solid #3498db !important; /* Borda azul vibrante */
        padding: 20px !important;
        border-radius: 12px !important;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.5) !important;
    }
    /* Título da métrica em Branco */
    div[data-testid="metric-container"] label {
        color: #ffffff !important;
        font-weight: bold !important;
        font-size: 16px !important;
    }
    /* Valor numérico em Azul Claro */
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #3498db !important;
        font-weight: 900 !important;
        font-size: 28px !important;
    }
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
    
    # Cards com alto contraste
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Lucro Total", "R$ 1.250,00", "+5.2%")
    col2.metric("ROI", "12.5%", "+1.1%")
    col3.metric("Win Rate", "68%", "-2%")
    col4.metric("Banca Atual", "R$ 5.400,00")

    st.divider()
    st.subheader("📈 Evolução do Patrimônio")
    st.line_chart([100, 120, 110, 150, 180, 175, 210])

# --- TELA: ANÁLISE PREDITIVA ---
elif menu == "⚽ Análise Preditiva":
    st.title("🤖 Inteligência Poisson")
    if not df_csv.empty:
        c1, c2 = st.columns(2)
        pais = c1.selectbox("Selecione o País", sorted(df_csv['pais'].unique()))
        liga = c2.selectbox("Selecione a Liga", sorted(df_csv[df_csv['pais'] == pais]['divisao'].unique()))
        
        filtro = df_csv[(df_csv['pais'] == pais) & (df_csv['divisao'] == liga)]
        times = sorted(filtro['mandante'].unique())
        
        t1, t2 = st.columns(2)
        casa = t1.selectbox("Time da Casa", times)
        fora = t2.selectbox("Time de Fora", [t for t in times if t != casa])
        
        if st.button("GERAR PROGNÓSTICO", use_container_width=True):
            s_c = Engine.calcular_stats(df_csv, casa, 'mandante')
            s_f = Engine.calcular_stats(df_csv, fora, 'visitante')
            
            if s_c and s_f:
                prob_c, prob_f, prob_e = 0, 0, 0
                for gc in range(6):
                    for gf in range(6):
                        p = Engine.poisson(gc, s_c['gols']) * Engine.poisson(gf, s_f['gols'])
                        if gc > gf: prob_c += p
                        elif gf > gc: prob_f += p
                        else: prob_e += p
                
                m1, m2, m3 = st.columns(3)
                m1.metric(f"Vitoria {casa}", f"{prob_c*100:.1f}%")
                m2.metric("Empate", f"{prob_e*100:.1f}%")
                m3.metric(f"Vitoria {fora}", f"{prob_f*100:.1f}%")

# --- TELA: REGISTRAR APOSTA (IGUAL DESKTOP) ---
elif menu == "📝 Registrar Aposta":
    st.title("🖊️ Registrar Nova Aposta")
    
    with st.form("form_aposta", clear_on_submit=True):
        col_data, col_pais = st.columns(2)
        data_aposta = col_data.date_input("Data da Aposta")
        
        # Filtros dinâmicos puxando do CSV
        paises_lista = sorted(df_csv['pais'].unique()) if not df_csv.empty else []
        pais_sel = col_pais.selectbox("País", paises_lista)
        
        ligas_lista = sorted(df_csv[df_csv['pais'] == pais_sel]['divisao'].unique()) if not df_csv.empty else []
        liga_sel = st.selectbox("Liga", ligas_lista)
        
        times_lista = sorted(df_csv[(df_csv['pais'] == pais_sel) & (df_csv['divisao'] == liga_sel)]['mandante'].unique()) if not df_csv.empty else []
        col_m, col_v = st.columns(2)
        mandante_sel = col_m.selectbox("Mandante", times_lista)
        visitante_sel = col_v.selectbox("Visitante", [t for t in times_lista if t != mandante_sel])
        
        col_mer, col_odd, col_stk = st.columns(3)
        mercado = col_mer.text_input("Mercado (Ex: Over 2.5)")
        odd = col_odd.number_input("Odd", min_value=1.01, step=0.01, format="%.2f")
        stake = col_stk.number_input("Stake (R$)", min_value=1.0, step=1.0)
        
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
                    st.error(f"Erro ao salvar dados: {e}")
            else:
                st.error("Não foi possível conectar à planilha. Verifique os Secrets.")
