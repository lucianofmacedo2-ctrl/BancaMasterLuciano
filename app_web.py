import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Banca Master Pro", layout="wide", initial_sidebar_state="expanded")

# --- CSS DE ALTO CONTRASTE ---
st.markdown("""
    <style>
    /* Fundo Geral */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    /* Cards de Métricas */
    div[data-testid="stMetric"] {
        background-color: #262730;
        border: 1px solid #464b5f;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.3);
    }
    div[data-testid="stMetricLabel"] {
        color: #d0d0d0 !important;
        font-size: 14px !important;
        font-weight: bold;
    }
    div[data-testid="stMetricValue"] {
        color: #00e676 !important;
        font-size: 26px !important;
    }
    /* Tabelas */
    div[data-testid="stDataFrame"] {
        background-color: #262730;
        border-radius: 8px;
    }
    /* Abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #262730;
        border-radius: 4px;
        color: white;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #00e676 !important;
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
    except:
        return None

supabase = conectar_supabase()

# --- FUNÇÕES AUXILIARES ---
@st.cache_data
def carregar_dados_csv():
    try:
        df = pd.read_csv("dados_25_26.csv", sep=None, engine='python')
        # Padroniza nomes das colunas (remove espaços, minúsculo)
        df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
        
        # Lista de colunas que PRECISAM ser numéricas para as médias
        cols_numericas = [
            'gols_mandante_ft', 'gols_visitante_ft', 'gols_mandante_ht', 'gols_visitante_ht',
            'mandante_finalizacoes', 'visitante_finalizacoes',
            'mandante_chute_ao_gol', 'visitante_chute_ao_gol',
            'mandante_cantos', 'visitante_cantos',
            'mandante_cartao_amarelo', 'visitante_cartao_amarelo',
            'mandante_cartao_vermelho', 'visitante_cartao_vermelho'
        ]
        
        for col in cols_numericas:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        # Garante coluna de data
        if 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data'], errors='coerce')
            
        return df
    except:
        return pd.DataFrame()

def calcular_lucro_real(resultado, odd, stake):
    try:
        status = str(resultado).strip().lower()
        odd_val = float(odd)
        stake_val = float(stake)
        
        if status == 'green': return (stake_val * odd_val) - stake_val
        elif status == 'meio green': return ((stake_val * odd_val) - stake_val) / 2
        elif status == 'red': return -stake_val
        elif status == 'meio red': return -stake_val / 2
        else: return 0.0
    except: return 0.0

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
            if 'data' in df.columns: df['data'] = pd.to_datetime(df['data']).dt.date
            df['odd'] = pd.to_numeric(df['odd'])
            df['stake'] = pd.to_numeric(df['stake'])
            df['lucro'] = pd.to_numeric(df['lucro'])
        return df
    except: return pd.DataFrame()

df_csv = carregar_dados_csv()

# --- MENU ---
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
# 1. MINHAS BANCAS
# ==============================================================================
if menu == "🏦 Minhas Bancas":
    st.title("Gerenciar Bancas")
    with st.form("nova_banca"):
        nome = st.text_input("Nome da Banca")
        if st.form_submit_button("Criar"):
            supabase.table("bancas").insert({"nome": nome}).execute()
            st.success("Criada!")
            st.rerun()
    st.divider()
    df_b = carregar_bancas()
    if not df_b.empty:
        for i, r in df_b.iterrows():
            c1, c2 = st.columns([4,1])
            c1.markdown(f"#### 🏦 {r['nome']}")
            if c2.button("Excluir", key=r['id']):
                st.error("Apague as apostas desta banca antes de excluir.")

# ==============================================================================
# 2. ANÁLISE DE TIMES (REFORMULADA COMPLETA)
# ==============================================================================
elif menu == "⚽ Análise de Times":
    st.title("🔎 Scout Avançado")
    
    if df_csv.empty:
        st.warning("CSV vazio ou não carregado.")
    else:
        # --- FILTROS ---
        c1, c2, c3, c4 = st.columns(4)
        p = c1.selectbox("País", sorted(df_csv['pais'].unique()))
        l = c2.selectbox("Liga", sorted(df_csv[df_csv['pais']==p]['divisao'].unique()))
        
        times_liga = df_csv[(df_csv['pais']==p)&(df_csv['divisao']==l)]
        tm = c3.selectbox("Mandante", sorted(times_liga['mandante'].unique()))
        tv_list = [x for x in sorted(times_liga['visitante'].unique()) if x != tm]
        if not tv_list: tv_list = ["Selecione"]
        tv = c4.selectbox("Visitante", tv_list)

        st.divider()

        # --- SELEÇÃO DOS DADOS ---
        # 1. Mandante jogando em CASA
        df_home_home = df_csv[df_csv['mandante'] == tm]
        # 2. Mandante GERAL (Casa + Fora)
        df_home_all = df_csv[(df_csv['mandante'] == tm) | (df_csv['visitante'] == tm)]
        
        # 3. Visitante jogando FORA
        df_away_away = df_csv[df_csv['visitante'] == tv]
        # 4. Visitante GERAL (Casa + Fora)
        df_away_all = df_csv[(df_csv['mandante'] == tv) | (df_csv['visitante'] == tv)]

        if df_home_home.empty or df_away_away.empty:
            st.warning("Dados insuficientes para análise Casa x Fora.")
        else:
            # --- FUNÇÃO DE CÁLCULO DE MÉDIAS ---
            def get_stats(df_input, team, side):
                # side = 'home' (se o time procurado é mandante no df), 'away', ou 'all'
                stats = {}
                
                # Filtrar colunas corretas baseadas na perspectiva
                if side == 'home':
                    cols = {
                        'gols_pro': 'gols_mandante_ft', 'gols_sof': 'gols_visitante_ft',
                        'gols_pro_ht': 'gols_mandante_ht', 'gols_sof_ht': 'gols_visitante_ht',
                        'cantos': 'mandante_cantos', 'cartoes': 'mandante_cartao_amarelo',
                        'finalizacoes': 'mandante_finalizacoes', 'chutes_gol': 'mandante_chute_ao_gol'
                    }
                elif side == 'away':
                    cols = {
                        'gols_pro': 'gols_visitante_ft', 'gols_sof': 'gols_mandante_ft',
                        'gols_pro_ht': 'gols_visitante_ht', 'gols_sof_ht': 'gols_mandante_ht',
                        'cantos': 'visitante_cantos', 'cartoes': 'visitante_cartao_amarelo',
                        'finalizacoes': 'visitante_finalizacoes', 'chutes_gol': 'visitante_chute_ao_gol'
                    }
                else: # ALL (Calculo mais complexo, simplificado aqui pela media total das colunas se existirem)
                    return {} 

                # Verifica existencia das colunas e calcula média
                for k, col_name in cols.items():
                    stats[k] = df_input[col_name].mean() if col_name in df_input.columns else 0.0
                
                return stats

            # Stats Específicas (Casa x Fora)
            st_home = get_stats(df_home_home, tm, 'home')
            st_away = get_stats(df_away_away, tv, 'away')
            
            # --- CÁLCULO DE PROBABILIDADE (WIN RATE) ---
            # Home Win Rate em Casa
            hw = len(df_home_home[df_home_home['gols_mandante_ft'] > df_home_home['gols_visitante_ft']])
            hd = len(df_home_home[df_home_home['gols_mandante_ft'] == df_home_home['gols_visitante_ft']])
            hl = len(df_home_home) - hw - hd
            
            # Away Win Rate Fora
            aw = len(df_away_away[df_away_away['gols_visitante_ft'] > df_away_away['gols_mandante_ft']])
            ad = len(df_away_away[df_away_away['gols_visitante_ft'] == df_away_away['gols_mandante_ft']])
            al = len(df_away_away) - aw - ad
            
            # Probabilidade Simples Ponderada
            total_jogos = len(df_home_home) + len(df_away_away)
            prob_h = (hw / len(df_home_home) * 100) if len(df_home_home) > 0 else 0
            prob_a = (aw / len(df_away_away) * 100) if len(df_away_away) > 0 else 0
            prob_d = ((hd/len(df_home_home)) + (ad/len(df_away_away))) / 2 * 100
            
            # Normalizar para 100%
            total_p = prob_h + prob_a + prob_d
            if total_p > 0:
                p_h, p_a, p_d = (prob_h/total_p*100), (prob_a/total_p*100), (prob_d/total_p*100)
            else:
                p_h, p_a, p_d = 0, 0, 0

            st.subheader(f"📊 Expectativa: {tm} x {tv}")
            
            col_p1, col_p2, col_p3 = st.columns(3)
            col_p1.metric(f"Vitória {tm}", f"{p_h:.1f}%")
            col_p2.metric("Empate", f"{p_d:.1f}%")
            col_p3.metric(f"Vitória {tv}", f"{p_a:.1f}%")

            # --- TABELAS COMPARATIVAS ---
            tab1, tab2 = st.tabs(["🏠 Casa vs ✈️ Fora (Específico)", "🌍 Forma Geral (Últimos 5)"])

            with tab1:
                st.markdown("#### Médias por Jogo (Fator Local)")
                
                # Montando o DataFrame Comparativo Bonito
                data_compare = {
                    "Estatística": [
                        "Gols Marcados FT", "Gols Sofridos FT", 
                        "Gols Marcados HT", "Gols Sofridos HT",
                        "Cantos", "Cartões Amarelos", 
                        "Finalizações Totais", "Chutes ao Gol"
                    ],
                    f"{tm} (em Casa)": [
                        st_home['gols_pro'], st_home['gols_sof'],
                        st_home['gols_pro_ht'], st_home['gols_sof_ht'],
                        st_home['cantos'], st_home['cartoes'],
                        st_home['finalizacoes'], st_home['chutes_gol']
                    ],
                    f"{tv} (Fora)": [
                        st_away['gols_pro'], st_away['gols_sof'],
                        st_away['gols_pro_ht'], st_away['gols_sof_ht'],
                        st_away['cantos'], st_away['cartoes'],
                        st_away['finalizacoes'], st_away['chutes_gol']
                    ]
                }
                df_comp = pd.DataFrame(data_compare)
                st.dataframe(df_comp.style.format(precision=2), use_container_width=True, hide_index=True)
                
                c_last1, c_last2 = st.columns(2)
                with c_last1:
                    st.write(f"**Últimos 5 do {tm} em Casa:**")
                    st.dataframe(df_home_home.sort_values('data', ascending=False).head(5)[['data', 'visitante', 'gols_mandante_ft', 'gols_visitante_ft']], hide_index=True)
                with c_last2:
                    st.write(f"**Últimos 5 do {tv} Fora:**")
                    st.dataframe(df_away_away.sort_values('data', ascending=False).head(5)[['data', 'mandante', 'gols_mandante_ft', 'gols_visitante_ft']], hide_index=True)

            with tab2:
                st.markdown("#### Forma Recente (Todos os Jogos)")
                
                c_gen1, c_gen2 = st.columns(2)
                with c_gen1:
                    st.write(f"**Últimos 5 Gerais - {tm}:**")
                    last5_gen_home = df_home_all.sort_values('data', ascending=False).head(5)
                    st.dataframe(last5_gen_home[['data', 'mandante', 'visitante', 'gols_mandante_ft', 'gols_visitante_ft']], hide_index=True)
                    
                with c_gen2:
                    st.write(f"**Últimos 5 Gerais - {tv}:**")
                    last5_gen_away = df_away_all.sort_values('data', ascending=False).head(5)
                    st.dataframe(last5_gen_away[['data', 'mandante', 'visitante', 'gols_mandante_ft', 'gols_visitante_ft']], hide_index=True)

# ==============================================================================
# 3. REGISTRAR APOSTA
# ==============================================================================
elif menu == "📝 Registrar Aposta":
    st.title("Novo Registro")
    df_bancas = carregar_bancas()
    
    if df_bancas.empty:
        st.warning("Cadastre uma banca primeiro.")
    else:
        banca_nome = st.selectbox("Banca", df_bancas['nome'])
        banca_id = int(df_bancas[df_bancas['nome'] == banca_nome]['id'].values[0])
        
        manual = st.checkbox("Entrada Manual")
        
        with st.form("form_aposta", clear_on_submit=True):
            col1, col2 = st.columns(2)
            data = col1.date_input("Data")
            
            if not manual and not df_csv.empty:
                p = col2.selectbox("País", sorted(df_csv['pais'].unique()))
                l = col1.selectbox("Liga", sorted(df_csv[df_csv['pais']==p]['divisao'].unique()))
                m = col2.selectbox("Mandante", sorted(df_csv[(df_csv['pais']==p)&(df_csv['divisao']==l)]['mandante'].unique()))
                v = col1.selectbox("Visitante", [x for x in sorted(df_csv[(df_csv['pais']==p)&(df_csv['divisao']==l)]['mandante'].unique()) if x != m])
            else:
                p, l, m, v = "", "", col2.text_input("Mandante"), col1.text_input("Visitante")

            c3, c4, c5 = st.columns(3)
            mercado = c3.text_input("Mercado")
            odd = c4.number_input("Odd", 1.01, step=0.01)
            stake = c5.number_input("Stake", 1.0, step=10.0)
            res = st.selectbox("Resultado", ["Em Aberto", "Green", "Meio Green", "Red", "Meio Red", "Anulada"])
            
            if st.form_submit_button("SALVAR"):
                lucro = calcular_lucro_real(res, odd, stake)
                dados = {
                    "banca_id": banca_id, "data": str(data),
                    "pais": p, "liga": l, "mandante": m, "visitante": v,
                    "mercado": mercado, "odd": odd, "stake": stake,
                    "resultado": res, "manual": manual, "lucro": lucro
                }
                supabase.table("apostas").insert(dados).execute()
                st.success(f"Salvo! Lucro: R$ {lucro:.2f}")

# ==============================================================================
# 4. HISTÓRICO
# ==============================================================================
elif menu == "📂 Histórico de Apostas":
    st.title("Histórico")
    df = carregar_apostas()
    if not df.empty:
        st.info("📝 Edite o 'Resultado' abaixo para resolver as apostas.")
        
        col_config = {
            "resultado": st.column_config.SelectboxColumn("Resultado", options=["Em Aberto", "Green", "Meio Green", "Red", "Meio Red", "Anulada"], required=True),
            "lucro": st.column_config.NumberColumn("Lucro", disabled=True),
            "id": st.column_config.TextColumn("ID", disabled=True),
        }
        cols = ['id', 'data', 'mandante', 'visitante', 'mercado', 'odd', 'stake', 'resultado', 'lucro']
        
        edited = st.data_editor(df[cols], column_config=col_config, use_container_width=True, hide_index=True, key="hist_edit")
        
        if st.button("💾 ATUALIZAR LUCROS"):
            progresso = st.progress(0)
            for i, row in edited.iterrows():
                novo_lucro = calcular_lucro_real(row['resultado'], row['odd'], row['stake'])
                supabase.table("apostas").update({"resultado": row['resultado'], "lucro": novo_lucro}).eq("id", row['id']).execute()
                progresso.progress((i+1)/len(edited))
            st.success("Atualizado!")
            st.rerun()
    else: st.info("Sem apostas.")

# ==============================================================================
# 5. CAIXA
# ==============================================================================
elif menu == "💰 Depósitos e Saques":
    st.title("Fluxo de Caixa")
    df_b = carregar_bancas()
    if not df_b.empty:
        with st.form("cx"):
            nom = st.selectbox("Banca", df_b['nome'])
            bid = int(df_b[df_b['nome']==nom]['id'].values[0])
            tp = st.radio("Tipo", ["Deposito", "Saque"], horizontal=True)
            val = st.number_input("Valor", 1.0)
            dt = st.date_input("Data")
            if st.form_submit_button("Lançar"):
                supabase.table("transacoes").insert({"banca_id": bid, "tipo": tp, "valor": val, "data": str(dt)}).execute()
                st.success("Sucesso!")

# ==============================================================================
# 6. DASHBOARD
# ==============================================================================
elif menu == "📊 Dashboard Analítico":
    st.title("Dashboard")
    df = carregar_apostas()
    if not df.empty:
        resolvidas = df[~df['resultado'].isin(['Em Aberto', 'Pendente'])]
        lucro = resolvidas['lucro'].sum()
        roi = (lucro / resolvidas['stake'].sum() * 100) if resolvidas['stake'].sum() > 0 else 0
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Lucro Total", f"R$ {lucro:.2f}")
        k2.metric("ROI Geral", f"{roi:.2f}%")
        k3.metric("Entradas Resolvidas", len(resolvidas))
        
        if not resolvidas.empty:
            resolvidas = resolvidas.sort_values('data')
            resolvidas['acumulado'] = resolvidas['lucro'].cumsum()
            st.markdown("### 📈 Curva de Crescimento")
            st.plotly_chart(px.line(resolvidas, x='data', y='acumulado', markers=True), use_container_width=True)
