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
def encontrar_coluna(df, lista_possibilidades):
    """Procura uma coluna no DF ignorando maiúsculas/minúsculas e espaços."""
    cols_no_csv = {c.strip().lower(): c for c in df.columns}
    for p in lista_possibilidades:
        p_clean = p.strip().lower()
        if p_clean in cols_no_csv:
            return cols_no_csv[p_clean]
    return None

def get_objetivo_txt(liga, pos):
    liga_clean = str(liga).upper().strip()
    if liga_clean not in REGRAS_LIGAS: return "⚪ Meio"
    regras = REGRAS_LIGAS[liga_clean]["alvos"]
    for obj, faixa in regras.items():
        if faixa[0] <= pos <= faixa[1]:
            return f"{'🔴' if 'Rebaixamento' in obj else '🟢'} {obj}"
    return "⚪ Meio"

def calcular_tabela_completa(df_liga):
    # Busca colunas necessárias para a tabela
    c_m = encontrar_coluna(df_liga, ['Mandante'])
    c_v = encontrar_coluna(df_liga, ['Visitante'])
    c_gm = encontrar_coluna(df_liga, ['Gols_Mandante_FT', 'Gols Mandante FT'])
    c_gv = encontrar_coluna(df_liga, ['Gols_Visitante_FT', 'Gols Visitante FT'])

    if not all([c_m, c_v, c_gm, c_gv]): return pd.DataFrame()

    stats = {}
    for _, r in df_liga.iterrows():
        m, v = r[c_m], r[c_v]
        gm, gv = r[c_gm], r[c_gv]
        for t in [m, v]:
            if t not in stats:
                stats[t] = {'P':0,'J':0,'V':0,'SG':0, 'P_Casa':0,'P_Fora':0}
        
        stats[m]['J']+=1; stats[v]['J']+=1
        stats[m]['SG']+=(gm-gv); stats[v]['SG']+=(gv-gm)
        
        if gm > gv: 
            stats[m]['P']+=3; stats[m]['V']+=1; stats[m]['P_Casa']+=3
        elif gm == gv: 
            stats[m]['P']+=1; stats[v]['P']+=1
        else: 
            stats[v]['P']+=3; stats[v]['V']+=1; stats[v]['P_Fora']+=3
            
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

