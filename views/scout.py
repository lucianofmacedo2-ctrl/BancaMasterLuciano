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

# --- FUNÇÕES DE CÁLCULO ---
def get_objetivo_txt(liga, pos):
    liga_clean = str(liga).upper().strip()
    if liga_clean not in REGRAS_LIGAS: return "⚪ Meio"
    regras = REGRAS_LIGAS[liga_clean]["alvos"]
    for obj, faixa in regras.items():
        if faixa[0] <= pos <= faixa[1]:
            return f"{'🔴' if 'Rebaixamento' in obj else '🟢'} {obj}"
    return "⚪ Meio"

def calcular_tabela_completa(df_liga):
    stats = {}
    for _, r in df_liga.iterrows():
        m, v = r['Mandante'], r['Visitante']
        gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
        for t in [m, v]:
            if t not in stats:
                stats[t] = {'P':0,'J':0,'V':0,'SG':0, 'P_Casa':0,'J_Casa':0, 'P_Fora':0,'J_Fora':0}
        
        stats[m]['J']+=1; stats[v]['J']+=1
        stats[m]['SG']+=(gm-gv); stats[v]['SG']+=(gv-gm)
        stats[m]['J_Casa']+=1; stats[v]['J_Fora']+=1
        
        if gm > gv: 
            stats[m]['P']+=3; stats[m]['V']+=1; stats[m]['P_Casa']+=3
        elif gm == gv: 
            stats[m]['P']+=1; stats[v]['P']+=1; stats[m]['P_Casa']+=1; stats[v]['P_Fora']+=1
        else: 
            stats[v]['P']+=3; stats[v]['V']+=1; stats[v]['P_Fora']+=3
            
    df = pd.DataFrame.from_dict(stats, orient='index').reset_index().rename(columns={'index':'Time'})
    df['Pos_Geral'] = df[['P', 'V', 'SG']].apply(tuple, axis=1).rank(method='min', ascending=False)
    df['Pos_Casa'] = df[['P_Casa', 'J_Casa']].apply(tuple, axis=1).rank(method='min', ascending=False)
    df['Pos_Fora'] = df[['P_Fora', 'J_Fora']].apply(tuple, axis=1).rank(method='min', ascending=False)
    return df

def calcular_metricas_completas(series, prefixo):
    if len(series) == 0:
        return {f"{prefixo} Média": 0, f"{prefixo} DP": 0}
    return {
        f"{prefixo} Média": series.mean(),
        f"{prefixo} Mediana": series.median(),
        f"{prefixo} Moda": series.mode().iloc[0] if not series.mode().empty else series.mean(),
        f"{prefixo} DP": series.std(),
        f"{prefixo} CV%": (series.std() / series.mean() * 100) if series.mean() != 0 else 0,
        f"{prefixo} 0.5+ (%)": (series > 0.5).mean() * 100,
        f"{prefixo} 1.5+ (%)": (series > 1.5).mean() * 100,
        f"{prefixo} 2.5+ (%)": (series > 2.5).mean() * 100,
    }

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

def extrair_dados_mercado(df_team, team, col_h, col_a):
    feitos = np.where(df_team['Mandante'] == team, df_team[col_h], df_team[col_a])
    sofridos = np.where(df_team['Mandante'] == team, df_team[col_a], df_team[col_h])
    return pd.Series(feitos), pd.Series(sofridos), pd.Series(feitos + sofridos)

def gerar_tabela_segmentada(df_m, df_v, m_sel, v_sel, col_h, col_a, titulo):
    fm, sm, tm = extrair_dados_mercado(df_m, m_sel, col_h, col_a)
    fv, sv, tv = extrair_dados_mercado(df_v, v_sel, col_h, col_a)
    dados = []
    for t_name, f, s, t in [(m_sel, fm, sm, tm), (v_sel, fv, sv, tv)]:
        row = {"Equipe": t_name}
        row.update(calcular_metricas_completas(f, "Feitos"))
        row.update(calcular_metricas_completas(s, "Sofridos"))
        row.update(calcular_metricas_completas(t, "Total"))
        if "Gols" in titulo: row["BTTS Sim (%)"] = ((f > 0) & (s > 0)).mean() * 100
        dados.append(row)
    st.markdown(f"#### {titulo}")
    st.dataframe(pd.DataFrame(dados).set_index("Equipe").T, use_container_width=True)

