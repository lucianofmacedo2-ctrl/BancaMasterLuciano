import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Banca Master Luciano", layout="wide")

# --- CONEXÃO SUPABASE ---
@st.cache_resource
def conectar_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = conectar_supabase()

# --- CARREGAR DADOS DO CSV (FILTROS) ---
@st.cache_data
def carregar_dados_csv():
    try:
        # Tenta carregar o arquivo CSV que você tem no GitHub
        df = pd.read_csv("dados_25_26.csv", sep=None, engine='python')
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

df_csv = carregar_dados_csv()

# --- NAVEGAÇÃO ---
st.sidebar.title("🏆 BancaMaster")
menu = st.sidebar.radio("Ir para:", ["🏠 Dashboard", "📝 Registrar Aposta"])

# --- TELA: DASHBOARD ---
if menu == "🏠 Dashboard":
    st.title("📊 Dashboard de Performance")
    
    # Busca dados reais do Supabase
    try:
        res = supabase.table("apostas").select("*").execute()
        df_nuvem = pd.DataFrame(res.data)
        
        if not df_nuvem.empty:
            st.write(f"Total de apostas no banco: {len(df_nuvem)}")
            # Aqui no futuro faremos os cálculos de Green/Red
        else:
            st.info("Aguardando o primeiro registro de aposta...")
    except:
        st.warning("Banco de dados conectado. Próximo passo: registrar uma aposta.")

# --- TELA: REGISTRAR APOSTA ---
elif menu == "📝 Registrar Aposta":
    st.title("🖊️ Registrar Nova Entrada")
    
    with st.form("form_aposta", clear_on_submit=True):
        col1, col2 = st.columns(2)
        data = col1.date_input("Data da Aposta")
        
        paises = sorted(df_csv['pais'].unique()) if not df_csv.empty else ["Brasil"]
        pais = col2.selectbox("País", paises)
        
        ligas = sorted(df_csv[df_csv['pais'] == pais]['divisao'].unique()) if not df_csv.empty else ["Série A"]
        liga = col1.selectbox("Liga", ligas)
        
        times = sorted(df_csv[(df_csv['pais'] == pais) & (df_csv['divisao'] == liga)]['mandante'].unique()) if not df_csv.empty else ["Time A"]
        mandante = col1.selectbox("Mandante", times)
        visitante = col2.selectbox("Visitante", [t for t in times if t != mandante] + ["Time B"])
        
        c3, c4, c5 = st.columns(3)
        mercado = c3.text_input("Mercado (Ex: Over 2.5)")
        odd = c4.number_input("Odd", min_value=1.01, value=1.80, step=0.01)
        stake = c5.number_input("Stake (R$)", min_value=1.0, value=10.0)
        
        resultado = st.selectbox("Resultado Final", ["Pendente", "Green", "Red", "Devolvida"])
        
        if st.form_submit_button("SALVAR NA NUVEM", use_container_width=True):
            try:
                # Monta os dados para o Supabase
                dados_aposta = {
                    "data": str(data),
                    "pais": pais,
                    "liga": liga,
                    "mandante": mandante,
                    "visitante": visitante,
                    "mercado": mercado,
                    "odd": float(odd),
                    "stake": float(stake),
                    "resultado": resultado
                }
                # Insere na tabela 'apostas'
                supabase.table("apostas").insert(dados_aposta).execute()
                st.success("✅ Aposta gravada com sucesso no Supabase!")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}. Verifique se as colunas na tabela 'apostas' foram criadas.")
