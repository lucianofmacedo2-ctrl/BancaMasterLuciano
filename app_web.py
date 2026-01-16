import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Banca Master Pro", layout="wide", initial_sidebar_state="expanded")

# --- CSS PERSONALIZADO (CORES E CONTRASTE) ---
st.markdown(f"""
    <style>
    /* 1. FUNDO DA TELA PRINCIPAL */
    .stApp {{
        background-color: #0b5754 !important;
        color: #ffffff !important;
    }}
    
    /* 2. MENU LATERAL (SIDEBAR) */
    [data-testid="stSidebar"] {{
        background-color: #030844 !important;
        border-right: 1px solid #ffffff33;
    }}
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] h1 {{
        color: #ffffff !important;
        font-weight: 600 !important;
    }}

    /* 3. CARDS DE MÉTRICAS */
    div[data-testid="stMetric"] {{
        background-color: #050f54 !important;
        border: 1px solid #ffffff33 !important;
        padding: 20px !important;
        border-radius: 12px !important;
    }}
    div[data-testid="stMetricValue"] > div {{ color: #ffffff !important; }}
    div[data-testid="stMetricLabel"] > div > p {{ color: #ffffff !important; }}

    /* 4. CAIXAS DE SELEÇÃO E DIGITAÇÃO (Fundo Branco, Texto Preto) */
    .stTextInput input, .stNumberInput input, .stDateInput input, 
    .stSelectbox div[data-baseweb="select"] {{
        background-color: #ffffff !important;
        color: #000000 !important;
        border-radius: 5px !important;
    }}
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
        color: #000000 !important;
    }}

    /* 5. TABELAS COM ALTO CONTRASTE (FONTE BRANCA) */
    div[data-testid="stTable"] table {{
        color: #ffffff !important;
        background-color: rgba(5, 15, 84, 0.5) !important;
    }}
    div[data-testid="stTable"] th {{
        color: #ffffff !important;
        background-color: #030844 !important;
    }}
    div[data-testid="stTable"] td {{
        color: #ffffff !important;
        border-bottom: 1px solid #ffffff22 !important;
    }}

    /* Estilo para as abas de Forma */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 10px;
    }}
    .stTabs [data-baseweb="tab"] {{
        background-color: #030844 !important;
        color: white !important;
        border-radius: 4px;
        padding: 8px 16px;
    }}
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

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def carregar_dados_csv():
    try:
        df = pd.read_csv("dados_25_26.csv", sep=None, engine='python')
        df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
        # Conversão de colunas numéricas
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

# --- FUNÇÕES AUXILIARES ---
def carregar_bancas():
    try:
        res = supabase.table("bancas").select("*").execute()
        return pd.DataFrame(res.data)
    except: return pd.DataFrame()

def calcular_probabilidades(df_m, df_v):
    if df_m.empty or df_v.empty: return 33, 34, 33
    win_m = len(df_m[df_m['gols_mandante_ft'] > df_m['gols_visitante_ft']]) / len(df_m)
    win_v = len(df_v[df_v['gols_visitante_ft'] > df_v['gols_mandante_ft']]) / len(df_v)
    draw = 1 - (win_m + win_v) if (win_m + win_v) < 1 else 0.1
    total = win_m + win_v + draw
    return (win_m/total)*100, (draw/total)*100, (win_v/total)*100

# --- NAVEGAÇÃO ---
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "⚽ Análise de Times", "📝 Registrar Aposta", "📂 Histórico", "🏦 Bancas"])

# ==============================================================================
# SEÇÃO: ANÁLISE DE TIMES
# ==============================================================================
if menu == "⚽ Análise de Times":
    st.title("🔎 Análise Estatística de Confronto")
    
    if not df_csv.empty:
        c1, c2 = st.columns(2)
        pais = c1.selectbox("País", sorted(df_csv['pais'].unique()))
        liga = c2.selectbox("Liga", sorted(df_csv[df_csv['pais'] == pais]['divisao'].unique()))
        
        times = sorted(df_csv[df_csv['divisao'] == liga]['mandante'].unique())
        c3, c4 = st.columns(2)
        m_sel = c3.selectbox("Time Mandante", times)
        v_sel = c4.selectbox("Time Visitante", [t for t in times if t != m_sel])

        # Filtragem específica (Casa/Fora)
        df_casa = df_csv[(df_csv['mandante'] == m_sel) & (df_csv['divisao'] == liga)].sort_values('data', ascending=False)
        df_fora = df_csv[(df_csv['visitante'] == v_sel) & (df_csv['divisao'] == liga)].sort_values('data', ascending=False)

        st.divider()

        # 1. PROGNÓSTICO DE PROBABILIDADE
        st.subheader("🎯 Prognóstico (Baseado em histórico Casa/Fora)")
        p_m, p_e, p_v = calcular_probabilidades(df_casa, df_fora)
        cp1, cp2, cp3 = st.columns(3)
        cp1.metric(f"Vitória {m_sel}", f"{p_m:.1f}%")
        cp2.metric("Empate", f"{p_e:.1f}%")
        cp3.metric(f"Vitória {v_sel}", f"{p_v:.1f}%")

        # 2. TABELA DE MÉDIAS (ALTO CONTRASTE)
        st.subheader("📊 Comparativo de Médias Específicas")
        
        def get_stats(df, is_home):
            pre = 'mandante_' if is_home else 'visitante_'
            opp = 'visitante_' if is_home else 'mandante_'
            return {
                "Gols FT": df[f'{pre}gols_mandante_ft' if is_home else f'{pre}gols_visitante_ft'].mean(),
                "Gols HT": df[f'{pre}gols_mandante_ht' if is_home else f'{pre}gols_visitante_ht'].mean(),
                "Cantos": df[f'{pre}cantos'].mean(),
                "Finalizações": df[f'{pre}finalizacoes'].mean(),
                "Chutes ao Gol": df[f'{pre}chute_ao_gol'].mean(),
                "Cartões": df[f'{pre}cartao_amarelo'].mean()
            }

        stats_m = get_stats(df_casa, True)
        stats_v = get_stats(df_fora, False)

        df_medias = pd.DataFrame({
            "Estatística": stats_m.keys(),
            f"{m_sel} (Em Casa)": stats_m.values(),
            f"{v_sel} (Fora)": stats_v.values()
        })
        st.table(df_medias.set_index("Estatística").style.format(precision=2))

        # 3. FORMA NOS ÚLTIMOS 5 JOGOS
        st.subheader("📈 Forma (Últimos 5 Jogos)")
        tf1, tf2 = st.columns(2)
        
        with tf1:
            st.write(f"**{m_sel}** (Jogando em Casa)")
            ultimos_5_c = df_casa.head(5)
            if not ultimos_5_c.empty:
                for _, r in ultimos_5_c.iterrows():
                    res = "✅" if r['gols_mandante_ft'] > r['gols_visitante_ft'] else ("🟧" if r['gols_mandante_ft'] == r['gols_visitante_ft'] else "❌")
                    st.write(f"{res} {r['data'].strftime('%d/%m')} vs {r['visitante']} ({int(r['gols_mandante_ft'])} - {int(r['gols_visitante_ft'])})")
            else: st.info("Sem dados recentes.")

        with tf2:
            st.write(f"**{v_sel}** (Jogando Fora)")
            ultimos_5_v = df_fora.head(5)
            if not ultimos_5_v.empty:
                for _, r in ultimos_5_v.iterrows():
                    res = "✅" if r['gols_visitante_ft'] > r['gols_mandante_ft'] else ("🟧" if r['gols_mandante_ft'] == r['gols_visitante_ft'] else "❌")
                    st.write(f"{res} {r['data'].strftime('%d/%m')} @ {r['mandante']} ({int(r['gols_mandante_ft'])} - {int(r['gols_visitante_ft'])})")
            else: st.info("Sem dados recentes.")

# (Manter o restante das seções de Dashboard, Registro e Histórico com o CSS aplicado acima)
elif menu == "📊 Dashboard":
    st.title("Dashboard")
    # Lógica do dashboard...
