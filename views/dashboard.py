import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from datetime import datetime, date, timedelta
import calendar

# --- CONFIGURAÇÃO SUPABASE ---
URL = "https://suhpdrqviuzrvygyhxhl.supabase.co"
KEY = "sb_publishable_pM5xDBpqZzo7h5SQqiFcfQ_ixbbydIB"
supabase = create_client(URL, KEY)

def carregar_tudo():
    try:
        res_a = supabase.table("apostas").select("*").execute()
        res_b = supabase.table("bancas").select("*").execute()
        res_m = supabase.table("movimentacoes").select("*").execute()
        return pd.DataFrame(res_a.data), pd.DataFrame(res_b.data), pd.DataFrame(res_m.data)
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def mostrar_dashboard():
    st.markdown("""
        <style>
            [data-testid="stMetricValue"] { color: #002b5c !important; font-weight: bold; font-size: 28px; }
            [data-testid="stMetricLabel"] { color: #1a1a1a !important; font-weight: 500; }
            .stSubheader { color: #002b5c !important; }
        </style>
    """, unsafe_allow_html=True)

    st.title("📊 Dashboard de Performance")
    df_ap, df_ba, df_mov = carregar_tudo()

    if df_ba.empty:
        st.warning("Cadastre uma banca para ver os gráficos.")
        return

    if not df_ap.empty:
        df_ap['data'] = pd.to_datetime(df_ap['data']).dt.tz_localize(None)

    # --- FILTROS ---
    c_f1, c_f2 = st.columns(2)
    with c_f1:
        banca_sel = st.selectbox("Filtrar por Banca", ["Todas"] + df_ba["nome"].tolist())
    
    with c_f2:
        # Filtro de Data por Intervalo
        data_min = df_ap['data'].min().date() if not df_ap.empty else date.today() - timedelta(days=30)
        data_max = date.today()
        periodo = st.date_input("Filtrar Período", value=(data_min, data_max))

    # Lógica de aplicação do filtro de data
    df_f = df_ap.copy()
    if isinstance(periodo, tuple) and len(periodo) == 2:
        start_date, end_date = periodo
        df_f = df_f[(df_f['data'].dt.date >= start_date) & (df_f['data'].dt.date <= end_date)]

    # --- LÓGICA DE SALDO ---
    if banca_sel != "Todas":
        row_banca = df_ba[df_ba["nome"] == banca_sel]
        id_banca = row_banca["id"].iloc[0]
        s_base = row_banca["saldo_inicial"].iloc[0]
        df_f = df_f[df_f['banca_nome'] == banca_sel]
        
        if not df_mov.empty:
            movs = df_mov[df_mov['banca_id'] == id_banca]
            aportes = movs[movs['tipo'] == 'Aporte']['valor'].sum()
            saques = movs[movs['tipo'] == 'Saque']['valor'].sum()
            s_ini = s_base + aportes - saques
        else:
            s_ini = s_base
    else:
        s_base_total = df_ba["saldo_inicial"].sum()
        if not df_mov.empty:
            aportes = df_mov[df_mov['tipo'] == 'Aporte']['valor'].sum()
            saques = df_mov[df_mov['tipo'] == 'Saque']['valor'].sum()
            s_ini = s_base_total + aportes - saques
        else:
            s_ini = s_base_total

    # --- CÁLCULOS PRINCIPAIS ---
    lucro_total = df_f['lucro'].sum() if not df_f.empty else 0
    greens_df = df_f[df_f['status'].str.contains('Green', na=False)]
    reds_df = df_f[df_f['status'].str.contains('Red', na=False)]
    devolvidas_df = df_f[df_f['status'].str.contains('Devolvida', na=False)]
    
    total_apostas = len(df_f)
    win_rate = (len(greens_df) / total_apostas * 100) if total_apostas > 0 else 0
    odd_media_greens = greens_df['odd'].mean() if not greens_df.empty else 0

    # --- MÉTRICAS DE TOPO ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Saldo Atualizado", f"R$ {s_ini + lucro_total:.2f}")
    c2.metric("Lucro Líquido", f"R$ {lucro_total:.2f}")
    c3.metric("Win Rate", f"{win_rate:.1f}%")

    # --- RELATÓRIO DO PERÍODO ---
    st.divider()
    st.subheader(f"📋 Relatório Detalhado do Período")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Total Entradas", total_apostas)
    r2.metric("Greens ✅", len(greens_df))
    r3.metric("Reds ❌", len(reds_df))
    r4.metric("Devolvidas 🔄", len(devolvidas_df))
    
    # --- GRÁFICOS ---
    if not df_f.empty:
        st.divider()
        # Gráfico de Evolução
        df_ev = df_f.sort_values('data')
        df_ev['Evolução'] = s_ini + df_ev['lucro'].cumsum()
        st.plotly_chart(px.line(df_ev, x='data', y='Evolução', title="Curva de Património no Período", markers=True), use_container_width=True)

        # Gráfico de Melhores e Piores Métodos (Top 5 cada)
        st.subheader("🏆 Top 5 Melhores vs 📉 Top 5 Piores Métodos")
        df_met = df_f.groupby('metodo')['lucro'].sum().reset_index()
        
        melhores = df_met.nlargest(5, 'lucro')
        piores = df_met.nsmallest(5, 'lucro')
        df_top10 = pd.concat([melhores, piores]).drop_duplicates().sort_values(by="lucro", ascending=False)
        
        fig_met = px.bar(
            df_top10, 
            x='metodo', 
            y='lucro', 
            color='lucro',
            text_auto='.2f',
            title="Performance por Método (Extremos)",
            color_continuous_scale="RdYlGn"
        )
        st.plotly_chart(fig_met, use_container_width=True)
        
        # Sugestão de Adição: Distribuição de Odds
        st.divider()
        st.subheader("🎯 Distribuição de Odds dos Greens")
        fig_odd = px.histogram(greens_df, x="odd", nbins=10, title="Frequência de Odds em Greens", color_discrete_sequence=['green'])
        st.plotly_chart(fig_odd, use_container_width=True)

    else:
        st.info("Sem dados para o período selecionado.")

# Sugestão extra para o Luciano:
# Seria legal adicionar uma coluna no DataFrame final mostrando o ROI (Retorno sobre Investimento)
# de cada método. Se quiser, posso implementar isso no próximo passo.
