import streamlit as st
import pandas as pd
import numpy as np

# --- CONFIGURAÇÃO DE ESTILO (CENTRALIZAÇÃO E CORES) ---
st.markdown("""
    <style>
    .stDataFrame td, .stDataFrame th {text-align: center !important;}
    [data-testid="stTable"] td, [data-testid="stTable"] th {text-align: center !important;}
    </style>
    """, unsafe_allow_html=True)

# --- REGRAS DE LIGAS ---
REGRAS_LIGAS = {
    "BRAZIL 1": {"alvos": {"Libertadores": [1, 6], "Sul-Americana": [7, 12], "Rebaixamento": [17, 20]}},
    "BRAZIL 2": {"alvos": {"Acesso": [1, 4], "Rebaixamento": [17, 20]}},
    "PORTUGAL 1": {"alvos": {"Champions League": [1, 3], "Rebaixamento": [16, 18]}},
}

# --- FUNÇÕES CORE ---
def get_objetivo_txt(liga, pos):
    liga_clean = str(liga).upper().strip()
    if liga_clean not in REGRAS_LIGAS: return "⚪ Meio"
    regras = REGRAS_LIGAS[liga_clean]["alvos"]
    for obj, faixa in regras.items():
        if faixa[0] <= pos <= faixa[1]:
            return f"{'🔴' if 'Rebaixamento' in obj else '🟢'} {obj}"
    return "⚪ Meio"

def calcular_stats_completas(series):
    if series.empty: return [0.0]*5
    mean = series.mean()
    median = series.median()
    mode = series.mode().iloc[0] if not series.mode().empty else 0.0
    std = series.std()
    cv = (std / mean) if mean != 0 else 0.0
    return [mean, median, mode, std, cv]

def get_team_series(df_t, team, col_h, col_a):
    if col_h not in df_t.columns or col_a not in df_t.columns:
        return pd.Series(dtype=float)
    s_h = df_t[df_t['Mandante'] == team][col_h]
    s_a = df_t[df_t['Visitante'] == team][col_a]
    return pd.concat([s_h, s_a])

def criar_tabela_estatistica(df_t, time):
    mapa = {
        'Gols HT': ('Gols_Mandante_HT', 'Gols_Visitante_HT'),
        'Gols FT': ('Gols_Mandante_FT', 'Gols_Visitante_FT'),
        'Cantos HT': ('Corners_H_HT', 'Corners_A_HT'),
        'Cantos FT': ('Corners_H', 'Corners_A'),
        'Chutes': ('Shots_H', 'Shots_A'),
        'Finalizações': ('ShotsOnTarget_H', 'ShotsOnTarget_A'),
        'Cartões': ('Yellow_Cards_H', 'Yellow_Cards_A'),
        'Faltas': ('Fouls_H', 'Fouls_A')
    }
    data = []
    for metric, (col_h, col_a) in mapa.items():
        series = get_team_series(df_t, time, col_h, col_a)
        if not series.empty:
            stats = calcular_stats_completas(series)
            data.append([metric] + stats)
    return pd.DataFrame(data, columns=['Indicador', 'Média', 'Mediana', 'Moda', 'DP', 'CV'])

def calcular_incidencia_mercados(df_t, time):
    df_t = df_t.copy()
    df_t['Total_FT'] = df_t['Gols_Mandante_FT'] + df_t['Gols_Visitante_FT']
    df_t['Total_HT'] = df_t['Gols_Mandante_HT'] + df_t['Gols_Visitante_HT']
    df_t['BTTS_FT'] = (df_t['Gols_Mandante_FT'] > 0) & (df_t['Gols_Visitante_FT'] > 0)
    df_t['BTTS_HT'] = (df_t['Gols_Mandante_HT'] > 0) & (df_t['Gols_Visitante_HT'] > 0)
    df_t['Total_Corners'] = df_t['Corners_H'] + df_t['Corners_A']

    rows = []
    for m in [0.5, 1.5, 2.5, 3.5]:
        rows.append({
            'Mercado': f'Over {m} Gols',
            'HT': f"{(df_t['Total_HT'] > m).mean()*100:.2f}%",
            'FT': f"{(df_t['Total_FT'] > m).mean()*100:.2f}%"
        })
    rows.append({'Mercado': 'Ambas Marcam', 'HT': f"{df_t['BTTS_HT'].mean()*100:.2f}%", 'FT': f"{df_t['BTTS_FT'].mean()*100:.2f}%"})
    for c in [7.5, 8.5, 9.5, 10.5]:
        rows.append({'Mercado': f'Over {c} Cantos', 'HT': '-', 'FT': f"{(df_t['Total_Corners'] > c).mean()*100:.2f}%"})
    return pd.DataFrame(rows)

