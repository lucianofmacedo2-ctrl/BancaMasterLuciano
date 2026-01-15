import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client, Client
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Banca Master Pro", layout="wide", initial_sidebar_state="expanded")

# --- CONEXÃO SUPABASE ---
@st.cache_resource
def conectar_supabase():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key)
    except:
        st.error("Erro nos Secrets do Supabase.")
        return None

supabase = conectar_supabase()

# --- FUNÇÕES ---

# Função blindada para calcular lucro
def calcular_lucro_real(resultado, odd, stake):
    try:
        status = str(resultado).strip().lower()
        odd_val = float(odd)
        stake_val = float(stake)
        
        if status == 'green':
            return (stake_val * odd_val) - stake_val
        elif status == 'meio green':
            return ((stake_val * odd_val) - stake_val) / 2
        elif status == 'red':
            return -stake_val
        elif status == 'meio red':
            return -stake_val / 2
        elif status == 'devolvida' or status == 'anulada':
            return 0.0
        else:
            return 0.0 # Em Aberto ou Pendente
    except:
        return 0.0

def carregar_bancas():
    try:
        res = supabase.table("bancas").select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

def carregar_apostas():
    try:
        # Trazemos tudo para garantir
        res = supabase.table("apostas").select("*").execute()
        df = pd.DataFrame(res.data)
        
        if not df.empty:
            # Converter data para datetime
            if 'data' in df.columns:
                df['data'] = pd.to_datetime(df['data']).dt.date
            
            # Garantir que numeros sao numeros
            df['odd'] = pd.to_numeric(df['odd'])
            df['stake'] = pd.to_numeric(df['stake'])
            df['lucro'] = pd.to_numeric(df['lucro'])
            
        return df
    except:
        return pd.DataFrame()

