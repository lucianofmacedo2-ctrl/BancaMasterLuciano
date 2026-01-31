import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client
from datetime import datetime, date, timedelta
import pytz 
import calendar

# --- CONFIGURAÇÃO SUPABASE ---
URL = "https://suhpdrqviuzrvygyhxhl.supabase.co"
KEY = "sb_publishable_pM5xDBpqZzo7h5SQqiFcfQ_ixbbydIB"
supabase = create_client(URL, KEY)

# --- FUSO HORÁRIO ---
brasil_tz = pytz.timezone('America/Sao_Paulo')

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
        # CONVERSÃO DE DATA CORRIGIDA PARA EVITAR TYPEERROR
        df_ap['data'] = pd.to_datetime(df_ap['data'])
        
        # Verifica se a coluna de data já tem fuso horário
        if df_ap['data'].dt.tz is None:
            # Se não tem fuso (naive), localizamos como UTC e depois convertemos para Brasil
            df_ap['data'] = df_ap['data'].dt.tz_localize('UTC').dt.tz_convert(brasil_tz).dt.tz_localize(None)
        else:
            # Se já tem fuso, apenas convertemos para Brasil
            df_ap['data'] = df_ap['data'].dt.tz_convert(brasil_tz).dt.tz_localize(None)

    # --- FILTROS ---
    c_f1, c_f2 = st.columns(2)
    with c_f1:
        banca_sel = st.selectbox("Filtrar por Banca", ["Todas"] + df_ba["nome"].tolist())
    
    with c_f2:
        tipo_filtro = st.radio("Tipo de Filtro de Data:", ["Intervalo", "Dia Único"], horizontal=True)
        
        # Data de hoje correta no Brasil
        hoje_br = datetime.now(brasil_tz).date()
        
        if not df_ap.empty:
            d_min = df_ap['data'].min().date()
            d_max = df_ap['data'].max().date()
            d_max_default = min(d_max, hoje_br)
        else:
            d_min, d_max_default = hoje_br, hoje_br

        if tipo_filtro == "Intervalo":
            periodo = st.date_input("Selecione o Período", value=(d_min, hoje_br))
        else:
            periodo = st.date_input("Selecione o Dia", value=hoje_br)

    # Aplicar Filtro de Data
    df_f = df_ap.copy()
    if tipo_filtro == "Intervalo" and isinstance(periodo, tuple) and len(periodo) == 2:
        df_f = df_f[(df_f['data'].dt.date >= periodo[0]) & (df_f['data'].dt.date <= periodo[1])]
    elif tipo_filtro == "Dia Único":
        df_f = df_f[df_f['data'].dt.date == periodo]

    # --- LÓGICA DE SALDO ---
    if banca_sel != "Todas":
        row_banca = df_ba[df_ba["nome"] == banca_sel]
        id_banca = row_banca["id"].iloc[0]
        s_base = row_banca["saldo_inicial"].iloc[0]
        df_f = df_f[df_f['banca_nome'] == banca_sel]
        
        if not df_mov.empty:
            movs = df_mov[df_mov['banca_id'] == id_banca]
            s_ini = s_base + movs[movs['tipo'] == 'Aporte']['valor'].sum() - movs[movs['tipo'] == 'Saque']['valor'].sum()
        else:
            s_ini = s_base
    else:
        s_base_total = df_ba["saldo_inicial"].sum()
        s_ini = s_base_total + (df_mov[df_mov['tipo'] == 'Aporte']['valor'].sum() if not df_mov.empty else 0) - (df_mov[df_mov['tipo'] == 'Saque']['valor'].sum() if not df_mov.empty else 0)

    # --- CÁLCULOS ---
    lucro_total = df_f['lucro'].sum() if not df_f.empty else 0
    greens_df = df_f[df_f['status'].str.contains('Green', na=False)]
    reds_df = df_f[df_f['status'].str.contains('Red', na=False)]
    
    total_apostas = len(df_f)
    win_rate = (len(greens_df) / total_apostas * 100) if total_apostas > 0 else 0
    odd_media_greens = greens_df['odd'].mean() if not greens_df.empty else 0

    # --- MÉTRICAS DE TOPO ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Saldo Atualizado", f"R$ {s_ini + lucro_total:.2f}")
    c2.metric("Lucro Líquido", f"R$ {lucro_total:.2f}")
    c3.metric("Win Rate", f"{win_rate:.1f}%")

    st.divider()
    st.subheader(f"📋 Resumo do Período")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Entradas", total_apostas)
    r2.metric("Greens ✅", len(greens_df))
    r3.metric("Reds ❌", len(reds_df))
    r4.metric("Odd Média (Greens)", f"{odd_media_greens:.2f}")

    # --- GRÁFICOS ---
    if not df_f.empty:
        df_ev = df_f.sort_values('data')
        df_ev['Evolução'] = s_ini + df_ev['lucro'].cumsum()
        st.plotly_chart(px.line(df_ev, x='data', y='Evolução', title="Curva de Património", markers=True), use_container_width=True)

        st.subheader("🏆 Performance por Método")
        df_met = df_f.groupby('metodo').agg({'lucro': 'sum', 'stake': 'sum'}).reset_index()
        df_met['ROI %'] = (df_met['lucro'] / df_met['stake']) * 100
        
        melhores = df_met.nlargest(5, 'lucro')
        piores = df_met.nsmallest(5, 'lucro')
        df_top10 = pd.concat([melhores, piores]).drop_duplicates().sort_values(by="lucro", ascending=False)
        
        fig_met = px.bar(
            df_top10, x='metodo', y='lucro', color='ROI %',
            text=df_top10['ROI %'].apply(lambda x: f"ROI: {x:.1f}%"),
            title="Lucro por Método e ROI %",
            color_continuous_scale="RdYlGn"
        )
        st.plotly_chart(fig_met, use_container_width=True)

        st.divider()
        st.subheader("🎯 Distribuição de Odds dos Greens")
        fig_odd = px.histogram(greens_df, x="odd", nbins=15, title="Onde estão seus acertos?", color_discrete_sequence=['#002b5c'])
        st.plotly_chart(fig_odd, use_container_width=True)
    else:
        st.info("Nenhuma aposta encontrada para este filtro.")
