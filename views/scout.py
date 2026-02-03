import streamlit as st
import pandas as pd
import numpy as np

# --- DICIONÁRIO DE REGRAS DE OBJETIVOS ---
REGRAS_LIGAS = {
    "BRAZIL 1": {"alvos": {"Libertadores": [1, 6], "Sul-Americana": [7, 12], "Rebaixamento": [17, 20]}},
    "BRAZIL 2": {"alvos": {"Acesso": [1, 4], "Rebaixamento": [17, 20]}},
    "PORTUGAL 1": {"alvos": {"Champions League": [1, 3], "Conference": [4, 5], "Rebaixamento": [16, 18]}},
    "ENGLAND 1": {"alvos": {"Champions League": [1, 4], "Europa League": [5, 5], "Rebaixamento": [18, 20]}},
}

# --- FUNÇÕES DE APOIO ---
def get_objetivo_txt(liga, pos):
    liga_clean = str(liga).upper().strip()
    if liga_clean not in REGRAS_LIGAS: return "⚪ Meio"
    regras = REGRAS_LIGAS[liga_clean]["alvos"]
    for obj, faixa in regras.items():
        if faixa[0] <= pos <= faixa[1]:
            return f"{'🔴' if 'Rebaixamento' in obj else '🟢'} {obj}"
    return "⚪ Meio"

def calcular_tabela_completa(df_liga):
    if df_liga.empty: return pd.DataFrame()
    stats = {}
    for _, r in df_liga.iterrows():
        m, v = r['Mandante'], r['Visitante']
        gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
        for t in [m, v]:
            if t not in stats: stats[t] = {'P':0,'J':0,'V':0,'SG':0}
        stats[m]['J']+=1; stats[v]['J']+=1
        stats[m]['SG']+=(gm-gv); stats[v]['SG']+=(gv-gm)
        if gm > gv: stats[m]['P']+=3; stats[m]['V']+=1
        elif gm == gv: stats[m]['P']+=1; stats[v]['P']+=1
        else: stats[v]['P']+=3; stats[v]['V']+=1
    df = pd.DataFrame.from_dict(stats, orient='index').reset_index().rename(columns={'index':'Time'})
    if not df.empty:
        df['Pos_Geral'] = df[['P', 'V', 'SG']].apply(tuple, axis=1).rank(method='min', ascending=False)
    return df

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

def get_avg(df_t, team, col_h, col_a):
    if df_t.empty or col_h not in df_t.columns: return 0.0
    vals_m = df_t[df_t['Mandante'] == team][col_h]
    vals_v = df_t[df_t['Visitante'] == team][col_a]
    combined = pd.concat([vals_m, vals_v])
    return combined.mean() if not combined.empty else 0.0

