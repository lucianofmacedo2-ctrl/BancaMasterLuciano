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
    if not df.empty:
        df['Pos_Geral'] = df[['P', 'V', 'SG']].apply(tuple, axis=1).rank(method='min', ascending=False)
    return df

def calcular_metricas_completas(series, prefixo):
    if len(series) == 0: return {f"{prefixo} Média": 0}
    return {
        f"{prefixo} Média": series.mean(),
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
    # Lógica para inverter colunas baseado em quem é o time analisado
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
    if df.empty: return st.error("O arquivo CSV está vazio ou não foi carregado corretamente.")
    
    # Padronização de Colunas (Remove espaços extras)
    df.columns = [c.strip() for c in df.columns]
    
    st.title("🔎 Scout de Elite - Master Luciano")
    
    # --- FILTROS ---
    df['Liga'] = df['Liga'].astype(str).str.strip().str.upper()
    c1, c2, c3 = st.columns(3)
    liga_sel = c1.selectbox("Selecione a Liga", sorted(df['Liga'].unique()))
    df_l = df[df['Liga'] == liga_sel].copy()
    temp_sel = c2.selectbox("Temporada", sorted(df_l['Temporada'].unique(), reverse=True))
    mando_sel = c3.selectbox("Filtro de Mando", ["Geral (Todos os Jogos)", "Apenas Casa/Fora"])
    
    df_s = df_l[df_l['Temporada'] == temp_sel].copy()
    times = sorted(df_s['Mandante'].unique())
    m_sel = st.selectbox("Mandante", times)
    v_sel = st.selectbox("Visitante", [t for t in times if t != m_sel])
    n_jogos = st.sidebar.slider("Amostragem de Jogos", 5, 50, 10)

    # --- CÁLCULO DE POSIÇÕES ---
    df_ranking = calcular_tabela_completa(df_s)
    try:
        pos_m = int(df_ranking[df_ranking['Time']==m_sel]['Pos_Geral'].values[0])
        pos_v = int(df_ranking[df_ranking['Time']==v_sel]['Pos_Geral'].values[0])
        st.info(f"📍 **{m_sel}** ({pos_m}º) vs **{v_sel}** ({pos_v}º)")
    except:
        st.warning("Não foi possível calcular o ranking com os dados atuais.")

    # Filtro de Amostragem
    if mando_sel == "Geral (Todos os Jogos)":
        df_m = df_s[(df_s['Mandante'] == m_sel) | (df_s['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(n_jogos)
        df_v = df_s[(df_s['Mandante'] == v_sel) | (df_s['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(n_jogos)
    else:
        df_m = df_s[df_s['Mandante'] == m_sel].sort_values('Data', ascending=False).head(n_jogos)
        df_v = df_s[df_s['Visitante'] == v_sel].sort_values('Data', ascending=False).head(n_jogos)

    # --- POWER STATS (MÉDIAS COMPARATIVAS) ---
    st.markdown("### 📊 Power Stats (Médias)")
    def get_avg(df_t, team, col_h, col_a):
        if col_h not in df_t.columns: return 0.0
        return np.where(df_t['Mandante']==team, df_t[col_h], df_t[col_a]).mean()

    # Renderizando barras de comparação baseadas nas colunas enviadas
    render_stat_row("EXPECTATIVA DE GOLS (xG)", get_avg(df_m, m_sel, 'xG_Mandante', 'xG_Visitante'), get_avg(df_v, v_sel, 'xG_Mandante', 'xG_Visitante'))
    render_stat_row("PONTOS POR JOGO (PPG)", get_avg(df_m, m_sel, 'PPG_H_Pre', 'PPG_A_Pre'), get_avg(df_v, v_sel, 'PPG_H_Pre', 'PPG_A_Pre'))
    render_stat_row("GOLS FT", get_avg(df_m, m_sel, 'Gols_Mandante_FT', 'Gols_Visitante_FT'), get_avg(df_v, v_sel, 'Gols_Mandante_FT', 'Gols_Visitante_FT'))
    render_stat_row("ATAQUES PERIGOSOS", get_avg(df_m, m_sel, 'DangerousAttacks_H', 'DangerousAttacks_A'), get_avg(df_v, v_sel, 'DangerousAttacks_H', 'DangerousAttacks_A'))
    render_stat_row("CHUTES NO GOL", get_avg(df_m, m_sel, 'ShotsOnTarget_H', 'ShotsOnTarget_A'), get_avg(df_v, v_sel, 'ShotsOnTarget_H', 'ShotsOnTarget_A'))
    render_stat_row("CANTOS TOTAIS FT", get_avg(df_m, m_sel, 'Corners_H', 'Corners_A'), get_avg(df_v, v_sel, 'Corners_H', 'Corners_A'))
    render_stat_row("CARTÕES TOTAIS", get_avg(df_m, m_sel, 'Total_Cards_H', 'Total_Cards_A'), get_avg(df_v, v_sel, 'Total_Cards_H', 'Total_Cards_A'))

    # --- ABAS DE DETALHAMENTO ---
    t_forma, t_stats, t_tecnico, t_class = st.tabs(["🕒 Histórico", "📊 Mercados FT/HT", "⚙️ Técnico & Pênaltis", "🏆 Classificação"])

    with t_forma:
        st.markdown("#### Últimos Confrontos")
        cols_hist = ['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante', 'Total_Corners']
        c_m, c_v = st.columns(2)
        c_m.markdown(f"**{m_sel}**")
        c_m.dataframe(df_m[cols_hist], hide_index=True)
        c_v.markdown(f"**{v_sel}**")
        c_v.dataframe(df_v[cols_hist], hide_index=True)

    with t_stats:
        gerar_tabela_segmentada(df_m, df_v, m_sel, v_sel, 'Gols_Mandante_FT', 'Gols_Visitante_FT', "⚽ Mercado de Gols FT")
        gerar_tabela_segmentada(df_m, df_v, m_sel, v_sel, 'Corners_H', 'Corners_A', "🚩 Mercado de Cantos FT")
        gerar_tabela_segmentada(df_m, df_v, m_sel, v_sel, 'Corners_H_HT', 'Corners_A_HT', "⏱️ Cantos HT (1º Tempo)")
        gerar_tabela_segmentada(df_m, df_v, m_sel, v_sel, 'Yellow_Cards_H', 'Yellow_Cards_A', "🟨 Cartões Amarelos")

    with t_tecnico:
        st.subheader("🛠️ Estatísticas Técnicas & Pênaltis")
        col_t1, col_t2 = st.columns(2)
        
        with col_t1:
            st.markdown(f"**{m_sel}**")
            st.write(f"Posse de Bola: **{get_avg(df_m, m_sel, 'Possession_H', 'Possession_A'):.1f}%**")
            st.write(f"Faltas Cometidas: **{get_avg(df_m, m_sel, 'Fouls_H', 'Fouls_A'):.1f}**")
            st.write(f"Impedimentos: **{get_avg(df_m, m_sel, 'Offsides_H', 'Offsides_A'):.1f}**")
            st.write(f"Pênaltis Ganhos: **{df_m['Penalties_Won_H'].sum() if 'Mandante' == m_sel else df_m['Penalties_Won_A'].sum():.0f}**")

        with col_t2:
            st.markdown(f"**{v_sel}**")
            st.write(f"Posse de Bola: **{get_avg(df_v, v_sel, 'Possession_H', 'Possession_A'):.1f}%**")
            st.write(f"Faltas Cometidas: **{get_avg(df_v, v_sel, 'Fouls_H', 'Fouls_A'):.1f}**")
            st.write(f"Impedimentos: **{get_avg(df_v, v_sel, 'Offsides_H', 'Offsides_A'):.1f}**")
            st.write(f"Pênaltis Ganhos: **{df_v['Penalties_Won_A'].sum() if 'Visitante' == v_sel else df_v['Penalties_Won_H'].sum():.0f}**")

    with t_class:
        st.subheader(f"Tabela - {liga_sel}")
        df_rank_show = df_ranking.sort_values('Pos_Geral').copy()
        df_rank_show['Objetivo'] = df_rank_show.apply(lambda r: get_objetivo_txt(liga_sel, r['Pos_Geral']), axis=1)
        st.dataframe(df_rank_show[['Pos_Geral', 'Time', 'P', 'J', 'V', 'SG', 'Objetivo']], use_container_width=True, hide_index=True)