def render_stat_row(label, val_h, val_v, format_str="{:.2f}"):
    col1, col2, col3 = st.columns([1, 2, 1])
    vh, vv = float(val_h or 0), float(val_v or 0)
    total = vh + vv
    perc = vh / total if total > 0 else 0.5
    with col1: st.markdown(f"<p style='text-align:right;font-weight:bold;font-size:18px;margin:0;'>{format_str.format(vh)}</p>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<p style='text-align:center;font-size:11px;color:gray;margin:0;'>{label}</p>", unsafe_allow_html=True)
        st.progress(max(0.0, min(1.0, perc)))
    with col3: st.markdown(f"<p style='text-align:left;font-weight:bold;font-size:18px;margin:0;'>{format_str.format(vv)}</p>", unsafe_allow_html=True)

# --- FUNÇÃO DE DESTAQUE (MÁXIMO) ---
def highlight_max(s):
    is_max = s == s.max()
    return ['background-color: #1f77b4; color: white; font-weight: bold' if v else '' for v in is_max]

# --- VIEW ---
def mostrar_scout(df):
    st.title("🔎 Scout Profissional - Master Luciano")
    df.columns = [c.strip() for c in df.columns]
    
    c1, c2, c3 = st.columns(3)
    liga_sel = c1.selectbox("Liga", sorted(df['Liga'].unique()))
    df_l = df[df['Liga'] == liga_sel].copy()
    temp_sel = c2.selectbox("Temporada", sorted(df_l['Temporada'].unique(), reverse=True))
    mando_sel = c3.selectbox("Mando", ["Geral", "Casa/Fora"])
    
    df_s = df_l[df_l['Temporada'] == temp_sel].copy()
    times = sorted(df_s['Mandante'].unique())
    m_sel = st.selectbox("Mandante", times)
    v_sel = st.selectbox("Visitante", [t for t in times if t != m_sel])
    n_jogos = st.sidebar.slider("Amostragem", 5, 50, 10)

    if mando_sel == "Geral":
        df_m = df_s[(df_s['Mandante'] == m_sel) | (df_s['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(n_jogos)
        df_v = df_s[(df_s['Mandante'] == v_sel) | (df_s['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(n_jogos)
    else:
        df_m = df_s[df_s['Mandante'] == m_sel].sort_values('Data', ascending=False).head(n_jogos)
        df_v = df_s[df_s['Visitante'] == v_sel].sort_values('Data', ascending=False).head(n_jogos)

    t_resumo, t_detalhe, t_mercado, t_minutos = st.tabs(["📊 Resumo", "📉 Estatística Detalhada", "💰 Mercados", "⏰ Minutos"])

    with t_resumo:
        render_stat_row("xG MÉDIO", get_team_series(df_m, m_sel, 'xG_Mandante', 'xG_Visitante').mean(), get_team_series(df_v, v_sel, 'xG_Mandante', 'xG_Visitante').mean())
        render_stat_row("GOLS FT", get_team_series(df_m, m_sel, 'Gols_Mandante_FT', 'Gols_Visitante_FT').mean(), get_team_series(df_v, v_sel, 'Gols_Mandante_FT', 'Gols_Visitante_FT').mean())
        render_stat_row("CANTOS FT", get_team_series(df_m, m_sel, 'Corners_H', 'Corners_A').mean(), get_team_series(df_v, v_sel, 'Corners_H', 'Corners_A').mean())

    with t_detalhe:
        fmt = {c: "{:.2f}" for c in ['Média', 'Mediana', 'Moda', 'DP', 'CV']}
        st.subheader(f"📊 {m_sel}")
        st.table(criar_tabela_estatistica(df_m, m_sel).style.format(fmt))
        st.subheader(f"📊 {v_sel}")
        st.table(criar_tabela_estatistica(df_v, v_sel).style.format(fmt))

    with t_mercado:
        c_m1, c_m2 = st.columns(2)
        with c_m1:
            st.markdown(f"<h4 style='text-align:center;'>{m_sel}</h4>", unsafe_allow_html=True)
            st.table(calcular_incidencia_mercados(df_m, m_sel))
        with c_m2:
            st.markdown(f"<h4 style='text-align:center;'>{v_sel}</h4>", unsafe_allow_html=True)
            st.table(calcular_incidencia_mercados(df_v, v_sel))

    with t_minutos:
        st.subheader("Gols por Faixa de Minutos (Soma)")
        faixas = ['0-15', '16-30', '31-45+', '46-60', '61-75', '76-90+']
        data_min = []
        for f in faixas:
            m_gols = get_team_series(df_m, m_sel, f'{f}_Mandante', f'{f}_Visitante').sum()
            v_gols = get_team_series(df_v, v_sel, f'{f}_Mandante', f'{f}_Visitante').sum()
            data_min.append({'Intervalo': f, m_sel: int(m_gols), v_sel: int(v_gols)})
        
        df_min = pd.DataFrame(data_min)
        # Aplicando destaque na coluna de cada time
        st.table(df_min.style.apply(highlight_max, subset=[m_sel, v_sel]))