def mostrar_scout(df):
    if df.empty: return st.error("Arquivo CSV vazio.")
    df.columns = [c.strip() for c in df.columns]

    st.title("🔎 Scout de Elite - Master Luciano")

    # --- FILTROS ---
    c1, c2, c3 = st.columns(3)
    liga_sel = c1.selectbox("Selecione a Liga", sorted(df['Liga'].unique()))
    df_l = df[df['Liga'] == liga_sel].copy()
    temp_sel = c2.selectbox("Temporada", sorted(df_l['Temporada'].unique(), reverse=True))
    mando_sel = c3.selectbox("Filtro de Mando", ["Geral (Todos)", "Apenas Casa/Fora"])
    
    df_s = df_l[df_l['Temporada'] == temp_sel].copy()
    times = sorted(df_s['Mandante'].unique())
    m_sel = st.selectbox("Mandante", times)
    v_sel = st.selectbox("Visitante", [t for t in times if t != m_sel])
    n_jogos = st.sidebar.slider("Amostragem", 5, 50, 10)

    # --- CÁLCULO DE POSIÇÕES ---
    df_ranking = calcular_tabela_completa(df_s)
    if not df_ranking.empty:
        pos_m = int(df_ranking[df_ranking['Time']==m_sel]['Pos_Geral'].values[0])
        pos_v = int(df_ranking[df_ranking['Time']==v_sel]['Pos_Geral'].values[0])
        st.info(f"📍 **{m_sel}** ({pos_m}º) vs **{v_sel}** ({pos_v}º)")

    # Filtro de Amostragem
    if mando_sel == "Geral (Todos)":
        df_m = df_s[(df_s['Mandante'] == m_sel) | (df_s['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(n_jogos)
        df_v = df_s[(df_s['Mandante'] == v_sel) | (df_s['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(n_jogos)
    else:
        df_m = df_s[df_s['Mandante'] == m_sel].sort_values('Data', ascending=False).head(n_jogos)
        df_v = df_s[df_s['Visitante'] == v_sel].sort_values('Data', ascending=False).head(n_jogos)

    # --- POWER STATS ---
    st.markdown("### 📊 Power Stats (Médias)")
    render_stat_row("EXPECTATIVA DE GOLS (xG)", get_avg(df_m, m_sel, 'xG_Mandante', 'xG_Visitante'), get_avg(df_v, v_sel, 'xG_Mandante', 'xG_Visitante'))
    render_stat_row("GOLS FT", get_avg(df_m, m_sel, 'Gols_Mandante_FT', 'Gols_Visitante_FT'), get_avg(df_v, v_sel, 'Gols_Mandante_FT', 'Gols_Visitante_FT'))
    render_stat_row("ATAQUES PERIGOSOS", get_avg(df_m, m_sel, 'DangerousAttacks_H', 'DangerousAttacks_A'), get_avg(df_v, v_sel, 'DangerousAttacks_H', 'DangerousAttacks_A'))
    render_stat_row("CHUTES NO GOL", get_avg(df_m, m_sel, 'ShotsOnTarget_H', 'ShotsOnTarget_A'), get_avg(df_v, v_sel, 'ShotsOnTarget_H', 'ShotsOnTarget_A'))
    render_stat_row("CANTOS TOTAIS FT", get_avg(df_m, m_sel, 'Corners_H', 'Corners_A'), get_avg(df_v, v_sel, 'Corners_H', 'Corners_A'))

    # --- ABAS ---
    t_hist, t_stats, t_minutos, t_class = st.tabs(["🕒 Histórico", "📊 Técnico/Odds", "⏰ Minutos", "🏆 Tabela"])

    with t_hist:
        cols_h = ['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']
        c_c1, c_c2 = st.columns(2)
        c_c1.dataframe(df_m[cols_h], hide_index=True)
        c_c2.dataframe(df_v[cols_h], hide_index=True)

    with t_stats:
        st.markdown("#### Odds Médias e Disciplina")
        render_stat_row("ODD FT", get_avg(df_m, m_sel, 'Odd_Mandante_FT', 'Odd_Visitante_FT'), get_avg(df_v, v_sel, 'Odd_Mandante_FT', 'Odd_Visitante_FT'))
        render_stat_row("POSSE DE BOLA", get_avg(df_m, m_sel, 'Possession_H', 'Possession_A'), get_avg(df_v, v_sel, 'Possession_H', 'Possession_A'), "{:.1f}%")
        render_stat_row("CARTÕES AMARELOS", get_avg(df_m, m_sel, 'Yellow_Cards_H', 'Yellow_Cards_A'), get_avg(df_v, v_sel, 'Yellow_Cards_H', 'Yellow_Cards_A'))
        render_stat_row("PÊNALTIS GANHOS", get_avg(df_m, m_sel, 'Penalties_Won_H', 'Penalties_Won_A'), get_avg(df_v, v_sel, 'Penalties_Won_H', 'Penalties_Won_A'))

    with t_minutos:
        st.subheader("Gols por Faixa de Tempo")
        faixas = ['0-15', '16-30', '31-45+', '46-60', '61-75', '76-90+']
        for f in faixas:
            m_f = get_avg(df_m, m_sel, f"{f}_Mandante", f"{f}_Visitante")
            v_f = get_avg(df_v, v_sel, f"{f}_Mandante", f"{f}_Visitante")
            render_stat_row(f"Gols {f} min", m_f, v_f)

    with t_class:
        df_rank_show = df_ranking.sort_values('Pos_Geral').copy()
        df_rank_show['Objetivo'] = df_rank_show.apply(lambda r: get_objetivo_txt(liga_sel, r['Pos_Geral']), axis=1)
        st.dataframe(df_rank_show, use_container_width=True, hide_index=True)
