import streamlit as st
import pandas as pd
import numpy as np

# --- 1. FUNÇÕES DE APOIO E CÁLCULO ---

def calcular_tabela_classificacao(df_liga):
    """Gera a tabela de classificação baseada nos resultados do CSV"""
    stats = {}
    for _, row in df_liga.iterrows():
        m, v = row['Mandande'], row['Visitante']
        gm, gv = row['Gols_Mandante_FT'], row['Gols_Visitante_FT']
        
        for t in [m, v]:
            if t not in stats:
                stats[t] = {'P':0, 'J':0, 'V':0, 'E':0, 'D':0, 'GP':0, 'GC':0, 'P_Casa':0, 'J_Casa':0, 'P_Fora':0, 'J_Fora':0}
        
        stats[m]['J'] += 1; stats[v]['J'] += 1
        stats[m]['GP'] += gm; stats[m]['GC'] += gv
        stats[v]['GP'] += gv; stats[v]['GC'] += gm
        stats[m]['J_Casa'] += 1; stats[v]['J_Fora'] += 1

        if gm > gv:
            stats[m]['P'] += 3; stats[m]['V'] += 1; stats[m]['P_Casa'] += 3; stats[v]['D'] += 1
        elif gm == gv:
            stats[m]['P'] += 1; stats[v]['P'] += 1; stats[m]['E'] += 1; stats[v]['E'] += 1
            stats[m]['P_Casa'] += 1; stats[v]['P_Fora'] += 1
        else:
            stats[v]['P'] += 3; stats[v]['V'] += 1; stats[v]['P_Fora'] += 3; stats[m]['D'] += 1

    df_tab = pd.DataFrame.from_dict(stats, orient='index').reset_index().rename(columns={'index': 'Time'})
    df_tab['SG'] = df_tab['GP'] - df_tab['GC']
    return df_tab.sort_values(by=['P', 'V', 'SG'], ascending=False).reset_index(drop=True)

def calcular_stats_completas(serie):
    if serie.empty or serie.isnull().all():
        return {"Média": 0.0, "Mediana": 0.0, "Moda": 0.0, "DP": 0.0, "CV%": 0.0}
    s = serie.dropna()
    media = s.mean()
    mediana = s.median()
    try:
        moda = s.mode()[0] if not s.mode().empty else 0.0
    except:
        moda = 0.0
    desvio = s.std() if len(s) > 1 else 0.0
    cv = (desvio / media * 100) if media > 0 else 0.0
    return {"Média": media, "Mediana": mediana, "Moda": moda, "DP": desvio, "CV%": cv}

def calcular_wdl(df_games, time_nome):
    v, e, d = 0, 0, 0
    for _, row in df_games.iterrows():
        sou_m = row['Mandande'] == time_nome
        meus = row['Gols_Mandante_FT'] if sou_m else row['Gols_Visitante_FT']
        adv = row['Gols_Visitante_FT'] if sou_m else row['Gols_Mandante_FT']
        if meus > adv: v += 1
        elif meus == adv: e += 1
        else: d += 1
    return v, e, d

def formatar_data_seguro(valor):
    try:
        if pd.isnull(valor): return "N/D"
        return valor.strftime('%d/%m/%y')
    except:
        return "N/D"

def calcular_probabilidades_mercado(df):
    if df.empty: return pd.DataFrame()
    n = len(df)
    gols_st = df['Total_Gols_FT'] - df['Total_Gols_HT']
    data = {
        "Mercado": [
            "Ambas Marcam HT", "Ambas Marcam FT",
            "0.5 Gols HT", "1.5 Gols HT", "2.5 Gols HT", "3.5 Gols HT",
            "0.5 Gols FT", "1.5 Gols FT", "2.5 Gols FT", "3.5 Gols FT",
            "0.5 Gols ST", "1.5 Gols ST", "2.5 Gols ST", "3.5 Gols ST"
        ],
        "% Batido": [
            (len(df[(df['Gols_Mandante_HT'] > 0) & (df['Gols_Visitante_HT'] > 0)]) / n) * 100,
            (len(df[(df['Gols_Mandante_FT'] > 0) & (df['Gols_Visitante_FT'] > 0)]) / n) * 100,
            (len(df[df['Total_Gols_HT'] >= 0.5]) / n) * 100,
            (len(df[df['Total_Gols_HT'] >= 1.5]) / n) * 100,
            (len(df[df['Total_Gols_HT'] >= 2.5]) / n) * 100,
            (len(df[df['Total_Gols_HT'] >= 3.5]) / n) * 100,
            (len(df[df['Total_Gols_FT'] >= 0.5]) / n) * 100,
            (len(df[df['Total_Gols_FT'] >= 1.5]) / n) * 100,
            (len(df[df['Total_Gols_FT'] >= 2.5]) / n) * 100,
            (len(df[df['Total_Gols_FT'] >= 3.5]) / n) * 100,
            (len(df[gols_st >= 0.5]) / n) * 100,
            (len(df[gols_st >= 1.5]) / n) * 100,
            (len(df[gols_st >= 2.5]) / n) * 100,
            (len(df[gols_st >= 3.5]) / n) * 100,
        ]
    }
    return pd.DataFrame(data)

