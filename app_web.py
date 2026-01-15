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

# --- FUNÇÕES AUXILIARES ---
@st.cache_data
def carregar_dados_csv():
    try:
        # Lê o CSV
        df = pd.read_csv("dados_25_26.csv", sep=None, engine='python')
        
        # Padroniza nomes das colunas (remove espaços, minúsculo)
        # Ex: "Gols_Mandante_FT" vira "gols_mandante_ft"
        df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
        
        # Garante que colunas numéricas sejam números (evita erro de string)
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
                
        return df
    except Exception as e:
        # st.error(f"Erro ao ler CSV: {e}") # Descomente para debug
        return pd.DataFrame()

def calcular_lucro_real(row):
    status = str(row['resultado']).strip().lower()
    odd = float(row['odd'])
    stake = float(row['stake'])
    
    if status == 'green':
        return (stake * odd) - stake
    elif status == 'meio green':
        return ((stake * odd) - stake) / 2
    elif status == 'red':
        return -stake
    elif status == 'meio red':
        return -stake / 2
    else:
        return 0.0

def carregar_bancas():
    try:
        res = supabase.table("bancas").select("*").execute()
        return pd.DataFrame(res.data)
    except:
        return pd.DataFrame()

def carregar_apostas():
    try:
        res = supabase.table("apostas").select("*, bancas(nome)").execute()
        df = pd.DataFrame(res.data)
        if not df.empty and 'data' in df.columns:
            df['data'] = pd.to_datetime(df['data']).dt.date
            # Recalcular lucro se necessário
            df['lucro_calc'] = df.apply(calcular_lucro_real, axis=1)
            # Extrair nome da banca do objeto aninhado se necessário (depende da resposta do Supabase)
            # Geralmente vem algo como {'nome': 'Bet365'} na coluna 'bancas'
        return df
    except:
        return pd.DataFrame()

df_csv = carregar_dados_csv()

