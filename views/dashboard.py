import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from datetime import datetime, date
import calendar

# --- CONFIGURAÇÃO SUPABASE ---
URL = "https://suhpdrqviuzrvygyhxhl.supabase.co"
KEY = "sb_publishable_pM5xDBpqZzo7h5SQqiFcfQ_ixbbydIB"
supabase = create_client(URL, KEY)

def carregar_tudo():
    try:
        res_a = supabase.table("apostas").select("*").execute()
        res_b = supabase.table("bancas").select("*").execute()
        return pd.DataFrame(res_a.data), pd.DataFrame(res_b.data)
    except:
        return pd.DataFrame(), pd.DataFrame()

def mostrar_dashboard():
    st.title("📊 Dashboard de Performance")
    df_ap, df_ba = carregar_tudo()

    if df_ba.empty:
        st.warning("Cadastre uma banca para ver os gráficos.")
        return

    # --- FILTROS (BANCA E MÊS) ---
    c_f1, c_f2 = st.columns(2)
    
    with c_f1:
        banca_sel = st.selectbox("Filtrar por Banca", ["Todas"] + df_ba["nome"].tolist())
    
    # Tratamento de Data para o Filtro Mensal
    if not df_ap.empty:
        df_ap['data'] = pd.to_datetime(df_ap['data'])
        meses_disponiveis = df_ap['data'].dt.strftime('%m/%Y').unique().tolist()
        meses_disponiveis.sort(reverse=True)
    else:
        meses_disponiveis = [datetime.now().strftime('%m/%Y')]

    with c_f2:
        mes_sel = st.selectbox("Filtrar por Mês", ["Todos"] + meses_disponiveis)

    # Aplicação dos Filtros
    df_f = df_ap.copy()
    
    if banca_sel != "Todas":
        df_f = df_f[df_f['banca_nome'] == banca_sel]
        s_ini = df_ba[df_ba["nome"] == banca_sel]["saldo_inicial"].iloc[0]
    else:
        s_ini = df_ba["saldo_inicial"].sum()

    if mes_sel != "Todos":
        df_f = df_f[df_f['data'].dt.strftime('%m/%Y') == mes_sel]

    # --- CÁLCULO DE MÉTRICAS ---
    lucro_total = df_f['lucro'].sum() if not df_f.empty else 0
    total_apostas = len(df_f)
    
    # Win Rate
    greens = df_f[df_f['status'].str.contains('Green', na=False)]
    win_rate = (len(greens) / total_apostas * 100) if total_apostas > 0 else 0
    
    # Odd Média dos Greens
    odd_media_greens = greens['odd'].mean() if not greens.empty else 0

    # --- LINHA 1 DE MÉTRICAS (EXISTENTES) ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Saldo Atualizado", f"R$ {s_ini + lucro_total:.2f}")
    c2.metric("Lucro Líquido", f"R$ {lucro_total:.2f}")
    c3.metric("Win Rate", f"{win_rate:.1f}%")

    # --- LINHA 2 DE MÉTRICAS (NOVAS) ---
    st.write("") # Espaçamento
    c4, c5, c6 = st.columns(3)
    
    c4.metric("Quantidade de Apostas", f"{total_apostas}")
    c5.metric("Odd Média (Greens)", f"{odd_media_greens:.2f}")

    # Projeção de Banca Final do Mês
    if mes_sel != "Todos" and not df_f.empty:
        # Extrai mês e ano selecionados
        m_idx, a_idx = map(int, mes_sel.split('/'))
        hoje = date.today()
        
        # Se for o mês atual, calcula dias restantes. Se for mês passado, dias restantes = 0.
        if hoje.month == m_idx and hoje.year == a_idx:
            ultimo_dia = calendar.monthrange(a_idx, m_idx)[1]
            dias_restantes = ultimo_dia - hoje.day
            dias_passados = hoje.day
        else:
            dias_restantes = 0
            dias_passados = calendar.monthrange(a_idx, m_idx)[1]

        lucro_diario = lucro_total / dias_passados if dias_passados > 0 else 0
        projecao_final = (s_ini + lucro_total) + (lucro_diario * dias_restantes)
        c6.metric("Projeção Final do Mês", f"R$ {projecao_final:.2f}", 
                  help="Baseado na média de lucro diário deste mês")
    else:
        c6.metric("Projeção Final do Mês", "Selecione um mês")

    # --- GRÁFICOS ---
    if not df_f.empty:
        st.divider()
        
        # Gráfico de Evolução
        df_ev = df_f.sort_values('data')
        df_ev['Evolução'] = s_ini + df_ev['lucro'].cumsum()
        st.plotly_chart(px.line(df_ev, x='data', y='Evolução', title="Curva de Patrimônio"), use_container_width=True)

        # Gráfico de Métodos
        df_met = df_f.groupby('metodo')['lucro'].sum().reset_index()
        st.plotly_chart(px.bar(df_met, x='metodo', y='lucro', color='lucro', 
                               title="Lucro por Método", color_continuous_scale="RdYlGn"), use_container_width=True)
    else:
        st.info("Aguardando registros de apostas para gerar gráficos.")
