import streamlit as st
import pandas as pd
import numpy as np

# --- FUNÇÕES DE APOIO ---
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

# --- NOVA FUNÇÃO: PROBABILIDADES ---
def calcular_probabilidades_mercado(df_jogos):
    if df_jogos.empty: return {}
    n = len(df_jogos)
    btss = len(df_jogos[(df_jogos['Gols_Mandante_FT'] > 0) & (df_jogos['Gols_Visitante_FT'] > 0)])
    o05ht = len(df_jogos[df_jogos['Total_Gols_HT'] > 0.5])
    o15ft = len(df_jogos[df_jogos['Total_Gols_FT'] > 1.5])
    o25ft = len(df_jogos[df_jogos['Total_Gols_FT'] > 2.5])
    return {
        "Ambas Marcam": (btss/n)*100,
        "Over 0.5 HT": (o05ht/n)*100,
        "Over 1.5 FT": (o15ft/n)*100,
        "Over 2.5 FT": (o25ft/n)*100
    }

def mostrar_scout(df):
    st.title("🚀 Scout Profissional & Inteligência de Mercado")
    df.columns = [c.strip() for c in df.columns]

    # --- 1. FILTROS ---
    c1, c2 = st.columns(2)
    liga_sel = c1.selectbox("Selecione a Liga", sorted(df['Liga'].unique()))
    df_liga = df[df['Liga'] == liga_sel].copy()
    temp_sel = c2.selectbox("Temporada", sorted(df_liga['Temporada'].unique(), reverse=True))
    
    df_season = df_liga[df_liga['Temporada'] == temp_sel].copy()
    df_season['Data'] = pd.to_datetime(df_season['Data'], dayfirst=True, errors='coerce')

    times = sorted(df_season['Mandande'].unique())
    c3, c4 = st.columns(2)
    m_sel = c3.selectbox("Mandante (Casa)", times)
    v_sel = c4.selectbox("Visitante (Fora)", [t for t in times if t != m_sel])

    # BASES DE DADOS
    df_m_home = df_season[df_season['Mandande'] == m_sel].sort_values('Data', ascending=False).head(10)
    df_v_away = df_season[df_season['Visitante'] == v_sel].sort_values('Data', ascending=False).head(10)
    df_m_geral = df_season[(df_season['Mandande'] == m_sel) | (df_season['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(10)
    df_v_geral = df_season[(df_season['Mandande'] == v_sel) | (df_season['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(10)

    # --- NOVO: CONTEXTO DA LIGA ---
    st.divider()
    media_gols_liga = df_season['Total_Gols_FT'].mean()
    media_cantos_liga = df_season['Total_Cantos_FT'].mean()
    
    col_l1, col_l2, col_l3 = st.columns(3)
    col_l1.metric("Média Gols da Liga", f"{media_gols_liga:.2f}")
    col_l2.metric(f"Média Gols {m_sel}", f"{df_m_home['Gols_Mandante_FT'].mean():.2f}", delta=f"{df_m_home['Gols_Mandante_FT'].mean() - media_gols_liga/2:.2f}")
    col_l3.metric(f"Média Gols {v_sel}", f"{df_v_away['Gols_Visitante_FT'].mean():.2f}", delta=f"{df_v_away['Gols_Visitante_FT'].mean() - media_gols_liga/2:.2f}")

    # --- APROVEITAMENTO WDL ---
    vm_h, em_h, dm_h = calcular_wdl(df_m_home, m_sel)
    vv_a, ev_a, dv_a = calcular_wdl(df_v_away, v_sel)
    col_res1, col_res2 = st.columns(2)
    with col_res1: st.info(f"**{m_sel} (Casa):** {vm_h}V | {em_h}E | {dm_h}D")
    with col_res2: st.info(f"**{v_sel} (Fora):** {vv_a}V | {ev_a}E | {dv_a}D")

    # --- NOVO: PROBABILIDADES DE MERCADO ---
    st.subheader("🎯 Probabilidades de Mercado (Últimos 10 Jogos)")
    prob_m = calcular_probabilidades_mercado(df_m_home)
    prob_v = calcular_probabilidades_mercado(df_v_away)
    
    c_p1, c_p2 = st.columns(2)
    with c_p1:
        st.write(f"**Frequência {m_sel} (Casa)**")
        st.dataframe(pd.DataFrame(prob_m.items(), columns=['Mercado', '% Batido']).set_index('Mercado').T.style.background_gradient(cmap="RdYlGn", axis=1).format("{:.1f}%"))
    with c_p2:
        st.write(f"**Frequência {v_sel} (Fora)**")
        st.dataframe(pd.DataFrame(prob_v.items(), columns=['Mercado', '% Batido']).set_index('Mercado').T.style.background_gradient(cmap="RdYlGn", axis=1).format("{:.1f}%"))

    # --- NOVO: DEFESA E EFICIÊNCIA ---
    st.subheader("🛡️ Defesa e Eficiência")
    
    def extrair_eficiencia(df_jogos, time_nome, mando="casa"):
        if df_jogos.empty: return 0, 0, 0, 0
        gols = df_jogos['Gols_Mandante_FT'].sum() if mando == "casa" else df_jogos['Gols_Visitante_FT'].sum()
        chutes = df_jogos['Chutes_Gol_Mandante'].sum() if mando == "casa" else df_jogos['Chutes_Gol_Visitante'].sum()
        cantos = df_jogos['Cantos_Mandante'].sum() if mando == "casa" else df_jogos['Cantos_Visitante'].sum()
        
        # Clean Sheets
        gols_sofridos = df_jogos['Gols_Visitante_FT'] if mando == "casa" else df_jogos['Gols_Mandante_FT']
        cs = len(gols_sofridos[gols_sofridos == 0])
        # Failed to Score
        gols_feitos = df_jogos['Gols_Mandante_FT'] if mando == "casa" else df_jogos['Gols_Visitante_FT']
        fts = len(gols_feitos[gols_feitos == 0])
        
        ch_por_gol = chutes / gols if gols > 0 else 0
        can_por_gol = cantos / gols if gols > 0 else 0
        return cs, fts, ch_por_gol, can_por_gol

    cs_m, fts_m, ch_g_m, can_g_m = extrair_eficiencia(df_m_home, m_sel, "casa")
    cs_v, fts_v, ch_g_v, can_g_v = extrair_eficiencia(df_v_away, v_sel, "fora")

    c_e1, c_e2 = st.columns(2)
    with c_e1:
        st.write(f"**Consistência {m_sel}**")
        st.write(f"🧤 Clean Sheets: **{cs_m}** | 🚫 Falhou em Marcar: **{fts_m}**")
        st.write(f"🎯 Chutes p/ marcar 1 gol: **{ch_g_m:.1f}**")
    with c_e2:
        st.write(f"**Consistência {v_sel}**")
        st.write(f"🧤 Clean Sheets: **{cs_v}** | 🚫 Falhou em Marcar: **{fts_v}**")
        st.write(f"🎯 Chutes p/ marcar 1 gol: **{ch_g_v:.1f}**")

    # --- 2. ABAS DE FORMA E H2H ---
    st.divider()
    tab_casa_fora, tab_geral, tab_h2h = st.tabs(["🏠 Casa vs Fora", "🌍 Geral (Últimos 10)", "⚔️ H2H"])
    with tab_casa_fora:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{m_sel} (Jogos em Casa)**")
            for _, r in df_m_home.iterrows():
                res = "✅" if r['Gols_Mandante_FT'] > r['Gols_Visitante_FT'] else ("🟧" if r['Gols_Mandante_FT'] == r['Gols_Visitante_FT'] else "❌")
                st.write(f"{res} {formatar_data_seguro(r['Data'])} vs {r['Visitante']} ({int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])})")
        with col2:
            st.markdown(f"**{v_sel} (Jogos Fora)**")
            for _, r in df_v_away.iterrows():
                res = "✅" if r['Gols_Visitante_FT'] > r['Gols_Mandante_FT'] else ("🟧" if r['Gols_Mandante_FT'] == r['Gols_Visitante_FT'] else "❌")
                st.write(f"{res} {formatar_data_seguro(r['Data'])} vs {r['Mandande']} ({int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])})")

    with tab_geral:
        col1, col2 = st.columns(2)
        with col1:
            vm_g, em_g, dm_g = calcular_wdl(df_m_geral, m_sel)
            st.markdown(f"**Geral: {m_sel}** ({vm_g}V-{em_g}E-{dm_g}D)")
            for _, r in df_m_geral.iterrows():
                sou_m = r['Mandande'] == m_sel
                meus, adv_g = (r['Gols_Mandante_FT'], r['Gols_Visitante_FT']) if sou_m else (r['Gols_Visitante_FT'], r['Gols_Mandante_FT'])
                res = "✅" if meus > adv_g else ("🟧" if meus == adv_g else "❌")
                st.write(f"{res} {formatar_data_seguro(r['Data'])} {'🏠' if sou_m else '✈️'} vs {r['Visitante'] if sou_m else r['Mandande']} ({int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])})")
        with col2:
            vv_g, ev_g, dv_g = calcular_wdl(df_v_geral, v_sel)
            st.markdown(f"**Geral: {v_sel}** ({vv_g}V-{ev_g}E-{dv_g}D)")
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
            st.markdown("**H2H na Casa**")
            for _, r in h2h_casa.iterrows(): st.write(f"📅 {formatar_data_seguro(r['Data'])} | {r['Mandande']} {int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])} {r['Visitante']}")
        with c_h2:
            st.markdown("**H2H Geral**")
            for _, r in h2h_geral.iterrows(): st.write(f"📅 {formatar_data_seguro(r['Data'])} | {r['Mandande']} {int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])} {r['Visitante']}")

    # --- 3. ESTATÍSTICAS AVANÇADAS EM QUADROS ---
    st.divider()
    st.subheader("📈 Estatísticas Detalhadas (Temporada Atual)")
    metricas = {
        "Gols HT": ("Gols_Mandante_HT", "Gols_Visitante_HT"), "Gols FT": ("Gols_Mandante_FT", "Gols_Visitante_FT"),
        "Cantos": ("Cantos_Mandante", "Cantos_Visitante"), "Chutes Gol": ("Chutes_Gol_Mandante", "Chutes_Gol_Visitante"),
        "Chutes Fora": ("Chutes_Fora_Mandante", "Chutes_Fora_Visitante"), "Finalizações": ("Finalizações_Totais_Mandante", "Finalizações_Totais_Visitante")
    }

    for label, (col_m, col_v) in metricas.items():
        with st.expander(f"📊 {label} (Feitos vs Levados)", expanded=True):
            m_col, v_col = st.columns(2)
            # Mandante
            m_f, m_l = df_m_home[col_m], df_m_home[col_v]
            df_st_m = pd.DataFrame({"Feitos": calcular_stats_completas(m_f), "Levados": calcular_stats_completas(m_l), "Total Jogo": calcular_stats_completas(m_f + m_l)}).T
            # Visitante
            v_f, v_l = df_v_away[col_v], df_v_away[col_m]
            df_st_v = pd.DataFrame({"Feitos": calcular_stats_completas(v_f), "Levados": calcular_stats_completas(v_l), "Total Jogo": calcular_stats_completas(v_f + v_l)}).T
            with m_col:
                st.write(f"**{m_sel} (Casa)**")
                st.dataframe(df_st_m.style.format("{:.2f}").background_gradient(cmap="RdYlGn", axis=0), use_container_width=True)
            with v_col:
                st.write(f"**{v_sel} (Fora)**")
                st.dataframe(df_st_v.style.format("{:.2f}").background_gradient(cmap="RdYlGn", axis=0), use_container_width=True)

    # --- 4. MINUTOS ---
    st.divider()
    st.subheader("⏰ Somatório de Gols por Minutos")
    faixas_m = ["0-15_Mandante", "16-30_Mandante", "31-45+_Mandante", "46-60_Mandante", "61-75_Mandante", "76-90+_Mandante"]
    faixas_v = ["0-15_Visitante", "16-30_Visitante", "31-45+_Visitante", "46-60_Visitante", "61-75_Visitante", "76-90+_Visitante"]
    labels = ["0-15'", "16-30'", "31-45'", "46-60'", "61-75'", "76-90'"]
    c_m1, c_v1 = st.columns(2)
    with c_m1:
        st.write(f"**Minutos Gols: {m_sel}**")
        st.dataframe(pd.DataFrame([df_m_home[faixas_m].sum().values], columns=labels, index=["Gols"]).style.background_gradient(cmap="RdYlGn", axis=1), use_container_width=True)
    with c_v1:
        st.write(f"**Minutos Gols: {v_sel}**")
        st.dataframe(pd.DataFrame([df_v_away[faixas_v].sum().values], columns=labels, index=["Gols"]).style.background_gradient(cmap="RdYlGn", axis=1), use_container_width=True)
