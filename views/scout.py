import streamlit as st
import pandas as pd
import numpy as np

def calcular_stats_completas(serie):
    """Calcula estatísticas com segurança contra erros de definição."""
    if serie.empty or serie.isnull().all():
        return {"Média": 0.0, "Mediana": 0.0, "Moda": 0.0, "DP": 0.0, "CV%": 0.0}
    
    s = serie.dropna()
    media = s.mean()
    mediana = s.median() # <-- Aqui estava o erro, agora definido corretamente
    
    try:
        moda = s.mode()[0] if not s.mode().empty else 0.0
    except:
        moda = 0.0
        
    desvio = s.std() if len(s) > 1 else 0.0
    cv = (desvio / media * 100) if media > 0 else 0.0
    
    return {
        "Média": media, 
        "Mediana": mediana, 
        "Moda": moda, 
        "DP": desvio, 
        "CV%": cv
    }

def formatar_data_seguro(valor):
    try:
        if pd.isnull(valor): return "N/D"
        return valor.strftime('%d/%m/%y')
    except:
        return "N/D"

def mostrar_scout(df):
    st.title("🔎 Scout Estatístico Profissional")
    
    # Limpeza de nomes de colunas
    df.columns = [c.strip() for c in df.columns]

    # --- 1. FILTROS ---
    c1, c2 = st.columns(2)
    ligas = sorted(df['Liga'].unique())
    liga_sel = c1.selectbox("Selecione a Liga", ligas)
    
    df_liga = df[df['Liga'] == liga_sel].copy()
    temps = sorted(df_liga['Temporada'].unique(), reverse=True)
    temp_sel = c2.selectbox("Temporada", temps)
    
    # Base filtrada pela temporada atual
    df_season = df_liga[df_liga['Temporada'] == temp_sel].copy()
    df_season['Data'] = pd.to_datetime(df_season['Data'], dayfirst=True, errors='coerce')

    times = sorted(df_season['Mandande'].unique())
    c3, c4 = st.columns(2)
    m_sel = c3.selectbox("Mandante (Casa)", times)
    v_sel = c4.selectbox("Visitante (Fora)", [t for t in times if t != m_sel])

    # BASES DE DADOS (Últimos 10)
    df_m_home = df_season[df_season['Mandande'] == m_sel].sort_values('Data', ascending=False).head(10)
    df_v_away = df_season[df_season['Visitante'] == v_sel].sort_values('Data', ascending=False).head(10)
    
    df_m_geral = df_season[(df_season['Mandande'] == m_sel) | (df_season['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(10)
    df_v_geral = df_season[(df_season['Mandande'] == v_sel) | (df_season['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(10)

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
            st.markdown(f"**Geral: {m_sel}**")
            for _, r in df_m_geral.iterrows():
                sou_m = r['Mandande'] == m_sel
                meus = r['Gols_Mandante_FT'] if sou_m else r['Gols_Visitante_FT']
                adv = r['Gols_Visitante_FT'] if sou_m else r['Gols_Mandante_FT']
                res = "✅" if meus > adv else ("🟧" if meus == adv else "❌")
                st.write(f"{res} {formatar_data_seguro(r['Data'])} {'🏠' if sou_m else '✈️'} vs {r['Visitante'] if sou_m else r['Mandande']} ({int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])})")
        with col2:
            st.markdown(f"**Geral: {v_sel}**")
            for _, r in df_v_geral.iterrows():
                sou_m = r['Mandande'] == v_sel
                meus = r['Gols_Mandante_FT'] if sou_m else r['Gols_Visitante_FT']
                adv = r['Gols_Visitante_FT'] if sou_m else r['Gols_Mandante_FT']
                res = "✅" if meus > adv else ("🟧" if meus == adv else "❌")
                st.write(f"{res} {formatar_data_seguro(r['Data'])} {'🏠' if sou_m else '✈️'} vs {r['Visitante'] if sou_m else r['Mandande']} ({int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])})")

    with tab_h2h:
        h2h_casa = df_liga[(df_liga['Mandande'] == m_sel) & (df_liga['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(10)
        h2h_geral = df_liga[((df_liga['Mandande'] == m_sel) & (df_liga['Visitante'] == v_sel)) | ((df_liga['Mandande'] == v_sel) & (df_liga['Visitante'] == m_sel))].sort_values('Data', ascending=False).head(10)
        c_h1, c_h2 = st.columns(2)
        with c_h1:
            st.markdown(f"**H2H na Casa do {m_sel}**")
            for _, r in h2h_casa.iterrows():
                st.write(f"📅 {formatar_data_seguro(r['Data'])} | {r['Mandande']} {int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])} {r['Visitante']}")
        with c_h2:
            st.markdown("**H2H Geral**")
            for _, r in h2h_geral.iterrows():
                st.write(f"📅 {formatar_data_seguro(r['Data'])} | {r['Mandande']} {int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])} {r['Visitante']}")

    # --- 3. ESTATÍSTICAS AVANÇADAS EM QUADROS ---
    st.divider()
    st.subheader("📈 Estatísticas Detalhadas (Temporada Atual)")
    
    metricas = {
        "Gols HT": ("Gols_Mandante_HT", "Gols_Visitante_HT"),
        "Gols FT": ("Gols_Mandante_FT", "Gols_Visitante_FT"),
        "Cantos": ("Cantos_Mandante", "Cantos_Visitante"),
        "Chutes Gol": ("Chutes_Gol_Mandante", "Chutes_Gol_Visitante"),
        "Chutes Fora": ("Chutes_Fora_Mandante", "Chutes_Fora_Visitante"),
        "Finalizações": ("Finalizações_Totais_Mandante", "Finalizações_Totais_Visitante")
    }

    for label, (col_m, col_v) in metricas.items():
        with st.expander(f"📊 {label} (Feitos vs Levados)", expanded=True):
            m_col, v_col = st.columns(2)
            
            # Processamento Mandante
            m_f = df_m_home[col_m]
            m_l = df_m_home[col_v]
            df_st_m = pd.DataFrame({
                "Feitos": calcular_stats_completas(m_f),
                "Levados": calcular_stats_completas(m_l),
                "Total Jogo": calcular_stats_completas(m_f + m_l)
            }).T
            
            # Processamento Visitante
            v_f = df_v_away[col_v]
            v_l = df_v_away[col_m]
            df_st_v = pd.DataFrame({
                "Feitos": calcular_stats_completas(v_f),
                "Levados": calcular_stats_completas(v_l),
                "Total Jogo": calcular_stats_completas(v_f + v_l)
            }).T

            with m_col:
                st.write(f"**{m_sel} (Casa)**")
                st.dataframe(df_st_m.style.format("{:.2f}").background_gradient(cmap="RdYlGn", axis=0), use_container_width=True)
            with v_col:
                st.write(f"**{v_sel} (Fora)**")
                st.dataframe(df_st_v.style.format("{:.2f}").background_gradient(cmap="RdYlGn", axis=0), use_container_width=True)

    # --- 4. MINUTOS (SOMATÓRIO) ---
    st.divider()
    st.subheader("⏰ Somatório de Gols por Minutos")
    
    faixas_m = ["0-15_Mandante", "16-30_Mandante", "31-45+_Mandante", "46-60_Mandante", "61-75_Mandante", "76-90+_Mandante"]
    faixas_v = ["0-15_Visitante", "16-30_Visitante", "31-45+_Visitante", "46-60_Visitante", "61-75_Visitante", "76-90+_Visitante"]
    labels = ["0-15'", "16-30'", "31-45'", "46-60'", "61-75'", "76-90'"]

    c_m1, c_v1 = st.columns(2)
    with c_m1:
        s_m = df_m_home[faixas_m].sum()
        st.dataframe(pd.DataFrame([s_m.values], columns=labels, index=["Gols"]).style.background_gradient(cmap="RdYlGn", axis=1), use_container_width=True)
    with c_v1:
        s_v = df_v_away[faixas_v].sum()
        st.dataframe(pd.DataFrame([s_v.values], columns=labels, index=["Gols"]).style.background_gradient(cmap="RdYlGn", axis=1), use_container_width=True)
