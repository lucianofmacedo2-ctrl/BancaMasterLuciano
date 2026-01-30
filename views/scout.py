import streamlit as st
import pandas as pd
import numpy as np

# --- DICIONÁRIO DE REGRAS ATUALIZADO (Com novas ligas e objetivos) ---
REGRAS_LIGAS = {
    "BRAZIL 1": {"alvos": {"Libertadores": [1, 6], "Sul-Americana": [7, 12], "Rebaixamento": [17, 20]}},
    "BRAZIL 2": {"alvos": {"Acesso": [1, 4], "Rebaixamento": [17, 20]}},
    "PORTUGAL 3": {"alvos": {"Acesso": [1, 2], "Playoff Acesso": [3, 4], "Rebaixamento": [17, 20]}},
    "ENGLAND 1": {"alvos": {"Champions League": [1, 4], "Europa League": [5, 5], "Rebaixamento": [18, 20]}},
    "SPAIN 1": {"alvos": {"Champions League": [1, 4], "Europa League": [5, 6], "Rebaixamento": [18, 20]}},
    "ITALY 1": {"alvos": {"Champions League": [1, 4], "Europa League": [5, 6], "Rebaixamento": [18, 20]}},
    "GERMANY 1": {"alvos": {"Champions League": [1, 4], "Europa League": [5, 5], "Rebaixamento": [16, 18]}},
}

def get_objetivo_txt(liga, pos):
    liga_clean = str(liga).upper().strip()
    if liga_clean not in REGRAS_LIGAS: 
        return "⚪ Meio de Tabela"
    
    regras = REGRAS_LIGAS[liga_clean]["alvos"]
    for obj, faixa in regras.items():
        if faixa[0] <= pos <= faixa[1]:
            if any(x in obj for x in ["Rebaixamento", "Z-4"]):
                return f"🔴 {obj}"
            return f"🟢 {obj}"
    return "⚪ Meio de Tabela"

def render_stat_row(label, val_home, val_away):
    col1, col2, col3 = st.columns([1, 2, 1])
    v_h = float(val_home) if pd.notnull(val_home) else 0.0
    v_a = float(val_away) if pd.notnull(val_away) else 0.0
    total = abs(v_h) + abs(v_a)
    p_home = (v_h / total) if total > 0 else 0.5
    with col1: st.markdown(f"<p style='text-align: right; font-size: 18px; font-weight: bold; margin:0;'>{v_h:.2f}</p>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<p style='text-align: center; font-size: 11px; color: gray; margin:0;'>{label}</p>", unsafe_allow_html=True)
        st.progress(max(0.0, min(1.0, float(p_home))))
    with col3: st.markdown(f"<p style='text-align: left; font-size: 18px; font-weight: bold; margin:0;'>{v_a:.2f}</p>", unsafe_allow_html=True)

def calcular_tabela_classificacao(df_liga):
    stats = {}
    for _, row in df_liga.iterrows():
        m, v = row['Mandante'], row['Visitante']
        gm, gv = row.get('Gols_Mandante_FT', 0), row.get('Gols_Visitante_FT', 0)
        for t in [m, v]:
            if t not in stats: stats[t] = {'P':0, 'J':0, 'V':0, 'E':0, 'D':0, 'GP':0, 'GC':0}
        stats[m]['J'] += 1; stats[v]['J'] += 1
        stats[m]['GP'] += gm; stats[m]['GC'] += gv
        stats[v]['GP'] += gv; stats[v]['GC'] += gm
        if gm > gv: stats[m]['P'] += 3; stats[m]['V'] += 1
        elif gm == gv: stats[m]['P'] += 1; stats[v]['P'] += 1
        else: stats[v]['P'] += 3; stats[v]['V'] += 1
    df_tab = pd.DataFrame.from_dict(stats, orient='index').reset_index().rename(columns={'index': 'Time'})
    df_tab['SG'] = df_tab['GP'] - df_tab['GC']
    return df_tab.sort_values(by=['P', 'V', 'SG'], ascending=False).reset_index(drop=True)