@st.cache_data
def carregar_dados_csv():
    try:
        df = pd.read_csv("dados_25_26.csv", sep=None, engine='python')
        df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
        # Conversão forçada de colunas numéricas
        cols_stats = ['gols_mandante_ft', 'gols_visitante_ft', 'gols_mandante_ht', 'gols_visitante_ht',
                      'mandante_cantos', 'visitante_cantos']
        for c in cols_stats:
            if c in df.columns: df[c] = pd.to_numeric(df[c], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

df_csv = carregar_dados_csv()

# --- CSS ---
st.markdown("""<style>.stMetric { background-color: #1e2130; padding: 10px; border-radius: 8px; border: 1px solid #444; }</style>""", unsafe_allow_html=True)

# --- MENU ---
st.sidebar.title("🚀 Banca Master Pro")
menu = st.sidebar.radio("Menu", ["📊 Dashboard Analítico", "⚽ Análise de Times", "📝 Registrar Aposta", "📂 Histórico de Apostas", "💰 Depósitos e Saques", "🏦 Minhas Bancas"])

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
            c1.write(f"🏦 {r['nome']}")
            if c2.button("Excluir", key=r['id']):
                st.error("Para excluir, apague primeiro as apostas dessa banca.")

# ==============================================================================
# 2. ANÁLISE DE TIMES
# ==============================================================================
elif menu == "⚽ Análise de Times":
    st.title("🔎 Scout e Estatísticas")
    if df_csv.empty:
        st.warning("CSV não carregado.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        p = c1.selectbox("País", sorted(df_csv['pais'].unique()))
        l = c2.selectbox("Liga", sorted(df_csv[df_csv['pais']==p]['divisao'].unique()))
        tm = c3.selectbox("Mandante", sorted(df_csv[(df_csv['pais']==p)&(df_csv['divisao']==l)]['mandante'].unique()))
        tv_list = sorted(df_csv[(df_csv['pais']==p)&(df_csv['divisao']==l)&(df_csv['mandante']!=tm)]['visitante'].unique())
        if not tv_list: tv_list = ["Selecione"]
        tv = c4.selectbox("Visitante", tv_list)
        
        st.divider()
        st.subheader(f"{tm} x {tv}")
        
        # Filtros
        home = df_csv[df_csv['mandante'] == tm]
        away = df_csv[df_csv['visitante'] == tv]
        
        if not home.empty and not away.empty:
            col_a, col_b = st.columns(2)
            
            # Médias
            with col_a:
                st.info(f"🏠 {tm} (Em Casa)")
                media_gf = home['gols_mandante_ft'].mean()
                media_gs = home['gols_visitante_ft'].mean()
                st.write(f"Média Gols Feitos: **{media_gf:.2f}**")
                st.write(f"Média Gols Sofridos: **{media_gs:.2f}**")
                
            with col_b:
                st.info(f"✈️ {tv} (Fora)")
                media_gf_a = away['gols_visitante_ft'].mean()
                media_gs_a = away['gols_mandante_ft'].mean()
                st.write(f"Média Gols Feitos: **{media_gf_a:.2f}**")
                st.write(f"Média Gols Sofridos: **{media_gs_a:.2f}**")

# ==============================================================================
# 3. REGISTRAR APOSTA
# ==============================================================================
elif menu == "📝 Registrar Aposta":
    st.title("Novo Registro")
    df_bancas = carregar_bancas()
    
    if df_bancas.empty:
        st.warning("Crie uma banca primeiro.")
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
                st.success(f"Salvo! Lucro calculado: R$ {lucro:.2f}")

# ==============================================================================
# 4. HISTÓRICO (AQUI ESTAVA O PROBLEMA)
# ==============================================================================
elif menu == "📂 Histórico de Apostas":
    st.title("Histórico e Edição")
    
    df = carregar_apostas()
    
    if not df.empty:
        # Mostra tabela editável
        st.write("📝 **Altere o 'Resultado' abaixo e clique no botão para recalcular:**")
        
        # Configuração das colunas
        col_config = {
            "resultado": st.column_config.SelectboxColumn("Resultado", options=["Em Aberto", "Green", "Meio Green", "Red", "Meio Red", "Anulada"], required=True),
            "lucro": st.column_config.NumberColumn("Lucro", disabled=True),
            "id": st.column_config.TextColumn("ID", disabled=True), # ID visível para garantir tracking
        }
        
        # Filtro de colunas para exibir
        cols = ['id', 'data', 'mandante', 'visitante', 'mercado', 'odd', 'stake', 'resultado', 'lucro']
        
        # O Editor
        edited = st.data_editor(df[cols], column_config=col_config, use_container_width=True, hide_index=True, key="editor_hist")
        
        if st.button("💾 SALVAR ALTERAÇÕES E RECALCULAR"):
            progresso = st.progress(0)
            total = len(edited)
            
            for i, row in edited.iterrows():
                # 1. Recalcula a matemática no Python
                novo_lucro = calcular_lucro_real(row['resultado'], row['odd'], row['stake'])
                
                # 2. Atualiza no Supabase
                try:
                    supabase.table("apostas").update({
                        "resultado": row['resultado'],
                        "lucro": novo_lucro
                    }).eq("id", row['id']).execute()
                except Exception as e:
                    st.error(f"Erro ao atualizar ID {row['id']}: Verifique se o RLS (Policies) permite UPDATE no Supabase.")
                
                progresso.progress((i + 1) / total)
            
            st.success("✅ Tudo atualizado!")
            st.rerun()
            
    else:
        st.info("Nenhuma aposta encontrada.")

# ==============================================================================
# 5. DEPÓSITOS E SAQUES
# ==============================================================================
elif menu == "💰 Depósitos e Saques":
    st.title("Caixa")
    df_b = carregar_bancas()
    if not df_b.empty:
        with st.form("cx"):
            nom = st.selectbox("Banca", df_b['nome'])
            bid = int(df_b[df_b['nome']==nom]['id'].values[0])
            tp = st.radio("Tipo", ["Deposito", "Saque"])
            val = st.number_input("Valor", 1.0)
            dt = st.date_input("Data")
            if st.form_submit_button("Lançar"):
                supabase.table("transacoes").insert({"banca_id": bid, "tipo": tp, "valor": val, "data": str(dt)}).execute()
                st.success("Lançado!")

# ==============================================================================
# 6. DASHBOARD
# ==============================================================================
elif menu == "📊 Dashboard Analítico":
    st.title("Dashboard")
    df = carregar_apostas()
    if not df.empty:
        resolvidas = df[~df['resultado'].isin(['Em Aberto', 'Pendente'])]
        lucro = resolvidas['lucro'].sum()
        roi = (lucro / resolvidas['stake'].sum() * 100) if not resolvidas.empty else 0
        
        k1, k2, k3 = st.columns(3)
        k1.metric("Lucro Total", f"R$ {lucro:.2f}")
        k2.metric("ROI", f"{roi:.2f}%")
        k3.metric("Apostas Resolvidas", len(resolvidas))
        
        # Gráfico
        if not resolvidas.empty:
            resolvidas = resolvidas.sort_values('data')
            resolvidas['acumulado'] = resolvidas['lucro'].cumsum()
            st.plotly_chart(px.line(resolvidas, x='data', y='acumulado', title="Curva de Lucro"), use_container_width=True)
    else:
        st.warning("Sem dados.")
