import streamlit as st
import pandas as pd
import numpy as np

# --- CONFIGURAÇÃO DE LIGAS ---
REGRAS_LIGAS = {
    "BRAZIL 1": {"alvos": {"Libertadores": [1, 6], "Sul-Americana": [7, 12], "Rebaixamento": [17, 20]}},
    "BRAZIL 2": {"alvos": {"Acesso": [1, 4], "Rebaixamento": [17, 20]}},
    "PORTUGAL 1": {"alvos": {"Champions League": [1, 3], "Rebaixamento": [16, 18]}},
}

def get_objetivo_txt(liga, pos):
    liga_clean = str(liga).upper().strip()
    if liga_clean not in REGRAS_LIGAS: return "⚪ Meio"
    regras = REGRAS_LIGAS[liga_clean]["alvos"]
    for obj, faixa in regras.items():
        if faixa[0] <= pos <= faixa[1]:
            return f"{'🔴' if 'Rebaixamento' in obj else '🟢'} {obj}"
    return "⚪ Meio"

def calcular_tabela(df_liga):
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
    
    df_tab = pd.DataFrame.from_dict(stats, orient='index').reset_index().rename(columns={'index':'Time'})
    if not df_tab.empty:
        df_tab['Pos'] = df_tab[['P', 'V', 'SG']].apply(tuple, axis=1).rank(method='min', ascending=False)
    return df_tab

def render_stat_row(label, val_h, val_v, format_str="{:.2f}"):
    col1, col2, col3 = st.columns([1, 2, 1])
    vh, vv = float(val_h or 0), float(val_v or 0)
    total = vh + vv
    perc = vh / total if total > 0 else 0.5
    with col1: st.markdown(f"<p style='text-align:right;font-weight:bold;font-size:18px;margin:0;'>{format_str.format(vh)}</p>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<p style='text-align:center;font-size:10px;color:gray;margin:0;text-transform:uppercase;'>{label}</p>", unsafe_allow_html=True)
        st.progress(max(0.0, min(1.0, perc)))
    with col3: st.markdown(f"<p style='text-align:left;font-weight:bold;font-size:18px;margin:0;'>{format_str.format(vv)}</p>", unsafe_allow_html=True)

def get_avg(df_t, team, col_h, col_a):
    """Função segura para calcular média sem dar KeyError"""
    if df_t.empty: return 0.0
    if col_h not in df_t.columns or col_a not in df_t.columns: return 0.0
    
    # Filtra onde o time é mandante e onde é visitante
    vals_m = df_t[df_t['Mandante'] == team][col_h]
    vals_v = df_t[df_t['Visitante'] == team][col_a]
    
    combined = pd.concat([vals_m, vals_v])
    return combined.mean() if not combined.empty else 0.0

def mostrar_scout(df):
    if df.empty:
        st.error("Base de dados vazia.")
        return

    # Limpeza e padronização
    df.columns = [c.strip() for c in df.columns]
    
    st.title("🔎 Scout Detalhado")

    # Filtros
    liga_sel = st.selectbox("Selecione a Liga", sorted(df['Liga'].unique()))
    df_l = df[df['Liga'] == liga_sel].copy()
    
    times = sorted(df_l['Mandante'].unique())
    col_a, col_b = st.columns(2)
    m_sel = col_a.selectbox("Time Mandante", times)
    v_sel = col_b.selectbox("Time Visitante", [t for t in times if t != m_sel])
    
    n_jogos = st.sidebar.slider("Quantidade de Jogos", 5, 20, 10)

    # Amostragem (Últimos jogos de cada time)
    df_m = df_l[(df_l['Mandante'] == m_sel) | (df_l['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(n_jogos)
    df_v = df_l[(df_l['Mandante'] == v_sel) | (df_l['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(n_jogos)

    # --- ÁREA DE SCOUTS ---
    st.subheader("⚽ Expectativa e Gols")
    render_stat_row("xG (Gols Esperados)", get_avg(df_m, m_sel, 'xG_Mandante', 'xG_Visitante'), get_avg(df_v, v_sel, 'xG_Mandante', 'xG_Visitante'))
    render_stat_row("Gols Marcados FT", get_avg(df_m, m_sel, 'Gols_Mandante_FT', 'Gols_Visitante_FT'), get_avg(df_v, v_sel, 'Gols_Mandante_FT', 'Gols_Visitante_FT'))
    render_stat_row("PPG (Pontos p/ Jogo)", get_avg(df_m, m_sel, 'PPG_H_Pre', 'PPG_A_Pre'), get_avg(df_v, v_sel, 'PPG_H_Pre', 'PPG_A_Pre'))

    st.subheader("🚩 Estatísticas de Jogo")
    render_stat_row("Escanteios (Cantos)", get_avg(df_m, m_sel, 'Corners_H', 'Corners_A'), get_avg(df_v, v_sel, 'Corners_H', 'Corners_A'))
    render_stat_row("Ataques Perigosos", get_avg(df_m, m_sel, 'DangerousAttacks_H', 'DangerousAttacks_A'), get_avg(df_v, v_sel, 'DangerousAttacks_H', 'DangerousAttacks_A'))
    render_stat_row("Chutes no Gol", get_avg(df_m, m_sel, 'ShotsOnTarget_H', 'ShotsOnTarget_A'), get_avg(df_v, v_sel, 'ShotsOnTarget_H', 'ShotsOnTarget_A'))

    st.subheader("🟨 Disciplina e Posse")
    render_stat_row("Cartões Amarelos", get_avg(df_m, m_sel, 'Yellow_Cards_H', 'Yellow_Cards_A'), get_avg(df_v, v_sel, 'Yellow_Cards_H', 'Yellow_Cards_A'))
    render_stat_row("Posse de Bola (%)", get_avg(df_m, m_sel, 'Possession_H', 'Possession_A'), get_avg(df_v, v_sel, 'Possession_H', 'Possession_A'), "{:.1f}%")
    render_stat_row("Faltas Cometidas", get_avg(df_m, m_sel, 'Fouls_H', 'Fouls_A'), get_avg(df_v, v_sel, 'Fouls_H', 'Fouls_A'))

    st.divider()

    tab1, tab2, tab3 = st.tabs(["🕒 Últimos Jogos", "🏆 Tabela", "🎯 Pênaltis"])
    
    with tab1:
        c1, c2 = st.columns(2)
        cols_show = ['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']
        c1.write(f"Últimos de {m_sel}")
        c1.dataframe(df_m[cols_show], hide_index=True)
        c2.write(f"Últimos de {v_sel}")
        c2.dataframe(df_v[cols_show], hide_index=True)

    with tab2:
        tabela = calcular_tabela(df_l)
        if not tabela.empty:
            tabela['Objetivo'] = tabela.apply(lambda r: get_objetivo_txt(liga_sel, r['Pos']), axis=1)
            st.dataframe(tabela.sort_values('Pos'), use_container_width=True, hide_index=True)

    with tab3:
        st.write("Média de Pênaltis Ganhos")
        render_stat_row("Pênaltis", get_avg(df_m, m_sel, 'Penalties_Won_H', 'Penalties_Won_A'), get_avg(df_v, v_sel, 'Penalties_Won_H', 'Penalties_Won_A'))