def mostrar_scout(df):
    if df.empty: return st.error("CSV vazio")
    
    st.title("🔎 Scout de Elite - Master Luciano")
    
    # --- FILTROS ---
    df['Liga'] = df['Liga'].astype(str).str.strip().str.upper()
    c1, c2, c3 = st.columns(3)
    liga_sel = c1.selectbox("Liga", sorted(df['Liga'].unique()))
    df_l = df[df['Liga'] == liga_sel].copy()
    temp_sel = c2.selectbox("Temporada", sorted(df_l['Temporada'].unique(), reverse=True))
    mando_sel = c3.selectbox("Filtro de Mando", ["Geral (Todos)", "Casa/Fora Específico"])
    
    df_s = df_l[df_l['Temporada'] == temp_sel].copy()
    times = sorted(df_s['Mandante'].unique())
    m_sel = st.selectbox("Mandante", times)
    v_sel = st.selectbox("Visitante", [t for t in times if t != m_sel])
    n_jogos = st.sidebar.slider("Amostragem de Jogos", 5, 50, 10)

    # --- CÁLCULO DE POSIÇÕES ---
    df_ranking = calcular_tabela_completa(df_s)
    pos_m_geral = int(df_ranking[df_ranking['Time']==m_sel]['Pos_Geral'].values[0])
    pos_m_casa = int(df_ranking[df_ranking['Time']==m_sel]['Pos_Casa'].values[0])
    pos_v_geral = int(df_ranking[df_ranking['Time']==v_sel]['Pos_Geral'].values[0])
    pos_v_fora = int(df_ranking[df_ranking['Time']==v_sel]['Pos_Fora'].values[0])

    st.info(f"📍 **{m_sel}**: {pos_m_geral}º Geral | {pos_m_casa}º em Casa --- **{v_sel}**: {pos_v_geral}º Geral | {pos_v_fora}º Fora")

    if mando_sel == "Geral (Todos)":
        df_m = df_s[(df_s['Mandante'] == m_sel) | (df_s['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(n_jogos)
        df_v = df_s[(df_s['Mandante'] == v_sel) | (df_s['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(n_jogos)
    else:
        df_m = df_s[df_s['Mandante'] == m_sel].sort_values('Data', ascending=False).head(n_jogos)
        df_v = df_s[df_s['Visitante'] == v_sel].sort_values('Data', ascending=False).head(n_jogos)

    # --- POWER STATS (MÉDIAS RECONFIGURADAS COM NOVAS COLUNAS) ---
    st.markdown("### 📊 Power Stats (Médias)")
    
    def get_avg(df_t, team, col_h, col_a):
        if col_h not in df_t.columns: return 0.0
        return np.where(df_t['Mandante']==team, df_t[col_h], df_t[col_a]).mean()

    # BLOCO 1: Gols e xG
    render_stat_row("EXPECTATIVA DE GOLS (xG)", get_avg(df_m, m_sel, 'xG_Mandante', 'xG_Visitante'), get_avg(df_v, v_sel, 'xG_Mandante', 'xG_Visitante'))
    render_stat_row("PONTOS POR JOGO (PPG)", get_avg(df_m, m_sel, 'PPG_H_Pre', 'PPG_A_Pre'), get_avg(df_v, v_sel, 'PPG_H_Pre', 'PPG_A_Pre'))
    render_stat_row("GOLS FT", get_avg(df_m, m_sel, 'Gols_Mandante_FT', 'Gols_Visitante_FT'), get_avg(df_v, v_sel, 'Gols_Mandante_FT', 'Gols_Visitante_FT'))
    
    # BLOCO 2: Pressão e Ataque
    render_stat_row("ATAQUES PERIGOSOS", get_avg(df_m, m_sel, 'DangerousAttacks_H', 'DangerousAttacks_A'), get_avg(df_v, v_sel, 'DangerousAttacks_H', 'DangerousAttacks_A'))
    render_stat_row("FINALIZAÇÕES (CHUTES)", get_avg(df_m, m_sel, 'Shots_H', 'Shots_A'), get_avg(df_v, v_sel, 'Shots_H', 'Shots_A'))
    render_stat_row("CHUTES NO GOL", get_avg(df_m, m_sel, 'ShotsOnTarget_H', 'ShotsOnTarget_A'), get_avg(df_v, v_sel, 'ShotsOnTarget_H', 'ShotsOnTarget_A'))
    
    # BLOCO 3: Cantos e Disciplina
    render_stat_row("CANTOS TOTAIS FT", get_avg(df_m, m_sel, 'Corners_H', 'Corners_A'), get_avg(df_v, v_sel, 'Corners_H', 'Corners_A'))
    render_stat_row("CARTÕES (TOTAL)", get_avg(df_m, m_sel, 'Total_Cards_H', 'Total_Cards_A'), get_avg(df_v, v_sel, 'Total_Cards_H', 'Total_Cards_A'))
    render_stat_row("FALTAS", get_avg(df_m, m_sel, 'Fouls_H', 'Fouls_A'), get_avg(df_v, v_sel, 'Fouls_H', 'Fouls_A'))

    # --- ABAS DE ANÁLISE ---
    t_forma, t_stats, t_minutos, t_class = st.tabs(["🕒 Forma", "📊 Stats Detalhadas", "⏰ Minutos", "🏆 Tabela"])

    with t_forma:
        st.markdown("#### Histórico Recente")
        c_m, c_v = st.columns(2)
        cols_hist = ['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante', 'Total_Corners']
        c_m.dataframe(df_m[cols_hist], hide_index=True)
        c_v.dataframe(df_v[cols_hist], hide_index=True)

    with t_stats:
        # Gols e xG
        gerar_tabela_segmentada(df_m, df_v, m_sel, v_sel, 'Gols_Mandante_FT', 'Gols_Visitante_FT', "⚽ Gols FT")
        gerar_tabela_segmentada(df_m, df_v, m_sel, v_sel, 'xG_Mandante', 'xG_Visitante', "📈 xG (Gols Esperados)")
        
        # Cantos Detalhados
        gerar_tabela_segmentada(df_m, df_v, m_sel, v_sel, 'Corners_H', 'Corners_A', "🚩 Cantos FT")
        gerar_tabela_segmentada(df_m, df_v, m_sel, v_sel, 'Corners_H_HT', 'Corners_A_HT', "⏱️ Cantos HT")
        
        # Disciplina Detalhada
        gerar_tabela_segmentada(df_m, df_v, m_sel, v_sel, 'Yellow_Cards_H', 'Yellow_Cards_A', "🟨 Cartões Amarelos")
        gerar_tabela_segmentada(df_m, df_v, m_sel, v_sel, 'Fouls_H', 'Fouls_A', "🚫 Faltas")
        
        # Técnico
        gerar_tabela_segmentada(df_m, df_v, m_sel, v_sel, 'Possession_H', 'Possession_A', "⚽ Posse de Bola")
        gerar_tabela_segmentada(df_m, df_v, m_sel, v_sel, 'Throwins_H', 'Throwins_A', "👐 Laterais (Throw-ins)")

    with t_minutos:
        faixas = ['0-15', '16-30', '31-45+', '46-60', '61-75', '76-90+']
        def calc_min(df_t, team):
            data = []
            for f in faixas:
                col_h, col_a = f"{f}_Mandante", f"{f}_Visitante"
                if col_h in df_t.columns:
                    f_g = np.where(df_t['Mandante']==team, df_t[col_h], df_t[col_a]).sum()
                    s_g = np.where(df_t['Mandante']==team, df_t[col_a], df_t[col_h]).sum()
                    data.append({"Minutos": f, "Feitos": f_g, "Sofridos": s_g, "Total": f_g+s_g})
            return pd.DataFrame(data)
        cm1, cm2 = st.columns(2)
        cm1.markdown(f"**Gols por Minuto - {m_sel}**")
        cm1.table(calc_min(df_m, m_sel))
        cm2.markdown(f"**Gols por Minuto - {v_sel}**")
        cm2.table(calc_min(df_v, v_sel))

    with t_class:
        st.subheader(f"Classificação: {liga_sel}")
        df_rank_show = df_ranking.sort_values('Pos_Geral').copy()
        df_rank_show['Objetivo'] = df_rank_show.apply(lambda r: get_objetivo_txt(liga_sel, r['Pos_Geral']), axis=1)
        st.dataframe(df_rank_show[['Pos_Geral', 'Time', 'P', 'J', 'V', 'SG', 'Objetivo']], use_container_width=True, hide_index=True)
        
        st.divider()
        st.subheader("🎯 Especial Pênaltis")
        col_pen1, col_pen2 = st.columns(2)
        with col_pen1:
            st.write(f"**{m_sel}**")
            st.write(f"Pênaltis a Favor: {df_m[['Penalties_Won_H', 'Penalties_Won_A']].values.sum():.0f}")
            st.write(f"Gols de Pênalti: {df_m[['Penalties_Goals_H', 'Penalties_Goals_A']].values.sum():.0f}")
        with col_pen2:
            st.write(f"**{v_sel}**")
            st.write(f"Pênaltis a Favor: {df_v[['Penalties_Won_H', 'Penalties_Won_A']].values.sum():.0f}")
            st.write(f"Gols de Pênalti: {df_v[['Penalties_Goals_H', 'Penalties_Goals_A']].values.sum():.0f}")
