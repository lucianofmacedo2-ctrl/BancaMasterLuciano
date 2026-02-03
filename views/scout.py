import streamlit as st
import pandas as pd
import numpy as np

# --- 1. CONFIGURAÇÃO DE ESTILO (CENTRALIZAÇÃO E VISUAL) ---
st.set_page_config(layout="wide")

st.markdown("""
    <style>
    .stDataFrame td, .stDataFrame th, [data-testid="stTable"] td, [data-testid="stTable"] th {
        text-align: center !important;
        vertical-align: middle !important;
    }
    .metric-container {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FUNÇÕES DE CÁLCULO ---
def calcular_stats_completas(series):
    if series.empty: return [0.0]*5
    mean = series.mean()
    median = series.median()
    mode = series.mode().iloc[0] if not series.mode().empty else 0.0
    std = series.std()
    cv = (std / mean) if mean != 0 else 0.0
    return [mean, median, mode, std, cv]

def get_team_series(df_t, team, col_h, col_a):
    s_h = df_t[df_t['Mandante'] == team][col_h] if col_h in df_t.columns else pd.Series(dtype=float)
    s_a = df_t[df_t['Visitante'] == team][col_a] if col_a in df_t.columns else pd.Series(dtype=float)
    return pd.concat([s_h, s_a])

def highlight_max(s):
    is_max = s == s.max()
    return ['background-color: #1f77b4; color: white; font-weight: bold' if v else '' for v in is_max]

def calcular_mercados(df_t):
    df_t = df_t.copy()
    df_t['Total_FT'] = df_t['Gols_Mandante_FT'] + df_t['Gols_Visitante_FT']
    df_t['Total_HT'] = df_t['Gols_Mandante_HT'] + df_t['Gols_Visitante_HT']
    df_t['BTTS'] = (df_t['Gols_Mandante_FT'] > 0) & (df_t['Gols_Visitante_FT'] > 0)
    
    rows = []
    for m in [0.5, 1.5, 2.5, 3.5]:
        rows.append({
            'Mercado': f'Over {m} Gols',
            'HT': f"{(df_t['Total_HT'] > m).mean()*100:.2f}%",
            'FT': f"{(df_t['Total_FT'] > m).mean()*100:.2f}%"
        })
    rows.append({'Mercado': 'BTTS (Ambas)', 'HT': '-', 'FT': f"{df_t['BTTS'].mean()*100:.2f}%"})
    return pd.DataFrame(rows)

# --- 3. VIEW PRINCIPAL ---
def mostrar_scout(df):
    st.title("🔎 Scout Profissional - Master Luciano")
    df.columns = [c.strip() for c in df.columns]

    # --- SEQUÊNCIA DE FILTROS (LIGA -> CLUBES) ---
    col_f1, col_f2 = st.columns(2)
    
    # 1. Escolher a Liga
    lista_ligas = sorted(df['Liga'].unique())
    liga_sel = col_f1.selectbox("1º Selecione a Liga", lista_ligas)
    df_l = df[df['Liga'] == liga_sel].copy()

    # 2. Escolher os Clubes (Baseado na Liga)
    lista_times = sorted(df_l['Mandante'].unique())
    m_sel = col_f1.selectbox("2º Time Mandante", lista_times)
    v_sel = col_f2.selectbox("3º Time Visitante", [t for t in lista_times if t != m_sel])

    # Filtros Adicionais
    n_jogos = st.sidebar.slider("Amostragem de Jogos", 5, 50, 10)
    mando_sel = st.sidebar.radio("Tipo de Amostragem", ["Geral (Todos os Jogos)", "Mando de Campo (Casa/Fora)"])

    # --- FILTRAGEM DOS DADOS ---
    if mando_sel == "Geral (Todos os Jogos)":
        df_m = df_l[(df_l['Mandante'] == m_sel) | (df_l['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(n_jogos)
        df_v = df_l[(df_l['Mandante'] == v_sel) | (df_l['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(n_jogos)
    else:
        df_m = df_l[df_l['Mandante'] == m_sel].sort_values('Data', ascending=False).head(n_jogos)
        df_v = df_l[df_l['Visitante'] == v_sel].sort_values('Data', ascending=False).head(n_jogos)

    # --- DASHBOARD DE RESUMO ---
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("xG Médio", f"{get_team_series(df_m, m_sel, 'xG_Mandante', 'xG_Visitante').mean():.2f}")
    with c2: st.metric("Média Gols FT", f"{get_team_series(df_m, m_sel, 'Gols_Mandante_FT', 'Gols_Visitante_FT').mean():.2f}")
    with c3: st.metric("Média Cantos FT", f"{get_team_series(df_m, m_sel, 'Corners_H', 'Corners_A').mean():.2f}")
    with c4: st.metric("Chutes no Gol", f"{get_team_series(df_m, m_sel, 'ShotsOnTarget_H', 'ShotsOnTarget_A').mean():.2f}")
    st.divider()

    # --- ABAS DE INFORMAÇÃO DETALHADA ---
    tab_stats, tab_mercados, tab_minutos, tab_historico = st.tabs([
        "📉 Estatística Detalhada", "💰 Incidência de Mercados", "⏰ Análise de Minutos", "🕒 Histórico Recente"
    ])

    with tab_stats:
        fmt = {c: "{:.2f}" for c in ['Média', 'Mediana', 'Moda', 'DP', 'CV']}
        mapa_indicadores = {
            'Gols HT': ('Gols_Mandante_HT', 'Gols_Visitante_HT'),
            'Gols FT': ('Gols_Mandante_FT', 'Gols_Visitante_FT'),
            'Cantos FT': ('Corners_H', 'Corners_A'),
            'Chutes Totais': ('Shots_H', 'Shots_A'),
            'Finalizações': ('ShotsOnTarget_H', 'ShotsOnTarget_A'),
            'Cartões Amarelos': ('Yellow_Cards_H', 'Yellow_Cards_A')
        }

        for time, dft, label in [(m_sel, df_m, "MANDANTE"), (v_sel, df_v, "VISITANTE")]:
            st.subheader(f"📊 {label}: {time}")
            stats_data = []
            for ind, (ch, ca) in mapa_indicadores.items():
                stats_data.append([ind] + calcular_stats_completas(get_team_series(dft, time, ch, ca)))
            df_final_stats = pd.DataFrame(stats_data, columns=['Indicador', 'Média', 'Mediana', 'Moda', 'DP', 'CV'])
            st.table(df_final_stats.style.format(fmt))

    with tab_mercados:
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.markdown(f"**Mercados {m_sel}**")
            st.table(calcular_mercados(df_m))
        with col_m2:
            st.markdown(f"**Mercados {v_sel}**")
            st.table(calcular_mercados(df_v))

    with tab_minutos:
        st.subheader("Gols Marcados por Faixa de Minutos (Soma)")
        faixas = ['0-15', '16-30', '31-45+', '46-60', '61-75', '76-90+']
        min_list = []
        for f in faixas:
            m_s = get_team_series(df_m, m_sel, f'{f}_Mandante', f'{f}_Visitante').sum()
            v_s = get_team_series(df_v, v_sel, f'{f}_Mandante', f'{f}_Visitante').sum()
            min_list.append({'Intervalo': f, m_sel: int(m_s), v_sel: int(v_s)})
        
        df_min_table = pd.DataFrame(min_list)
        st.table(df_min_table.style.apply(highlight_max, subset=[m_sel, v_sel]))

    with tab_historico:
        cols_h = ['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']
        st.write(f"Últimos jogos de {m_sel}")
        st.dataframe(df_m[cols_h], hide_index=True, use_container_width=True)
        st.write(f"Últimos jogos de {v_sel}")
        st.dataframe(df_v[cols_h], hide_index=True, use_container_width=True)