# --- CSS PERSONALIZADO ---
st.markdown("""
    <style>
    .stMetric { background-color: #1e2130; padding: 10px; border-radius: 8px; border: 1px solid #444; }
    div[data-testid="stMetricValue"] { font-size: 20px; color: #00e676; }
    div[data-testid="stMetricLabel"] { font-size: 14px; color: #bbb; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO LATERAL ---
st.sidebar.title("🚀 Banca Master Pro")
menu = st.sidebar.radio("Menu", [
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
        nome_banca = st.text_input("Nome da Nova Banca (ex: Bet365, Pinnacle)")
        if st.form_submit_button("Criar Banca"):
            if nome_banca:
                try:
                    supabase.table("bancas").insert({"nome": nome_banca}).execute()
                    st.success(f"Banca '{nome_banca}' criada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao criar: {e}")
    
    st.divider()
    st.subheader("Bancas Existentes")
    df_bancas = carregar_bancas()
    
    if not df_bancas.empty:
        for index, row in df_bancas.iterrows():
            c1, c2 = st.columns([4, 1])
            c1.write(f"🏦 **{row['nome']}** (ID: {row['id']})")
            if c2.button("Excluir", key=f"del_{row['id']}"):
                try:
                    supabase.table("bancas").delete().eq("id", row['id']).execute()
                    st.success("Banca excluída.")
                    st.rerun()
                except:
                    st.error("Não é possível excluir banca que possui histórico.")
    else:
        st.info("Nenhuma banca cadastrada.")

# ==============================================================================
# 2. ANÁLISE DE TIMES (COM SUAS COLUNAS NOVAS)
# ==============================================================================
elif menu == "⚽ Análise de Times":
    st.title("🔎 Scout e Estatísticas")
    
    if df_csv.empty:
        st.warning("Arquivo CSV não carregado ou colunas não reconhecidas.")
    else:
        # Filtros
        c1, c2, c3, c4 = st.columns(4)
        paises = sorted(df_csv['pais'].unique())
        pais_sel = c1.selectbox("País", paises)
        
        ligas = sorted(df_csv[df_csv['pais'] == pais_sel]['divisao'].unique())
        liga_sel = c2.selectbox("Liga", ligas)
        
        times_mandante = sorted(df_csv[(df_csv['pais'] == pais_sel) & (df_csv['divisao'] == liga_sel)]['mandante'].unique())
        mandante_sel = c3.selectbox("Mandante", times_mandante)
        
        # Filtra visitantes, removendo o mandante da lista
        times_visitante = sorted(df_csv[(df_csv['pais'] == pais_sel) & (df_csv['divisao'] == liga_sel) & (df_csv['mandante'] != mandante_sel)]['visitante'].unique())
        if not times_visitante: times_visitante = [t for t in times_mandante if t != mandante_sel]
        
        visitante_sel = c4.selectbox("Visitante", times_visitante)
        
        st.divider()
        st.subheader(f"⚔️ Confronto: {mandante_sel} x {visitante_sel}")
        
        # --- Lógica de Estatísticas Específica ---
        
        # 1. Dados do Mandante JOGANDO EM CASA
        df_home = df_csv[df_csv['mandante'] == mandante_sel]
        jogos_home = len(df_home)
        
        # 2. Dados do Visitante JOGANDO FORA
        df_away = df_csv[df_csv['visitante'] == visitante_sel]
        jogos_away = len(df_away)
        
        if jogos_home > 0 and jogos_away > 0:
            # --- CÁLCULO DE PROBABILIDADES ---
            # Home: Vitórias em casa
            home_wins = len(df_home[df_home['gols_mandante_ft'] > df_home['gols_visitante_ft']])
            home_draws = len(df_home[df_home['gols_mandante_ft'] == df_home['gols_visitante_ft']])
            home_loss = len(df_home[df_home['gols_mandante_ft'] < df_home['gols_visitante_ft']])
            
            # Away: Vitórias fora
            away_wins = len(df_away[df_away['gols_visitante_ft'] > df_away['gols_mandante_ft']])
            away_draws = len(df_away[df_away['gols_visitante_ft'] == df_away['gols_mandante_ft']])
            away_loss = len(df_away[df_away['gols_visitante_ft'] < df_away['gols_mandante_ft']])
            
            # Médias Ponderadas (Simplificadas)
            prob_home = ((home_wins / jogos_home) * 100)
            prob_away = ((away_wins / jogos_away) * 100)
            # Empate é uma média das taxas de empate de ambos
            prob_draw = (((home_draws / jogos_home) + (away_draws / jogos_away)) / 2) * 100
            
            # Ajuste para somar 100% (Normalização simples)
            total_prob = prob_home + prob_away + prob_draw
            p_h = (prob_home / total_prob) * 100
            p_a = (prob_away / total_prob) * 100
            p_d = (prob_draw / total_prob) * 100
            
            # Exibir Probabilidades
            st.markdown("##### 🎲 Probabilidades (Baseado no histórico Casa/Fora)")
            col_p1, col_p2, col_p3 = st.columns(3)
            col_p1.metric(f"Vitória {mandante_sel}", f"{p_h:.1f}%")
            col_p2.metric("Empate", f"{p_d:.1f}%")
            col_p3.metric(f"Vitória {visitante_sel}", f"{p_a:.1f}%")
            
            st.divider()
            
            # --- COMPARAÇÃO DE MÉDIAS ---
            st.markdown("##### 📊 Comparativo Estatístico (Médias por Jogo)")
            
            # Montar Tabela de Comparação
            stats_data = {
                "Métrica": ["Gols Feitos FT", "Gols Sofridos FT", "Gols Feitos HT", "Gols Sofridos HT", 
                            "Finalizações", "Chutes ao Gol", "Cantos A favor", "Cartões Amarelos"],
                f"{mandante_sel} (Casa)": [
                    df_home['gols_mandante_ft'].mean(),
                    df_home['gols_visitante_ft'].mean(),
                    df_home['gols_mandante_ht'].mean(),
                    df_home['gols_visitante_ht'].mean(),
                    df_home['mandante_finalizacoes'].mean() if 'mandante_finalizacoes' in df_home else 0,
                    df_home['mandante_chute_ao_gol'].mean() if 'mandante_chute_ao_gol' in df_home else 0,
                    df_home['mandante_cantos'].mean(),
                    df_home['mandante_cartao_amarelo'].mean()
                ],
                f"{visitante_sel} (Fora)": [
                    df_away['gols_visitante_ft'].mean(),
                    df_away['gols_mandante_ft'].mean(),
                    df_away['gols_visitante_ht'].mean(),
                    df_away['gols_mandante_ht'].mean(),
                    df_away['visitante_finalizacoes'].mean() if 'visitante_finalizacoes' in df_away else 0,
                    df_away['visitante_chute_ao_gol'].mean() if 'visitante_chute_ao_gol' in df_away else 0,
                    df_away['visitante_cantos'].mean(),
                    df_away['visitante_cartao_amarelo'].mean()
                ]
            }
            
            df_compare = pd.DataFrame(stats_data)
            st.dataframe(df_compare.style.format({f"{mandante_sel} (Casa)": "{:.2f}", f"{visitante_sel} (Fora)": "{:.2f}"}), use_container_width=True)
            
            # --- FORMA RECENTE ---
            c_f1, c_f2 = st.columns(2)
            
            with c_f1:
                st.subheader(f"Últimos 5 em Casa: {mandante_sel}")
                last5_home = df_home.tail(5)[['data', 'visitante', 'gols_mandante_ft', 'gols_visitante_ft']].copy()
                st.dataframe(last5_home, hide_index=True)
                
            with c_f2:
                st.subheader(f"Últimos 5 Fora: {visitante_sel}")
                last5_away = df_away.tail(5)[['data', 'mandante', 'gols_mandante_ft', 'gols_visitante_ft']].copy() # Mostra placar sempre mandante x visitante para nao confundir
                st.dataframe(last5_away, hide_index=True)

        else:
            st.warning("Dados insuficientes para um dos times nesta condição (Casa/Fora).")

# ==============================================================================
# 3. REGISTRAR APOSTA
# ==============================================================================
elif menu == "📝 Registrar Aposta":
    st.title("Novo Registro")
    
    df_bancas = carregar_bancas()
    if df_bancas.empty:
        st.error("Cadastre uma banca primeiro na aba 'Minhas Bancas'.")
    else:
        banca_opcoes = dict(zip(df_bancas['nome'], df_bancas['id']))
        banca_nome = st.selectbox("Selecione a Banca", list(banca_opcoes.keys()))
        banca_id_sel = banca_opcoes[banca_nome]
        
        entrada_manual = st.checkbox("Entrada Manual (Jogo fora do CSV?)")
        
        with st.form("form_aposta", clear_on_submit=True):
            col1, col2 = st.columns(2)
            data_aposta = col1.date_input("Data do Evento")
            
            pais, liga, mandante, visitante = "", "", "", ""
            
            if not entrada_manual and not df_csv.empty:
                paises = sorted(df_csv['pais'].unique())
                pais = col2.selectbox("País", paises)
                ligas = sorted(df_csv[df_csv['pais'] == pais]['divisao'].unique())
                liga = col1.selectbox("Liga", ligas)
                times = sorted(df_csv[(df_csv['pais'] == pais) & (df_csv['divisao'] == liga)]['mandante'].unique())
                mandante = col2.selectbox("Mandante", times)
                visitante = col1.selectbox("Visitante", [t for t in times if t != mandante])
            else:
                pais = col2.text_input("País")
                liga = col1.text_input("Liga")
                mandante = col2.text_input("Mandante")
                visitante = col1.text_input("Visitante")
            
            st.divider()
            c3, c4, c5 = st.columns(3)
            mercado = c3.text_input("Mercado (ex: Over 2.5)")
            odd = c4.number_input("Odd", min_value=1.01, step=0.01)
            stake = c5.number_input("Stake (R$)", min_value=1.0)
            
            resultado = st.selectbox("Resultado Final", ["Em Aberto", "Green", "Meio Green", "Red", "Meio Red", "Anulada"])
            
            if st.form_submit_button("✅ SALVAR APOSTA"):
                try:
                    lucro_inicial = 0
                    if resultado.lower() != 'em aberto':
                        row_sim = {'resultado': resultado, 'odd': odd, 'stake': stake}
                        lucro_inicial = calcular_lucro_real(row_sim)
                    
                    dados = {
                        "banca_id": int(banca_id_sel),
                        "data": str(data_aposta),
                        "pais": pais, "liga": liga, "mandante": mandante, "visitante": visitante,
                        "mercado": mercado, "odd": float(odd), "stake": float(stake),
                        "resultado": resultado,
                        "manual": entrada_manual,
                        "lucro": float(lucro_inicial)
                    }
                    supabase.table("apostas").insert(dados).execute()
                    st.success("Aposta registrada com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# ==============================================================================
# 4. HISTÓRICO DE APOSTAS
# ==============================================================================
elif menu == "📂 Histórico de Apostas":
    st.title("Histórico Geral")
    
    df_apostas = carregar_apostas()
    
    if not df_apostas.empty:
        # Filtro de Data
        c1, c2 = st.columns(2)
        dt_ini = c1.date_input("De", value=datetime.today() - timedelta(days=30))
        dt_fim = c2.date_input("Até", value=datetime.today())
        
        # Filtros
        mask = (df_apostas['data'] >= dt_ini) & (df_apostas['data'] <= dt_fim)
        df_filtered = df_apostas.loc[mask].copy()
        
        st.info("💡 Edite o 'Resultado' abaixo e clique no botão para recalcular o lucro.")
        
        column_config = {
            "resultado": st.column_config.SelectboxColumn(
                "Resultado",
                options=["Em Aberto", "Green", "Meio Green", "Red", "Meio Red", "Anulada"],
                required=True
            ),
            "lucro": st.column_config.NumberColumn("Lucro (R$)", format="R$ %.2f", disabled=True),
            "banca_id": st.column_config.TextColumn("ID Banca", disabled=True),
        }
        
        cols_show = ['id', 'data', 'mandante', 'visitante', 'mercado', 'odd', 'stake', 'resultado', 'lucro']
        
        edited_df = st.data_editor(
            df_filtered[cols_show], 
            column_config=column_config, 
            hide_index=True,
            use_container_width=True,
            key="editor_historico"
        )
        
        if st.button("💾 Atualizar Alterações e Recalcular Lucro"):
            try:
                for index, row in edited_df.iterrows():
                    novo_lucro = calcular_lucro_real(row)
                    supabase.table("apostas").update({
                        "resultado": row['resultado'],
                        "lucro": novo_lucro
                    }).eq("id", row['id']).execute()
                
                st.success("Histórico atualizado!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao atualizar: {e}")
            
    else:
        st.info("Nenhuma aposta encontrada.")

# ==============================================================================
# 5. DEPÓSITOS E SAQUES
# ==============================================================================
elif menu == "💰 Depósitos e Saques":
    st.title("Fluxo de Caixa")
    
    df_bancas = carregar_bancas()
    if df_bancas.empty:
        st.warning("Cadastre uma banca primeiro.")
    else:
        with st.form("form_transacao"):
            banca_dict = dict(zip(df_bancas['nome'], df_bancas['id']))
            banca_sel = st.selectbox("Selecione a Banca", list(banca_dict.keys()))
            tipo = st.radio("Tipo", ["Deposito", "Saque"], horizontal=True)
            valor = st.number_input("Valor (R$)", min_value=0.01, step=10.0)
            data_t = st.date_input("Data da Transação")
            
            if st.form_submit_button("Confirmar Transação"):
                try:
                    supabase.table("transacoes").insert({
                        "banca_id": banca_dict[banca_sel],
                        "tipo": tipo,
                        "valor": valor,
                        "data": str(data_t)
                    }).execute()
                    st.success(f"{tipo} de R$ {valor} registrado!")
                except Exception as e:
                    st.error(f"Erro: {e}")

# ==============================================================================
# 6. DASHBOARD ANALÍTICO
# ==============================================================================
elif menu == "📊 Dashboard Analítico":
    st.title("Dashboard Pro")
    
    df_bancas = carregar_bancas()
    df_apostas = carregar_apostas()
    
    try:
        res_trans = supabase.table("transacoes").select("*").execute()
        df_trans = pd.DataFrame(res_trans.data)
    except:
        df_trans = pd.DataFrame()
    
    if df_bancas.empty:
        st.warning("Sem dados.")
    else:
        c1, c2, c3 = st.columns(3)
        banca_filtro = c1.selectbox("Filtrar Banca", ["Todas"] + list(df_bancas['nome']))
        d1 = c2.date_input("Início", value=datetime.today() - timedelta(days=90))
        d2 = c3.date_input("Fim", value=datetime.today())
        
        if banca_filtro != "Todas":
            id_banca = df_bancas[df_bancas['nome'] == banca_filtro]['id'].values[0]
            df_apostas = df_apostas[df_apostas['banca_id'] == id_banca] if not df_apostas.empty else df_apostas
            df_trans = df_trans[df_trans['banca_id'] == id_banca] if not df_trans.empty else df_trans
            
        if not df_apostas.empty:
            df_apostas = df_apostas[(df_apostas['data'] >= d1) & (df_apostas['data'] <= d2)]
            
        if not df_apostas.empty:
            resolvidas = df_apostas[~df_apostas['resultado'].isin(['Em Aberto', 'Pendente', 'Anulada'])]
            
            lucro_total = resolvidas['lucro'].sum()
            investido = resolvidas['stake'].sum()
            roi = (lucro_total / investido * 100) if investido > 0 else 0
            
            greens = len(resolvidas[resolvidas['resultado'].str.contains('Green', case=False)])
            total_res = len(resolvidas)
            win_rate = (greens / total_res * 100) if total_res > 0 else 0
            
            saldo_atual = 0
            if not df_trans.empty:
                depositos = df_trans[df_trans['tipo'] == 'Deposito']['valor'].sum()
                saques = df_trans[df_trans['tipo'] == 'Saque']['valor'].sum()
                saldo_atual += (depositos - saques)
            saldo_atual += lucro_total
            
            # KPIs
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Lucro no Período", f"R$ {lucro_total:,.2f}", delta=f"{roi:.1f}% ROI")
            k2.metric("Saldo Estimado", f"R$ {saldo_atual:,.2f}")
            k3.metric("Win Rate", f"{win_rate:.1f}%", f"{greens}/{total_res}")
            k4.metric("Apostas", len(df_apostas))
            
            st.divider()
            
            # Gráfico de Evolução
            resolvidas_sorted = resolvidas.sort_values('data')
            resolvidas_sorted['lucro_acumulado'] = resolvidas_sorted['lucro'].cumsum()
            
            fig_line = px.line(resolvidas_sorted, x='data', y='lucro_acumulado', title='Curva de Lucro', markers=True)
            fig_line.update_traces(line_color='#00e676')
            st.plotly_chart(fig_line, use_container_width=True)
            
            # Gráficos de Barras
            col_g1, col_g2 = st.columns(2)
            
            lucro_mercado = resolvidas.groupby('mercado')['lucro'].sum().reset_index().sort_values('lucro', ascending=False)
            fig_bar1 = px.bar(lucro_mercado, x='mercado', y='lucro', title='Lucro por Mercado', color='lucro', color_continuous_scale='RdYlGn')
            col_g1.plotly_chart(fig_bar1, use_container_width=True)
            
            lucro_liga = resolvidas.groupby('liga')['lucro'].sum().reset_index().sort_values('lucro', ascending=False)
            fig_bar2 = px.bar(lucro_liga, x='liga', y='lucro', title='Lucro por Liga', color='lucro', color_continuous_scale='RdYlGn')
            col_g2.plotly_chart(fig_bar2, use_container_width=True)
            
        else:
            st.info("Sem dados de apostas para o período selecionado.")