def mostrar_scout(df):
    st.title("🔎 Scout Profissional")
    
    df['Liga'] = df['Liga'].astype(str).str.strip().str.upper()
    listagem_ligas = sorted([l for l in df['Liga'].unique() if l != 'NAN'])

    c1, c2 = st.columns(2)
    liga_sel = c1.selectbox("Selecione a Liga", listagem_ligas)
    
    df_liga = df[df['Liga'] == liga_sel].copy()
    temps = sorted(df_liga['Temporada'].astype(str).unique().tolist(), reverse=True)
    temp_sel = c2.selectbox("Temporada", temps)
    
    df_s = df_liga[df_liga['Temporada'].astype(str) == temp_sel].copy()
    df_s['Data'] = pd.to_datetime(df_s['Data'], errors='coerce')
    
    tab_class = calcular_tabela_classificacao(df_s)
    
    times = sorted(df_s['Mandante'].unique().tolist())
    m_sel = st.selectbox("Mandante", times)
    v_sel = st.selectbox("Visitante", [t for t in times if t != m_sel])

    n_jogos = st.radio("Jogos para Análise", ["5", "10", "Todos"], index=1, horizontal=True)

    def get_form(team):
        res = df_s[(df_s['Mandante'] == team) | (df_s['Visitante'] == team)].sort_values('Data', ascending=False)
        return res if n_jogos == "Todos" else res.head(int(n_jogos))

    df_m = get_form(m_sel)
    df_v = get_form(v_sel)

    st.divider()
    st.subheader(f"📊 Desempenho: {m_sel} vs {v_sel}")
    
    # Médias Reintegradas
    avg_gm = np.where(df_m['Mandante']==m_sel, df_m['Gols_Mandante_FT'], df_m['Gols_Visitante_FT']).mean()
    avg_gv = np.where(df_v['Mandante']==v_sel, df_v['Gols_Mandante_FT'], df_v['Gols_Visitante_FT']).mean()
    render_stat_row("MÉDIA GOLS MARCADOS", avg_gm, avg_gv)
    
    # Adicionando xG se disponível no seu novo CSV
    if 'xG_Mandante' in df.columns:
        avg_xg_m = np.where(df_m['Mandante']==m_sel, df_m['xG_Mandante'], df_m['xG_Visitante']).mean()
        avg_xg_v = np.where(df_v['Mandante']==v_sel, df_v['xG_Mandante'], df_v['xG_Visitante']).mean()
        render_stat_row("EXPECTATIVA DE GOLS (xG)", avg_xg_m, avg_xg_v)

    t1, t2, t3, t4, t5 = st.tabs(["🕒 Forma", "⚔️ H2H", "📊 Classificação", "📈 Stats Detalhadas", "⏰ Minutos"])
    
    with t1:
        c_m, c_v = st.columns(2)
        c_m.write(f"Últimos jogos: {m_sel}")
        c_m.dataframe(df_m[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], hide_index=True)
        c_v.write(f"Últimos jogos: {v_sel}")
        c_v.dataframe(df_v[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], hide_index=True)

    with t2:
        h2h = df[((df['Mandante'] == m_sel) & (df['Visitante'] == v_sel)) | ((df['Mandante'] == v_sel) & (df['Visitante'] == m_sel))].sort_values('Data', ascending=False)
        st.dataframe(h2h[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], hide_index=True)

    with t3:
        st.write(f"Classificação Atual - {liga_sel}")
        tab_display = tab_class.copy()
        tab_display.insert(0, 'Pos', range(1, len(tab_display) + 1))
        tab_display['Objetivo'] = [get_objetivo_txt(liga_sel, p) for p in tab_display['Pos']]
        st.dataframe(tab_display, use_container_width=True, hide_index=True)

    with t4:
        def calc_full(df_team, team_name):
            g_marc = np.where(df_team['Mandante'] == team_name, df_team['Gols_Mandante_FT'], df_team['Gols_Visitante_FT'])
            g_sofr = np.where(df_team['Mandante'] == team_name, df_team['Gols_Visitante_FT'], df_team['Gols_Mandante_FT'])
            return pd.DataFrame({
                "Média Marcados": [np.mean(g_marc)], "DP Marcados": [np.std(g_marc)],
                "Média Sofridos": [np.mean(g_sofr)], "DP Sofridos": [np.std(g_sofr)]
            }, index=[team_name])
        st.table(pd.concat([calc_full(df_m, m_sel), calc_full(df_v, v_sel)]))

    with t5:
        minutos = ['0-15_Mandante', '16-30_Mandante', '31-45+_Mandante', '46-60_Mandante', '61-75_Mandante', '76-90+_Mandante']
        if all(col in df.columns for col in minutos):
            st.bar_chart(df_m[minutos].mean())
