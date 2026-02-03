import streamlit as st
import pandas as pd
import numpy as np

# --- 1. CONFIGURAÇÃO DE ESTILO E LAYOUT ---
st.set_page_config(layout="wide")

st.markdown("""
    <style>
    /* Centralização de tabelas e cabeçalhos */
    .stDataFrame td, .stDataFrame th, [data-testid="stTable"] td, [data-testid="stTable"] th {
        text-align: center !important;
        vertical-align: middle !important;
    }
    /* Estilização dos Cards de Resumo */
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border: 1px solid #d1d5db;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNÇÕES DE SUPORTE ---
def calcular_stats_v2(series):
    if series.empty: return [0.0]*5
    mean = series.mean()
    median = series.median()
    mode = series.mode().iloc[0] if not series.mode().empty else 0.0
    std = series.std()
    cv = (std / mean) if mean != 0 else 0.0
    return [mean, median, mode, std, cv]

def get_team_series(df_t, team, col_h, col_a):
    s_h = df_t[df_t['Mandante'] == team][col_h] if col_h in df_t.columns else pd.Series()
    s_a = df_t[df_t['Visitante'] == team][col_a] if col_a in df_t.columns else pd.Series()
    return pd.concat([s_h, s_a])

def highlight_max(s):
    is_max = s == s.max()
    return ['background-color: #1f77b4; color: white; font-weight: bold' if v else '' for v in is_max]

# --- 3. COMPONENTES DO SCOUT ---

def render_metric_dashboard(df_m, df_v, m_sel, v_sel):
    st.markdown("### 🏟️ Visão Geral de Performance")
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        m_xg = get_team_series(df_m, m_sel, 'xG_Mandante', 'xG_Visitante').mean()
        v_xg = get_team_series(df_v, v_sel, 'xG_Mandante', 'xG_Visitante').mean()
        st.metric("xG Médio", f"{m_xg:.2f}", f"{m_xg - v_xg:.2f}", delta_color="normal")
        
    with c2:
        m_g = get_team_series(df_m, m_sel, 'Gols_Mandante_FT', 'Gols_Visitante_FT').mean()
        v_g = get_team_series(df_v, v_sel, 'Gols_Mandante_FT', 'Gols_Visitante_FT').mean()
        st.metric("Gols Pro FT", f"{m_g:.2f}", f"{m_g - v_g:.2f}")

    with c3:
        m_c = get_team_series(df_m, m_sel, 'Corners_H', 'Corners_A').mean()
        v_c = get_team_series(df_v, v_sel, 'Corners_H', 'Corners_A').mean()
        st.metric("Cantos FT", f"{m_c:.2f}", f"{m_c - v_c:.2f}")
        
    with c4:
        m_s = get_team_series(df_m, m_sel, 'ShotsOnTarget_H', 'ShotsOnTarget_A').mean()
        v_s = get_team_series(df_v, v_sel, 'ShotsOnTarget_H', 'ShotsOnTarget_A').mean()
        st.metric("Chutes no Gol", f"{m_s:.2f}", f"{m_s - v_s:.2f}")

def mostrar_scout(df):
    df.columns = [c.strip() for c in df.columns]
    
    # Sidebar Filtros
    st.sidebar.header("Configurações do Scout")
    liga_sel = st.sidebar.selectbox("Liga", sorted(df['Liga'].unique()))
    df_l = df[df['Liga'] == liga_sel].copy()
    
    times = sorted(df_l['Mandante'].unique())
    m_sel = st.selectbox("Time Mandante", times)
    v_sel = st.selectbox("Time Visitante", [t for t in times if t != m_sel])
    
    n_jogos = st.sidebar.slider("Quantidade de Jogos", 5, 50, 10)
    mando_sel = st.sidebar.radio("Mando", ["Geral", "Casa/Fora"])

    # Filtragem de Amostragem
    if mando_sel == "Geral":
        df_m = df_l[(df_l['Mandante'] == m_sel) | (df_l['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(n_jogos)
        df_v = df_l[(df_l['Mandante'] == v_sel) | (df_l['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(n_jogos)
    else:
        df_m = df_l[df_l['Mandante'] == m_sel].sort_values('Data', ascending=False).head(n_jogos)
        df_v = df_l[df_l['Visitante'] == v_sel].sort_values('Data', ascending=False).head(n_jogos)

    # --- DASHBOARD DE MÉTRICAS ---
    render_metric_dashboard(df_m, df_v, m_sel, v_sel)
    st.divider()

    # --- ABAS DE INFORMAÇÃO ---
    t_detalhe, t_mercado, t_minutos, t_hist = st.tabs(["📉 Estatísticas Detalhadas", "💰 Incidência de Mercados", "⏰ Análise de Minutos", "🕒 Histórico Recente"])

    with t_detalhe:
        fmt = {c: "{:.2f}" for c in ['Média', 'Mediana', 'Moda', 'DP', 'CV']}
        
        st.markdown(f"#### 📊 Estatísticas Avançadas: {m_sel}")
        st.table(criar_tabela_stats(df_m, m_sel).style.format(fmt))
        
        st.markdown(f"#### 📊 Estatísticas Avançadas: {v_sel}")
        st.table(criar_tabela_stats(df_v, v_sel).style.format(fmt))

    with t_mercado:
        c_m1, c_m2 = st.columns(2)
        with c_m1:
            st.markdown(f"**Mercados: {m_sel}**")
            st.table(calcular_mercados_v2(df_m))
        with c_m2:
            st.markdown(f"**Mercados: {v_sel}**")
            st.table(calcular_mercados_v2(df_v))

    with t_minutos:
        st.markdown("#### ⏰ Gols Marcados por Faixa (Total na Amostragem)")
        faixas = ['0-15', '16-30', '31-45+', '46-60', '61-75', '76-90+']
        min_data = []
        for f in faixas:
            m_sum = get_team_series(df_m, m_sel, f'{f}_Mandante', f'{f}_Visitante').sum()
            v_sum = get_team_series(df_v, v_sel, f'{f}_Mandante', f'{f}_Visitante').sum()
            min_data.append({'Intervalo': f, m_sel: int(m_sum), v_sel: int(v_sum)})
        
        df_min = pd.DataFrame(min_data)
        st.table(df_min.style.apply(highlight_max, subset=[m_sel, v_sel]))

    with t_hist:
        cols_h = ['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']
        st.markdown(f"**Últimos {n_jogos} jogos de {m_sel}**")
        st.dataframe(df_m[cols_h], hide_index=True, use_container_width=True)
        st.markdown(f"**Últimos {n_jogos} jogos de {v_sel}**")
        st.dataframe(df_v[cols_h], hide_index=True, use_container_width=True)

# --- 4. FUNÇÕES INTERNAS DE TABELAS ---

def criar_tabela_stats(df_t, time):
    mapa = {
        'Gols HT': ('Gols_Mandante_HT', 'Gols_Visitante_HT'),
        'Gols FT': ('Gols_Mandante_FT', 'Gols_Visitante_FT'),
        'Cantos FT': ('Corners_H', 'Corners_A'),
        'Chutes': ('Shots_H', 'Shots_A'),
        'Finalizações': ('ShotsOnTarget_H', 'ShotsOnTarget_A'),
        'Cartões': ('Yellow_Cards_H', 'Yellow_Cards_A')
    }
    data = []
    for metric, (col_h, col_a) in mapa.items():
        series = get_team_series(df_t, time, col_h, col_a)
        data.append([metric] + calcular_stats_v2(series))
    return pd.DataFrame(data, columns=['Indicador', 'Média', 'Mediana', 'Moda', 'DP', 'CV'])

def calcular_mercados_v2(df_t):
    df_t = df_t.copy()
    df_t['Total_FT'] = df_t['Gols_Mandante_FT'] + df_t['Gols_Visitante_FT']
    df_t['Total_HT'] = df_t['Gols_Mandante_HT'] + df_t['Gols_Visitante_HT']
    df_t['BTTS'] = (df_t['Gols_Mandante_FT'] > 0) & (df_t['Gols_Visitante_FT'] > 0)
    
    rows = []
    for m in [0.5, 1.5, 2.5]:
        rows.append({'Mercado': f'Over {m} Gols', 'HT': f"{(df_t['Total_HT'] > m).mean()*100:.2f}%", 'FT': f"{(df_t['Total_FT'] > m).mean()*100:.2f}%"})
    rows.append({'Mercado': 'BTTS (Ambas)', 'HT': '-', 'FT': f"{df_t['BTTS'].mean()*100:.2f}%"})
    return pd.DataFrame(rows)
