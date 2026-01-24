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
        # Buscando as movimentações de aporte e saque
        res_m = supabase.table("movimentacoes").select("*").execute()
        return pd.DataFrame(res_a.data), pd.DataFrame(res_b.data), pd.DataFrame(res_m.data)
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

def mostrar_dashboard():
    # --- CSS PARA CORES ESCURAS ---
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
        df_ap['data'] = pd.to_datetime(df_ap['data']).dt.tz_localize(None) # Remove timezone para evitar conflitos
    
    # --- FILTROS ---
    c_f1, c_f2 = st.columns(2)
    with c_f1:
        banca_sel = st.selectbox("Filtrar por Banca", ["Todas"] + df_ba["nome"].tolist())
    
    if not df_ap.empty:
        meses_disponiveis = df_ap['data'].dt.strftime('%m/%Y').unique().tolist()
        meses_disponiveis.sort(reverse=True)
    else:
        meses_disponiveis = [datetime.now().strftime('%m/%Y')]

    with c_f2:
        mes_sel = st.selectbox("Filtrar por Mês", ["Todos"] + meses_disponiveis)

    # --- LÓGICA DE SALDO (INCLUINDO APORTES E SAQUES) ---
    df_f = df_ap.copy()
    
    if banca_sel != "Todas":
        row_banca = df_ba[df_ba["nome"] == banca_sel]
        id_banca = row_banca["id"].iloc[0]
        s_base = row_banca["saldo_inicial"].iloc[0]
        
        # Filtra apostas
        df_f = df_f[df_f['banca_nome'] == banca_sel]
        
        # Calcula movimentações da banca específica
        if not df_mov.empty:
            movs = df_mov[df_mov['banca_id'] == id_banca]
            aportes = movs[movs['tipo'] == 'Aporte']['valor'].sum()
            saques = movs[movs['tipo'] == 'Saque']['valor'].sum()
            s_ini = s_base + aportes - saques
        else:
            s_ini = s_base
    else:
        # Soma de todas as bancas + todas as movimentações
        s_base_total = df_ba["saldo_inicial"].sum()
        if not df_mov.empty:
            aportes = df_mov[df_mov['tipo'] == 'Aporte']['valor'].sum()
            saques = df_mov[df_mov['tipo'] == 'Saque']['valor'].sum()
            s_ini = s_base_total + aportes - saques
        else:
            s_ini = s_base_total

    if mes_sel != "Todos":
        df_f = df_f[df_f['data'].dt.strftime('%m/%Y') == mes_sel]

    # --- NOVA LÓGICA DE TEMPO ATIVO ---
    hoje = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    if not df_f.empty:
        data_inicio_operacoes = df_f['data'].min().replace(hour=0, minute=0, second=0, microsecond=0)
        
        if mes_sel != "Todos":
            m_idx, a_idx = map(int, mes_sel.split('/'))
            if hoje.month == m_idx and hoje.year == a_idx:
                dias_passados = (hoje - data_inicio_operacoes).days + 1
                ultimo_dia_mes = calendar.monthrange(a_idx, m_idx)[1]
                data_fim_mes = datetime(a_idx, m_idx, ultimo_dia_mes)
                dias_restantes = (data_fim_mes - hoje).days
            else:
                ultimo_dia_mes = calendar.monthrange(a_idx, m_idx)[1]
                data_fim_mes = datetime(a_idx, m_idx, ultimo_dia_mes)
                dias_passados = (data_fim_mes - data_inicio_operacoes).days + 1
                dias_restantes = 0
        else:
            dias_passados = (df_f['data'].max() - data_inicio_operacoes).days + 1
            dias_restantes = 0
    else:
        dias_passados = 1
        dias_restantes = 0

    # --- CÁLCULOS ---
    total_apostas = len(df_f)
    lucro_total = df_f['lucro'].sum() if not df_f.empty else 0
    greens = df_f[df_f['status'].str.contains('Green', na=False)]
    win_rate = (len(greens) / total_apostas * 100) if total_apostas > 0 else 0
    odd_media_greens = greens['odd'].mean() if not greens.empty else 0
    apostas_por_dia = total_apostas / dias_passados if dias_passados > 0 else 0

    # --- MÉTRICAS ---
    c1, c2, c3 = st.columns(3)
    # Aqui o cálculo agora considera o saldo inicial + aportes/saques + lucro das apostas
    c1.metric("Saldo Atualizado", f"R$ {s_ini + lucro_total:.2f}")
    c2.metric("Lucro Líquido", f"R$ {lucro_total:.2f}")
    c3.metric("Win Rate", f"{win_rate:.1f}%")

    st.write("") 
    c4, c5, c6 = st.columns(3)
    c4.metric("Qtd Apostas", f"{total_apostas}")
    c5.metric("Média Apostas/Dia", f"{apostas_por_dia:.1f}")
    c6.metric("Odd Média (Greens)", f"{odd_media_greens:.2f}")

    # --- PROJEÇÃO FINAL ---
    if mes_sel != "Todos" and dias_restantes > 0 and not df_f.empty:
        st.divider()
        st.subheader(f"🔮 Projeção Baseada no Ritmo Atual ({dias_passados} dias ativos)")
        
        lucro_diario = lucro_total / dias_passados
        lucro_projetado_adicional = lucro_diario * dias_restantes
        banca_final_projetada = (s_ini + lucro_total) + lucro_projetado_adicional
        
        pj1, pj2, pj3 = st.columns(3)
        pj1.metric("Banca Final Esperada", f"R$ {banca_final_projetada:.2f}")
        pj2.metric("Lucro Extra Estimado", f"R$ {lucro_projetado_adicional:.2f}")
        pj3.metric("Entradas Estimadas", f"{int(apostas_por_dia * dias_restantes)} apostas")
        st.caption(f"A projeção assume que manterá a média de {apostas_por_dia:.1f} apostas/dia até o dia {ultimo_dia_mes}.")

    # --- GRÁFICOS ---
    if not df_f.empty:
        st.divider()
        df_ev = df_f.sort_values('data')
        df_ev['Evolução'] = s_ini + df_ev['lucro'].cumsum()
        st.plotly_chart(px.line(df_ev, x='data', y='Evolução', title="Curva de Património"), use_container_width=True)

        df_met = df_f.groupby('metodo')['lucro'].sum().reset_index()
        st.plotly_chart(px.bar(df_met, x='metodo', y='lucro', color='lucro', title="Lucro por Método", color_continuous_scale="RdYlGn"), use_container_width=True)
    else:
        st.info("Sem dados para o período selecionado.")
