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
    # --- CSS PARA ESCURECER AS MÉTRICAS ---
    st.markdown("""
        <style>
            /* Altera a cor do valor da métrica para um azul escuro/marinho */
            [data-testid="stMetricValue"] {
                color: #003366 !important;
                font-weight: bold;
            }
            /* Altera o rótulo da métrica para cinza escuro */
            [data-testid="stMetricLabel"] {
                color: #333333 !important;
            }
        </style>
    """, unsafe_allow_html=True)

    st.title("📊 Dashboard de Performance")
    df_ap, df_ba = carregar_tudo()

    if df_ba.empty:
        st.warning("Cadastre uma banca para ver os gráficos.")
        return

    # --- FILTROS ---
    c_f1, c_f2 = st.columns(2)
    with c_f1:
        banca_sel = st.selectbox("Filtrar por Banca", ["Todas"] + df_ba["nome"].tolist())
    
    if not df_ap.empty:
        df_ap['data'] = pd.to_datetime(df_ap['data'])
        meses_disponiveis = df_ap['data'].dt.strftime('%m/%Y').unique().tolist()
        meses_disponiveis.sort(reverse=True)
    else:
        meses_disponiveis = [datetime.now().strftime('%m/%Y')]

    with c_f2:
        mes_sel = st.selectbox("Filtrar por Mês", ["Todos"] + meses_disponiveis)

    # --- APLICAÇÃO DOS FILTROS ---
    df_f = df_ap.copy()
    if banca_sel != "Todas":
        df_f = df_f[df_f['banca_nome'] == banca_sel]
        s_ini = df_ba[df_ba["nome"] == banca_sel]["saldo_inicial"].iloc[0]
    else:
        s_ini = df_ba["saldo_inicial"].sum()

    if mes_sel != "Todos":
        df_f = df_f[df_f['data'].dt.strftime('%m/%Y') == mes_sel]

    # --- CÁLCULOS ---
    total_apostas = len(df_f)
    lucro_total = df_f['lucro'].sum() if not df_f.empty else 0
    greens = df_f[df_f['status'].str.contains('Green', na=False)]
    win_rate = (len(greens) / total_apostas) if total_apostas > 0 else 0
    odd_media_greens = greens['odd'].mean() if not greens.empty else 0
    
    # Média de Apostas por Dia
    if mes_sel != "Todos":
        m_idx, a_idx = map(int, mes_sel.split('/'))
        hoje = date.today()
        if hoje.month == m_idx and hoje.year == a_idx:
            dias_corridos = hoje.day
        else:
            dias_corridos = calendar.monthrange(a_idx, m_idx)[1]
    else:
        dias_corridos = (df_f['data'].max() - df_f['data'].min()).days + 1 if not df_f.empty else 1
    
    apostas_por_dia = total_apostas / dias_corridos if dias_corridos > 0 else 0

    # --- MÉTRICAS LINHA 1 ---
    c1, c2, c3 = st.columns(3)
    c1.metric("Saldo Atualizado", f"R$ {s_ini + lucro_total:.2f}")
    c2.metric("Lucro Líquido", f"R$ {lucro_total:.2f}")
    c3.metric("Win Rate", f"{win_rate*100:.1f}%")

    # --- MÉTRICAS LINHA 2 ---
    st.write("")
    c4, c5, c6 = st.columns(3)
    c4.metric("Qtd Apostas", f"{total_apostas}")
    c5.metric("Média Apostas/Dia", f"{apostas_por_dia:.1f}")
    c6.metric("Odd Média (Greens)", f"{odd_media_greens:.2f}")

    # --- PROJEÇÃO MATEMÁTICA ---
    st.divider()
    if mes_sel != "Todos" and not df_f.empty:
        ultimo_dia = calendar.monthrange(a_idx, m_idx)[1]
        dias_restantes = ultimo_dia - dias_corridos
        
        # Valor médio de cada aposta (stake média)
        stake_media = df_f['valor_aposta'].mean() if 'valor_aposta' in df_f.columns else 0
        
        # Projeção baseada em: Volume Diário * Dias Restantes * Probabilidade de Green * (Odd-1)
        # Simplificando pelo lucro médio real atual:
        lucro_diario_real = lucro_total / dias_corridos
        projecao_final = (s_ini + lucro_total) + (lucro_diario_real * dias_restantes)
        
        st.subheader(f"🔮 Projeção para o fim de {mes_sel}")
        cp1, cp2 = st.columns(2)
        cp1.metric("Banca Final Estimada", f"R$ {projecao_final:.2f}")
        cp2.metric("Lucro Adicional Estimado", f"R$ {lucro_diario_real * dias_restantes:.2f}")
    
    # --- GRÁFICOS ---
    if not df_f.empty:
        df_ev = df_f.sort_values('data')
        df_ev['Evolução'] = s_ini + df_ev['lucro'].cumsum()
        st.plotly_chart(px.line(df_ev, x='data', y='Evolução', title="Curva de Patrimônio"), use_container_width=True)

        df_met = df_f.groupby('metodo')['lucro'].sum().reset_index()
        st.plotly_chart(px.bar(df_met, x='metodo', y='lucro', color='lucro', title="Lucro por Método", color_continuous_scale="RdYlGn"), use_container_width=True)
    else:
        st.info("Aguardando registros para gerar os gráficos.")
