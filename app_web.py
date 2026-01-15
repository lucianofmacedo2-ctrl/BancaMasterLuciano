import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Banca Master Pro", layout="wide", initial_sidebar_state="expanded")

# --- CSS DE ALTO CONTRASTE (SIDEBAR + INPUTS + SELEÇÃO) ---
st.markdown("""
    <style>
    /* 1. FUNDO GERAL E TEXTO */
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* 2. MENU LATERAL (SIDEBAR) - CORREÇÃO DE CONTRASTE */
    [data-testid="stSidebar"] {
        background-color: #1a1c24 !important;
        border-right: 1px solid #333;
    }
    /* Texto das opções do menu lateral */
    [data-testid="stSidebar"] .st-emotion-cache-17l6i46, 
    [data-testid="stSidebar"] p, 
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: #ffffff !important;
        font-weight: 600 !important;
        font-size: 16px !important;
    }
    /* Título do menu lateral */
    [data-testid="stSidebar"] h1 { color: #00ff88 !important; }

    /* 3. INPUTS E SELECTBOX (CAMPOS DE SELEÇÃO) */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #1e222e !important;
        color: #ffffff !important;
        border: 2px solid #00ff88 !important; /* Borda Neon visível */
        border-radius: 8px !important;
    }
    
    /* Texto dentro dos campos de seleção */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        color: #ffffff !important;
        font-weight: bold !important;
    }

    /* Dropdown (Lista que abre ao clicar) */
    div[role="listbox"] { 
        background-color: #1e222e !important; 
        border: 2px solid #4f5366 !important; 
    }
    div[role="option"] { 
        color: #ffffff !important; 
        padding: 10px !important;
    }
    div[role="option"]:hover { 
        background-color: #00ff88 !important; 
        color: #000000 !important; 
    }

    /* 4. CARDS DE MÉTRICAS (DASHBOARD) */
    div[data-testid="stMetric"] {
        background-color: #1a1c24 !important;
        border: 1px solid #333 !important;
        padding: 20px !important;
        border-radius: 12px !important;
    }
    div[data-testid="stMetricValue"] > div { color: #00ff88 !important; }
    div[data-testid="stMetricLabel"] > div > p { color: #aaaaaa !important; }

    /* 5. TABELAS */
    .stDataFrame, div[data-testid="stTable"] { 
        background-color: #1a1c24 !important; 
        border-radius: 8px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXÃO SUPABASE ---
@st.cache_resource
def conectar_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except: return None

supabase = conectar_supabase()

# --- CARREGAMENTO DE DADOS CSV ---
@st.cache_data
def carregar_dados_csv():
    try:
        df = pd.read_csv("dados_25_26.csv", sep=None, engine='python')
        df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
        cols_num = ['gols_mandante_ft', 'gols_visitante_ft', 'gols_mandante_ht', 'gols_visitante_ht',
                    'mandante_finalizacoes', 'visitante_finalizacoes', 'mandante_chute_ao_gol', 
                    'visitante_chute_ao_gol', 'mandante_cantos', 'visitante_cantos', 
                    'mandante_cartao_amarelo', 'visitante_cartao_amarelo']
        for c in cols_num:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        if 'data' in df.columns: df['data'] = pd.to_datetime(df['data'], errors='coerce')
        return df
    except: return pd.DataFrame()

df_csv = carregar_dados_csv()

# --- FUNÇÕES DE BANCO DE DADOS ---
def carregar_bancas():
    try:
        res = supabase.table("bancas").select("*").execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

def carregar_apostas():
    try:
        res = supabase.table("apostas").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            df['data'] = pd.to_datetime(df['data']).dt.date
            df['odd'] = pd.to_numeric(df['odd'])
            df['stake'] = pd.to_numeric(df['stake'])
            df['lucro'] = pd.to_numeric(df['lucro'])
        return df
    except: return pd.DataFrame()

def calcular_lucro_real(resultado, odd, stake):
    status = str(resultado).strip().lower()
    if status == 'green': return (stake * odd) - stake
    if status == 'meio green': return ((stake * odd) - stake) / 2
    if status == 'red': return -stake
    if status == 'meio red': return -stake / 2
    return 0.0

# --- MENU LATERAL ---
st.sidebar.title("🚀 Banca Master Pro")
menu = st.sidebar.radio("Navegação", [
    "📊 Dashboard Analítico", 
    "⚽ Análise de Times", 
    "📝 Registrar Aposta", 
    "📂 Histórico de Apostas",
    "💰 Depósitos e Saques",
    "🏦 Minhas Bancas"
])

# ==============================================================================
# 1. DASHBOARD
# ==============================================================================
if menu == "📊 Dashboard Analítico":
    st.title("Dashboard de Performance")
    df_apostas = carregar_apostas()
    
    if df_apostas.empty:
        st.info("Nenhuma aposta registrada.")
    else:
        resolvidas = df_apostas[~df_apostas['resultado'].isin(['Pendente', 'Em Aberto'])]
        lucro_total = resolvidas['lucro'].sum()
        roi = (lucro_total / resolvidas['stake'].sum() * 100) if not resolvidas.empty else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Lucro Total", f"R$ {lucro_total:.2f}")
        c2.metric("ROI Geral", f"{roi:.2f}%")
        c3.metric("Entradas", len(resolvidas))
        
        st.subheader("📈 Evolução")
        resolvidas = resolvidas.sort_values('data')
        resolvidas['acumulado'] = resolvidas['lucro'].cumsum()
        fig = px.line(resolvidas, x='data', y='acumulado', markers=True, template="plotly_dark")
        fig.update_traces(line_color='#00ff88')
        st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# 2. ANÁLISE DE TIMES
# ==============================================================================
elif menu == "⚽ Análise de Times":
    st.title("🔎 Scout Avançado")
    if df_csv.empty:
        st.error("CSV não carregado.")
    else:
        c1, c2 = st.columns(2)
        pais_sel = c1.selectbox("País", sorted(df_csv['pais'].unique()))
        liga_sel = c2.selectbox("Liga", sorted(df_csv[df_csv['pais'] == pais_sel]['divisao'].unique()))
        
        times = sorted(df_csv[df_csv['divisao'] == liga_sel]['mandante'].unique())
        c3, c4 = st.columns(2)
        m_sel = c3.selectbox("Mandante", times)
        v_sel = c4.selectbox("Visitante", [t for t in times if t != m_sel])

        # Estatísticas Casa vs Fora
        df_m = df_csv[(df_csv['mandante'] == m_sel) & (df_csv['divisao'] == liga_sel)]
        df_v = df_csv[(df_csv['visitante'] == v_sel) & (df_csv['divisao'] == liga_sel)]
        
        st.subheader("📊 Médias do Confronto")
        res_m = {"Gols FT": df_m['gols_mandante_ft'].mean(), "Cantos": df_m['mandante_cantos'].mean(), "Chutes": df_m['mandante_chute_ao_gol'].mean()}
        res_v = {"Gols FT": df_v['gols_visitante_ft'].mean(), "Cantos": df_v['visitante_cantos'].mean(), "Chutes": df_v['visitante_chute_ao_gol'].mean()}
        
        st.table(pd.DataFrame({f"{m_sel} (Casa)": res_m, f"{v_sel} (Fora)": res_v}).T)

# ==============================================================================
# 3. REGISTRAR APOSTA
# ==============================================================================
elif menu == "📝 Registrar Aposta":
    st.title("Nova Entrada")
    df_bancas = carregar_bancas()
    if df_bancas.empty:
        st.warning("Crie uma banca primeiro.")
    else:
        with st.form("form_registro"):
            b_sel = st.selectbox("Banca", df_bancas['nome'])
            c1, c2 = st.columns(2)
            mandante = c1.text_input("Mandante")
            visitante = c2.text_input("Visitante")
            mercado = st.text_input("Mercado")
            c3, c4, c5 = st.columns(3)
            odd = c3.number_input("Odd", 1.01, value=1.90)
            stake = c4.number_input("Stake", 1.0, value=50.0)
            res = c5.selectbox("Resultado", ["Pendente", "Green", "Red", "Meio Green", "Meio Red"])
            
            if st.form_submit_button("SALVAR"):
                b_id = int(df_bancas[df_bancas['nome'] == b_sel]['id'].iloc[0])
                lucro = calcular_lucro_real(res, odd, stake)
                supabase.table("apostas").insert({
                    "banca_id": b_id, "data": str(datetime.now().date()), "mandante": mandante,
                    "visitante": visitante, "mercado": mercado, "odd": odd, "stake": stake, 
                    "resultado": res, "lucro": lucro
                }).execute()
                st.success("Salvo!")

# ==============================================================================
# 4. HISTÓRICO
# ==============================================================================
elif menu == "📂 Histórico de Apostas":
    st.title("Gestão de Entradas")
    df = carregar_apostas()
    if not df.empty:
        config = {"resultado": st.column_config.SelectboxColumn("Resultado", options=["Pendente", "Green", "Meio Green", "Red", "Meio Red", "Anulada"])}
        editado = st.data_editor(df, column_config=config, use_container_width=True, hide_index=True)
        if st.button("💾 SALVAR ALTERAÇÕES"):
            for i, row in editado.iterrows():
                novo_lucro = calcular_lucro_real(row['resultado'], row['odd'], row['stake'])
                supabase.table("apostas").update({"resultado": row['resultado'], "lucro": novo_lucro}).eq("id", row['id']).execute()
            st.rerun()

# ==============================================================================
# 5. DEPÓSITOS / 6. BANCAS
# ==============================================================================
elif menu == "💰 Depósitos e Saques":
    st.title("Caixa")
    # Lógica de transações simplificada
    st.info("Menu para controle de depósitos e saques nas bancas.")

elif menu == "🏦 Minhas Bancas":
    st.title("Bancas")
    nome = st.text_input("Nome da Banca")
    if st.button("CRIAR"):
        supabase.table("bancas").insert({"nome": nome}).execute()
        st.rerun()