def mostrar_scout(df):
    if df.empty: return st.error("CSV não carregado.")
    
    st.title("🔎 Scout de Elite - Master Luciano")
    
    # --- MAPEAMENTO DINÂMICO DE COLUNAS ---
    col_liga = encontrar_coluna(df, ['Liga'])
    col_temp = encontrar_coluna(df, ['Temporada'])
    col_mandante = encontrar_coluna(df, ['Mandante'])
    col_visitante = encontrar_coluna(df, ['Visitante'])
    col_data = encontrar_coluna(df, ['Data'])

    # --- FILTROS ---
    df[col_liga] = df[col_liga].astype(str).str.strip().str.upper()
    c1, c2, c3 = st.columns(3)
    liga_sel = c1.selectbox("Liga", sorted(df[col_liga].unique()))
    df_l = df[df[col_liga] == liga_sel].copy()
    temp_sel = c2.selectbox("Temporada", sorted(df_l[col_temp].unique(), reverse=True))
    mando_sel = c3.selectbox("Filtro de Mando", ["Geral (Todos)", "Casa/Fora"])
    
    df_s = df_l[df_l[col_temp] == temp_sel].copy()
    times = sorted(df_s[col_mandante].unique())
    m_sel = st.selectbox("Mandante", times)
    v_sel = st.selectbox("Visitante", [t for t in times if t != m_sel])
    n_jogos = st.sidebar.slider("Amostragem", 5, 50, 10)

    # --- POSIÇÕES ---
    df_ranking = calcular_tabela_completa(df_s)
    if not df_ranking.empty:
        pos_m = int(df_ranking[df_ranking['Time']==m_sel]['Pos_Geral'].values[0])
        pos_v = int(df_ranking[df_ranking['Time']==v_sel]['Pos_Geral'].values[0])
        st.info(f"📍 **{m_sel}** ({pos_m}º) vs **{v_sel}** ({pos_v}º)")

    # Amostragem
    if mando_sel == "Geral (Todos)":
        df_m = df_s[(df_s[col_mandante] == m_sel) | (df_s[col_visitante] == m_sel)].sort_values(col_data, ascending=False).head(n_jogos)
        df_v = df_s[(df_s[col_mandante] == v_sel) | (df_s[col_visitante] == v_sel)].sort_values(col_data, ascending=False).head(n_jogos)
    else:
        df_m = df_s[df_s[col_mandante] == m_sel].sort_values(col_data, ascending=False).head(n_jogos)
        df_v = df_s[df_s[col_visitante] == v_sel].sort_values(col_data, ascending=False).head(n_jogos)

    # --- POWER STATS (COM BUSCA INTELIGENTE) ---
    st.markdown("### 📊 Power Stats (Médias)")

    def calc_media(df_t, team, lista_h, lista_a):
        ch = encontrar_coluna(df_t, lista_h)
        ca = encontrar_coluna(df_t, lista_a)
        if ch and ca:
            return np.where(df_t[col_mandante] == team, df_t[ch], df_t[ca]).mean()
        return 0.0

    # Lista de Médias Mapeadas
    stats_map = [
        ("EXPECTATIVA DE GOLS (xG)", ['xG_Mandante', 'xG Mandante', 'Total_xG'], ['xG_Visitante', 'xG Visitante', 'Total_xG']),
        ("PONTOS POR JOGO (PPG)", ['PPG_H_Pre', 'PPG Casa'], ['PPG_A_Pre', 'PPG Fora']),
        ("GOLS FT", ['Gols_Mandante_FT'], ['Gols_Visitante_FT']),
        ("ATAQUES PERIGOSOS", ['DangerousAttacks_H', 'Ataques Perigosos Mandante'], ['DangerousAttacks_A', 'Ataques Perigosos Visitante']),
        ("CHUTES NO GOL", ['ShotsOnTarget_H'], ['ShotsOnTarget_A']),
        ("CANTOS TOTAIS FT", ['Corners_H'], ['Corners_A']),
        ("CARTÕES (TOTAL)", ['Total_Cards_H'], ['Total_Cards_A']),
        ("FALTAS", ['Fouls_H'], ['Fouls_A'])
    ]

    for label, lh, la in stats_map:
        render_stat_row(label, calc_media(df_m, m_sel, lh, la), calc_media(df_v, v_sel, lh, la))

    # --- ABAS ---
    t_hist, t_tecnico, t_class = st.tabs(["🕒 Histórico", "⚙️ Técnico & Pênaltis", "🏆 Tabela"])

    with t_hist:
        # Pega as colunas de gols para o histórico
        c_gm = encontrar_coluna(df, ['Gols_Mandante_FT'])
        c_gv = encontrar_coluna(df, ['Gols_Visitante_FT'])
        cols_hist = [col_data, col_mandante, c_gm, c_gv, col_visitante]
        cols_hist = [c for c in cols_hist if c is not None]
        
        c_col1, c_col2 = st.columns(2)
        c_col1.dataframe(df_m[cols_hist], hide_index=True)
        c_col2.dataframe(df_v[cols_hist], hide_index=True)

    with t_tecnico:
        st.subheader("Finalizações e Posse")
        render_stat_row("POSSE DE BOLA", calc_media(df_m, m_sel, ['Possession_H'], ['Possession_A']), calc_media(df_v, v_sel, ['Possession_H'], ['Possession_A']), "{:.1f}%")
        render_stat_row("PÊNALTIS GANHOS", calc_media(df_m, m_sel, ['Penalties_Won_H'], ['Penalties_Won_A']), calc_media(df_v, v_sel, ['Penalties_Won_H'], ['Penalties_Won_A']))

    with t_class:
        if not df_ranking.empty:
            df_rank_show = df_ranking.sort_values('Pos_Geral').copy()
            df_rank_show['Objetivo'] = df_rank_show.apply(lambda r: get_objetivo_txt(liga_sel, r['Pos_Geral']), axis=1)
            st.dataframe(df_rank_show, use_container_width=True, hide_index=True)