# --- 2. INTERFACE PRINCIPAL ---

def mostrar_scout(df):
    st.markdown("""<style>.stDataFrame div[data-testid="stTable"] { text-align: center; } [data-testid="stMetricValue"] { text-align: center; }</style>""", unsafe_allow_html=True)
    st.title("🚀 Scout Profissional & Inteligência de Mercado")
    df.columns = [c.strip() for c in df.columns]

    # --- FILTROS ---
    c1, c2 = st.columns(2)
    liga_sel = c1.selectbox("Selecione a Liga", sorted(df['Liga'].unique()))
    df_liga = df[df['Liga'] == liga_sel].copy()
    temp_sel = c2.selectbox("Temporada", sorted(df_liga['Temporada'].unique(), reverse=True))
    
    df_season = df_liga[df_liga['Temporada'] == temp_sel].copy()
    df_season['Data'] = pd.to_datetime(df_season['Data'], dayfirst=True, errors='coerce')

    # --- NOVO: POSIÇÃO NA CLASSIFICAÇÃO ---
    st.divider()
    tabela_ranking = calcular_tabela_classificacao(df_season)
    tab_casa = tabela_ranking[['Time', 'P_Casa', 'J_Casa']].sort_values(by='P_Casa', ascending=False).reset_index(drop=True)
    tab_fora = tabela_ranking[['Time', 'P_Fora', 'J_Fora']].sort_values(by='P_Fora', ascending=False).reset_index(drop=True)

    times = sorted(df_season['Mandande'].unique())
    c3, c4 = st.columns(2)
    m_sel = c3.selectbox("Mandante (Casa)", times)
    v_sel = c4.selectbox("Visitante (Fora)", [t for t in times if t != m_sel])

    # Encontrar posições
    try:
        pos_geral_m = tabela_ranking[tabela_ranking['Time'] == m_sel].index[0] + 1
        pos_casa_m = tab_casa[tab_casa['Time'] == m_sel].index[0] + 1
        pos_geral_v = tabela_ranking[tabela_ranking['Time'] == v_sel].index[0] + 1
        pos_fora_v = tab_fora[tab_fora['Time'] == v_sel].index[0] + 1
        st.info(f"🏆 **Posições na Tabela** | **{m_sel}**: {pos_geral_m}º Geral ({pos_casa_m}º em Casa) | **{v_sel}**: {pos_geral_v}º Geral ({pos_fora_v}º Fora)")
    except:
        st.warning("Dados insuficientes para calcular posições na tabela.")

    # BASES DE DADOS PARA ANÁLISE
    df_m_home = df_season[df_season['Mandande'] == m_sel].sort_values('Data', ascending=False).head(10)
    df_v_away = df_season[df_season['Visitante'] == v_sel].sort_values('Data', ascending=False).head(10)
    df_m_geral = df_season[(df_season['Mandande'] == m_sel) | (df_season['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(10)
    df_v_geral = df_season[(df_season['Mandande'] == v_sel) | (df_season['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(10)

    # --- CONTEXTO DA LIGA ---
    st.divider()
    media_gols_liga = df_season['Total_Gols_FT'].mean()
    col_l1, col_l2, col_l3 = st.columns(3)
    col_l1.metric("Média Gols da Liga", f"{media_gols_liga:.2f}")
    col_l2.metric(f"Média {m_sel}", f"{df_m_home['Gols_Mandante_FT'].mean():.2f}")
    col_l3.metric(f"Média {v_sel}", f"{df_v_away['Gols_Visitante_FT'].mean():.2f}")

    # --- APROVEITAMENTO WDL ---
    vm_h, em_h, dm_h = calcular_wdl(df_m_home, m_sel)
    vv_a, ev_a, dv_a = calcular_wdl(df_v_away, v_sel)
    col_res1, col_res2 = st.columns(2)
    with col_res1: st.info(f"**{m_sel} (Casa):** {vm_h}V | {em_h}E | {dm_h}D")
    with col_res2: st.info(f"**{v_sel} (Fora):** {vv_a}V | {ev_a}E | {dv_a}D")

    # --- TABELA DE PROBABILIDADES ---
    st.subheader("🎯 Frequência de Mercados (Últimos 10 Jogos)")
    df_prob_m = calcular_probabilidades_mercado(df_m_home)
    df_prob_v = calcular_probabilidades_mercado(df_v_away)
    cp1, cp2 = st.columns(2)
    with cp1:
        st.write(f"**Probabilidades {m_sel} (Casa)**")
        st.dataframe(df_prob_m.style.background_gradient(cmap="RdYlGn", subset=['% Batido']).format({"% Batido": "{:.1f}%"}), use_container_width=True)
    with cp2:
        st.write(f"**Probabilidades {v_sel} (Fora)**")
        st.dataframe(df_prob_v.style.background_gradient(cmap="RdYlGn", subset=['% Batido']).format({"% Batido": "{:.1f}%"}), use_container_width=True)

    # --- DEFESA E EFICIÊNCIA ---
    st.subheader("🛡️ Consistência Defensiva e Ataque")
    def extrair_eficiencia(df_jogos, mando="casa"):
        if df_jogos.empty: return 0, 0, 0, 0
        gols = df_jogos['Gols_Mandante_FT'].sum() if mando == "casa" else df_jogos['Gols_Visitante_FT'].sum()
        chutes = df_jogos['Chutes_Gol_Mandante'].sum() if mando == "casa" else df_jogos['Chutes_Gol_Visitante'].sum()
        gols_sofridos = df_jogos['Gols_Visitante_FT'] if mando == "casa" else df_jogos['Gols_Mandante_FT']
        cs = len(gols_sofridos[gols_sofridos == 0])
        gols_feitos = df_jogos['Gols_Mandante_FT'] if mando == "casa" else df_jogos['Gols_Visitante_FT']
        fts = len(gols_feitos[gols_feitos == 0])
        ch_por_gol = chutes / gols if gols > 0 else 0
        return cs, fts, ch_por_gol, gols

    cs_m, fts_m, ch_g_m, _ = extrair_eficiencia(df_m_home, "casa")
    cs_v, fts_v, ch_g_v, _ = extrair_eficiencia(df_v_away, "fora")

    ce1, ce2 = st.columns(2)
    with ce1: st.write(f"**{m_sel}**: 🧤 CS: {cs_m} | 🚫 FTS: {fts_m} | 🎯 Chutes p/ Gol: {ch_g_m:.1f}")
    with ce2: st.write(f"**{v_sel}**: 🧤 CS: {cs_v} | 🚫 FTS: {fts_v} | 🎯 Chutes p/ Gol: {ch_g_v:.1f}")

    # --- ABAS DE FORMA E H2H ---
    st.divider()
    tab_casa_fora, tab_geral, tab_h2h = st.tabs(["🏠 Casa vs Fora", "🌍 Geral (10)", "⚔️ H2H"])
    with tab_casa_fora:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{m_sel} (Casa)**")
            for _, r in df_m_home.iterrows():
                res = "✅" if r['Gols_Mandante_FT'] > r['Gols_Visitante_FT'] else ("🟧" if r['Gols_Mandante_FT'] == r['Gols_Visitante_FT'] else "❌")
                st.write(f"{res} {formatar_data_seguro(r['Data'])} vs {r['Visitante']} ({int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])})")
        with col2:
            st.markdown(f"**{v_sel} (Fora)**")
            for _, r in df_v_away.iterrows():
                res = "✅" if r['Gols_Visitante_FT'] > r['Gols_Mandante_FT'] else ("🟧" if r['Gols_Mandante_FT'] == r['Gols_Visitante_FT'] else "❌")
                st.write(f"{res} {formatar_data_seguro(r['Data'])} vs {r['Mandande']} ({int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])})")

    with tab_geral:
        col1, col2 = st.columns(2)
        with col1:
            vm_g, em_g, dm_g = calcular_wdl(df_m_geral, m_sel)
            st.markdown(f"**{m_sel}** ({vm_g}V-{em_g}E-{dm_g}D)")
            for _, r in df_m_geral.iterrows():
                sou_m = r['Mandande'] == m_sel
                meus, adv_g = (r['Gols_Mandante_FT'], r['Gols_Visitante_FT']) if sou_m else (r['Gols_Visitante_FT'], r['Gols_Mandante_FT'])
                res = "✅" if meus > adv_g else ("🟧" if meus == adv_g else "❌")
                st.write(f"{res} {formatar_data_seguro(r['Data'])} {'🏠' if sou_m else '✈️'} vs {r['Visitante'] if sou_m else r['Mandande']} ({int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])})")
        with col2:
            vv_g, ev_g, dv_g = calcular_wdl(df_v_geral, v_sel)
            st.markdown(f"**{v_sel}** ({vv_g}V-{ev_g}E-{dv_g}D)")
            for _, r in df_v_geral.iterrows():
                sou_m = r['Mandande'] == v_sel
                meus, adv_g = (r['Gols_Mandante_FT'], r['Gols_Visitante_FT']) if sou_m else (r['Gols_Visitante_FT'], r['Gols_Mandante_FT'])
                res = "✅" if meus > adv_g else ("🟧" if meus == adv_g else "❌")
                st.write(f"{res} {formatar_data_seguro(r['Data'])} {'🏠' if sou_m else '✈️'} vs {r['Visitante'] if sou_m else r['Mandande']} ({int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])})")

    with tab_h2h:
        h2h_casa = df_liga[(df_liga['Mandande'] == m_sel) & (df_liga['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(10)
        h2h_geral = df_liga[((df_liga['Mandande'] == m_sel) & (df_liga['Visitante'] == v_sel)) | ((df_liga['Mandande'] == v_sel) & (df_liga['Visitante'] == m_sel))].sort_values('Data', ascending=False).head(10)
        c_h1, c_h2 = st.columns(2)
        with c_h1:
            st.markdown(f"**H2H na Casa do {m_sel}**")
            for _, r in h2h_casa.iterrows(): st.write(f"📅 {formatar_data_seguro(r['Data'])} | {r['Mandande']} {int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])} {r['Visitante']}")
        with c_h2:
            st.markdown("**H2H Geral (Mandante/Visitante)**")
            for _, r in h2h_geral.iterrows(): st.write(f"📅 {formatar_data_seguro(r['Data'])} | {r['Mandande']} {int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])} {r['Visitante']}")

    # --- ESTATÍSTICAS AVANÇADAS ---
    st.divider()
    st.subheader("📈 Estatísticas Médias Detalhadas")
    metricas = {
        "Gols HT": ("Gols_Mandante_HT", "Gols_Visitante_HT"), 
        "Gols FT": ("Gols_Mandante_FT", "Gols_Visitante_FT"),
        "Cantos": ("Cantos_Mandante", "Cantos_Visitante"), 
        "Chutes Gol": ("Chutes_Gol_Mandante", "Chutes_Gol_Visitante"),
        "Chutes Fora": ("Chutes_Fora_Mandante", "Chutes_Fora_Visitante"),
        "Finalizações": ("Finalizações_Totais_Mandante", "Finalizações_Totais_Visitante")
    }

    for label, (col_m, col_v) in metricas.items():
        with st.expander(f"📊 {label}", expanded=True):
            m_col, v_col = st.columns(2)
            df_st_m = pd.DataFrame({
                "Feitos": calcular_stats_completas(df_m_home[col_m]), 
                "Levados": calcular_stats_completas(df_m_home[col_v]),
                "Total Jogo": calcular_stats_completas(df_m_home[col_m] + df_m_home[col_v])
            }).T
            df_st_v = pd.DataFrame({
                "Feitos": calcular_stats_completas(df_v_away[col_v]), 
                "Levados": calcular_stats_completas(df_v_away[col_m]),
                "Total Jogo": calcular_stats_completas(df_v_away[col_v] + df_v_away[col_m])
            }).T
            with m_col: st.dataframe(df_st_m.style.format("{:.2f}").background_gradient(cmap="RdYlGn", axis=0), use_container_width=True)
            with v_col: st.dataframe(df_st_v.style.format("{:.2f}").background_gradient(cmap="RdYlGn", axis=0), use_container_width=True)

    # --- MINUTOS ---
    st.divider()
    st.subheader("⏰ Somatório de Gols por Minutos")
    faixas_m = ["0-15_Mandante", "16-30_Mandante", "31-45+_Mandante", "46-60_Mandante", "61-75_Mandante", "76-90+_Mandante"]
    faixas_v = ["0-15_Visitante", "16-30_Visitante", "31-45+_Visitante", "46-60_Visitante", "61-75_Visitante", "76-90+_Visitante"]
    labels = ["0-15'", "16-30'", "31-45'", "46-60'", "61-75'", "76-90'"]
    c_m1, c_v1 = st.columns(2)
    with c_m1: st.dataframe(pd.DataFrame([df_m_home[faixas_m].sum().values], columns=labels, index=["Gols"]).style.background_gradient(cmap="RdYlGn", axis=1), use_container_width=True)
    with c_v1: st.dataframe(pd.DataFrame([df_v_away[faixas_v].sum().values], columns=labels, index=["Gols"]).style.background_gradient(cmap="RdYlGn", axis=1), use_container_width=True)
