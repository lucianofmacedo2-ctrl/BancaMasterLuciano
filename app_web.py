import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Banca Master Pro", layout="wide", initial_sidebar_state="expanded")

# --- CSS DE ALTO CONTRASTE (CORREÇÃO PARA TODOS OS CAMPOS) ---
st.markdown("""
    <style>
    /* Fundo Geral */
    .stApp { background-color: #0e1117; color: #ffffff; }
    
    /* Labels e Títulos */
    h1, h2, h3, h4, h5, h6, label, p, .stMarkdown { color: #ffffff !important; font-weight: 600 !important; }

    /* INPUTS E SELECTBOX - FUNDO ESCURO E TEXTO BRANCO */
    .stTextInput input, .stNumberInput input, .stDateInput input, .stSelectbox div[data-baseweb="select"] {
        background-color: #1e222e !important;
        color: #ffffff !important;
        border: 1px solid #00ff88 !important; /* Verde Neon */
        border-radius: 8px !important;
        height: 45px;
    }

    /* Texto dentro do Selectbox */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
        color: #ffffff !important;
        font-weight: bold;
    }

    /* Dropdown (Lista de opções ao clicar) */
    div[role="listbox"] { background-color: #1e222e !important; border: 1px solid #4f5366 !important; }
    div[role="option"] { color: #ffffff !important; }
    div[role="option"]:hover { background-color: #00ff88 !important; color: #000000 !important; }

    /* CARDS DE MÉTRICAS */
    div[data-testid="stMetric"] {
        background-color: #1a1c24 !important;
        border: 1px solid #333 !important;
        padding: 20px !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetricValue"] > div { color: #00ff88 !important; font-size: 32px !important; }
    div[data-testid="stMetricLabel"] > div > p { color: #aaaaaa !important; font-size: 16px !important; }

    /* TABELAS E DATAEDITOR */
    .stDataFrame, div[data-testid="stTable"] { 
        background-color: #1a1c24 !important; 
        border: 1px solid #333 !important;
        border-radius: 8px !important;
    }
    
    /* Abas */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #1a1c24 !important;
        border: 1px solid #333 !important;
        color: white !important;
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00ff88 !important;
        color: black !important;
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
        
        # Colunas numéricas essenciais para análise
        cols_num = [
            'gols_mandante_ft', 'gols_visitante_ft', 'gols_mandante_ht', 'gols_visitante_ht',
            'mandante_finalizacoes', 'visitante_finalizacoes', 
            'mandante_chute_ao_gol', 'visitante_chute_ao_gol',
            'mandante_cantos', 'visitante_cantos', 
            'mandante_cartao_amarelo', 'visitante_cartao_amarelo'
        ]
        for c in cols_num:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
            
        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], errors='coerce')
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
# 1. DASHBOARD ANALÍTICO
# ==============================================================================
if menu == "📊 Dashboard Analítico":
    st.title("Dashboard de Performance")
    df_apostas = carregar_apostas()
    
    if df_apostas.empty:
        st.info("Nenhuma aposta registrada para exibir estatísticas.")
    else:
        resolvidas = df_apostas[~df_apostas['resultado'].isin(['Pendente', 'Em Aberto'])]
        lucro_total = resolvidas['lucro'].sum()
        roi = (lucro_total / resolvidas['stake'].sum() * 100) if not resolvidas.empty else 0
        win_rate = (len(resolvidas[resolvidas['lucro'] > 0]) / len(resolvidas) * 100) if not resolvidas.empty else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Lucro Total", f"R$ {lucro_total:.2f}")
        c2.metric("ROI Geral", f"{roi:.2f}%")
        c3.metric("Taxa de Acerto", f"{win_rate:.1f}%")
        
        st.subheader("📈 Evolução da Banca")
        resolvidas = resolvidas.sort_values('data')
        resolvidas['acumulado'] = resolvidas['lucro'].cumsum()
        fig = px.line(resolvidas, x='data', y='acumulado', markers=True, template="plotly_dark")
        fig.update_traces(line_color='#00ff88')
        st.plotly_chart(fig, use_container_width=True)

# ==============================================================================
# 2. ANÁLISE DE TIMES (SISTEMA COMPLETO)
# ==============================================================================
elif menu == "⚽ Análise de Times":
    st.title("🔎 Scout Avançado")
    
    if df_csv.empty:
        st.error("O arquivo 'dados_25_26.csv' não foi encontrado ou está vazio.")
    else:
        # Filtros em Cascata
        col1, col2 = st.columns(2)
        paises = sorted(df_csv['pais'].unique())
        pais_sel = col1.selectbox("Selecione o País", paises)
        
        ligas = sorted(df_csv[df_csv['pais'] == pais_sel]['divisao'].unique())
        liga_sel = col2.selectbox("Selecione a Liga", ligas)
        
        df_filtrado = df_csv[(df_csv['pais'] == pais_sel) & (df_csv['divisao'] == liga_sel)]
        times = sorted(df_filtrado['mandante'].unique())
        
        col3, col4 = st.columns(2)
        m_sel = col3.selectbox("Time Mandante", times)
        v_sel = col4.selectbox("Time Visitante", [t for t in times if t != m_sel])

        st.divider()

        # Dados Específicos
        df_m_casa = df_filtrado[df_filtrado['mandante'] == m_sel]
        df_v_fora = df_filtrado[df_filtrado['visitante'] == v_sel]
        df_m_geral = df_filtrado[(df_filtrado['mandante'] == m_sel) | (df_filtrado['visitante'] == m_sel)]
        df_v_geral = df_filtrado[(df_filtrado['mandante'] == v_sel) | (df_filtrado['visitante'] == v_sel)]

        # Probabilidades
        def calcular_probabilidades(m_df, v_df):
            if m_df.empty or v_df.empty: return 33, 34, 33
            v_m = len(m_df[m_df['gols_mandante_ft'] > m_df['gols_visitante_ft']]) / len(m_df)
            v_v = len(v_df[v_df['gols_visitante_ft'] > v_df['gols_mandante_ft']]) / len(v_df)
            emp = 1 - (v_m + v_v) if (v_m + v_v) < 1 else 0.2
            total = v_m + v_v + emp
            return (v_m/total)*100, (emp/total)*100, (v_v/total)*100

        p_m, p_e, p_v = calcular_probabilidades(df_m_casa, df_v_fora)

        col_p1, col_p2, col_p3 = st.columns(3)
        col_p1.metric(f"Vitória {m_sel}", f"{p_m:.1f}%")
        col_p2.metric("Empate", f"{p_e:.1f}%")
        col_p3.metric(f"Vitória {v_sel}", f"{p_v:.1f}%")

        # Tabela de Médias
        st.subheader("📊 Médias do Confronto (Casa vs Fora)")
        
        def get_team_stats(df, is_home):
            pre = 'mandante_' if is_home else 'visitante_'
            return {
                "Gols FT": df[f'{pre}gols_mandante_ft' if is_home else f'{pre}gols_visitante_ft'].mean(),
                "Gols HT": df[f'{pre}gols_mandante_ht' if is_home else f'{pre}gols_visitante_ht'].mean(),
                "Finalizações": df[f'{pre}finalizacoes'].mean(),
                "Chutes ao Gol": df[f'{pre}chute_ao_gol'].mean(),
                "Cantos": df[f'{pre}cantos'].mean(),
                "Cartões Am.": df[f'{pre}cartao_amarelo'].mean()
            }

        stats_m = get_team_stats(df_m_casa, True)
        stats_v = get_team_stats(df_v_fora, False)

        df_stats = pd.DataFrame({
            "Estatística": stats_m.keys(),
            f"{m_sel} (Em Casa)": stats_m.values(),
            f"{v_sel} (Fora)": stats_v.values()
        })
        st.table(df_stats.set_index("Estatística").style.format(precision=2))

        # Forma (Últimos 5)
        st.subheader("📈 Forma Recente (Últimos 5 Jogos)")
        t1, t2 = st.tabs(["Fator Local (Casa/Fora)", "Forma Geral"])
        
        with t1:
            c5, c6 = st.columns(2)
            c5.write(f"**{m_sel} em Casa**")
            c5.dataframe(df_m_casa.sort_values('data', ascending=False).head(5)[['data', 'visitante', 'gols_mandante_ft', 'gols_visitante_ft']], hide_index=True)
            c6.write(f"**{v_sel} Fora**")
            c6.dataframe(df_v_fora.sort_values('data', ascending=False).head(5)[['data', 'mandante', 'gols_mandante_ft', 'gols_visitante_ft']], hide_index=True)
            
        with t2:
            c7, c8 = st.columns(2)
            c7.write(f"**{m_sel} (Geral)**")
            c7.dataframe(df_m_geral.sort_values('data', ascending=False).head(5)[['data', 'mandante', 'visitante', 'gols_mandante_ft', 'gols_visitante_ft']], hide_index=True)
            c8.write(f"**{v_sel} (Geral)**")
            c8.dataframe(df_v_geral.sort_values('data', ascending=False).head(5)[['data', 'mandante', 'visitante', 'gols_mandante_ft', 'gols_visitante_ft']], hide_index=True)

# ==============================================================================
# 3. REGISTRAR APOSTA
# ==============================================================================
elif menu == "📝 Registrar Aposta":
    st.title("Nova Entrada")
    df_bancas = carregar_bancas()
    
    if df_bancas.empty:
        st.warning("Crie uma banca primeiro no menu 'Minhas Bancas'.")
    else:
        with st.form("form_registro", clear_on_submit=True):
            banca_sel = st.selectbox("Selecione a Banca", df_bancas['nome'])
            b_id = int(df_bancas[df_bancas['nome'] == banca_sel]['id'].iloc[0])
            
            c1, c2 = st.columns(2)
            data = c1.date_input("Data", datetime.now())
            pais = c2.selectbox("País", sorted(df_csv['pais'].unique()) if not df_csv.empty else ["Manual"])
            
            c3, c4 = st.columns(2)
            mandante = c3.text_input("Mandante")
            visitante = c4.text_input("Visitante")
            
            mercado = st.text_input("Mercado (Ex: Over 2.5)")
            
            c5, c6, c7 = st.columns(3)
            odd = c5.number_input("Odd", 1.01, 100.0, 1.90)
            stake = c6.number_input("Stake (R$)", 1.0, 100000.0, 50.0)
            res = c7.selectbox("Resultado Inicial", ["Pendente", "Green", "Meio Green", "Red", "Meio Red"])
            
            if st.form_submit_button("SALVAR APOSTA"):
                lucro = calcular_lucro_real(res, odd, stake)
                dados = {
                    "banca_id": b_id, "data": str(data), "mandante": mandante,
                    "visitante": visitante, "mercado": mercado, "odd": odd,
                    "stake": stake, "resultado": res, "lucro": lucro
                }
                supabase.table("apostas").insert(dados).execute()
                st.success("Aposta registrada com sucesso!")

# ==============================================================================
# 4. HISTÓRICO DE APOSTAS
# ==============================================================================
elif menu == "📂 Histórico de Apostas":
    st.title("Gestão de Entradas")
    df = carregar_apostas()
    
    if df.empty:
        st.info("Nenhuma aposta no histórico.")
    else:
        st.write("Edite o resultado para atualizar automaticamente o lucro.")
        config = {
            "resultado": st.column_config.SelectboxColumn("Resultado", options=["Pendente", "Green", "Meio Green", "Red", "Meio Red", "Anulada"]),
            "lucro": st.column_config.NumberColumn("Lucro (R$)", disabled=True),
            "id": st.column_config.TextColumn("ID", disabled=True)
        }
        
        editado = st.data_editor(df, column_config=config, use_container_width=True, hide_index=True)
        
        if st.button("💾 ATUALIZAR ALTERAÇÕES"):
            for i, row in editado.iterrows():
                novo_lucro = calcular_lucro_real(row['resultado'], row['odd'], row['stake'])
                supabase.table("apostas").update({"resultado": row['resultado'], "lucro": novo_lucro}).eq("id", row['id']).execute()
            st.success("Histórico atualizado!")
            st.rerun()

# ==============================================================================
# 5. DEPÓSITOS E SAQUES
# ==============================================================================
elif menu == "💰 Depósitos e Saques":
    st.title("Fluxo de Caixa")
    df_bancas = carregar_bancas()
    
    if not df_bancas.empty:
        with st.form("form_caixa"):
            b_sel = st.selectbox("Banca", df_bancas['nome'])
            b_id = int(df_bancas[df_bancas['nome'] == b_sel]['id'].iloc[0])
            tipo = st.radio("Operação", ["Depósito", "Saque"], horizontal=True)
            valor = st.number_input("Valor (R$)", 1.0)
            data = st.date_input("Data", datetime.now())
            
            if st.form_submit_button("EFETUAR LANÇAMENTO"):
                supabase.table("transacoes").insert({
                    "banca_id": b_id, "tipo": tipo, "valor": valor, "data": str(data)
                }).execute()
                st.success(f"{tipo} realizado com sucesso!")

# ==============================================================================
# 6. MINHAS BANCAS
# ==============================================================================
elif menu == "🏦 Minhas Bancas":
    st.title("Gerenciar Bancas")
    
    with st.form("nova_banca"):
        nome = st.text_input("Nome da Nova Banca (Ex: Bet365, Gestão 2026)")
        if st.form_submit_button("CRIAR BANCA"):
            if nome:
                supabase.table("bancas").insert({"nome": nome}).execute()
                st.success("Banca criada!")
                st.rerun()
            else: st.error("Insira um nome.")
            
    st.divider()
    df_b = carregar_bancas()
    if not df_b.empty:
        for i, r in df_b.iterrows():
            col_b1, col_b2 = st.columns([4, 1])
            col_b1.subheader(f"🏦 {r['nome']}")
            if col_b2.button("Excluir", key=f"del_{r['id']}"):
                supabase.table("bancas").delete().eq("id", r['id']).execute()
                st.rerun()
