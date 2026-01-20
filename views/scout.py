import streamlit as st
import pandas as pd
import numpy as np

def calcular_stats_completas(serie):
    """Calcula estatísticas com segurança contra erros."""
    if serie.empty or serie.isnull().all():
        return {"Média": 0, "Mediana": 0, "Moda": 0, "DP": 0, "CV%": 0}
    s = serie.dropna()
    media = s.mean()
    try:
        moda = s.mode()[0] if not s.mode().empty else 0
    except:
        moda = 0
    desvio = s.std()
    cv = (desvio / media * 100) if media > 0 else 0
    return {"Média": media, "Mediana": mediana, "Moda": moda, "DP": desvio, "CV%": cv}

def formatar_data_seguro(valor):
    try:
        if pd.isnull(valor): return "N/D"
        return valor.strftime('%d/%m/%y')
    except:
        return "N/D"

def mostrar_scout(df):
    st.title("🔎 Scout Estatístico Profissional")
    df.columns = [c.strip() for c in df.columns]

    # --- 1. FILTROS ---
    c1, c2 = st.columns(2)
    liga_sel = c1.selectbox("Liga", sorted(df['Liga'].unique()))
    df_liga = df[df['Liga'] == liga_sel].copy()
    
    temp_sel = c2.selectbox("Temporada", sorted(df_liga['Temporada'].unique(), reverse=True))
    df_season = df_liga[df_liga['Temporada'] == temp_sel].copy()
    df_season['Data'] = pd.to_datetime(df_season['Data'], dayfirst=True, errors='coerce')

    times = sorted(df_season['Mandande'].unique())
    c3, c4 = st.columns(2)
    m_sel = c3.selectbox("Mandante (Casa)", times)
    v_sel = c4.selectbox("Visitante (Fora)", [t for t in times if t != m_sel])

    # --- BASES DE DADOS ---
    # Específicas
    df_m_home = df_season[df_season['Mandande'] == m_sel].sort_values('Data', ascending=False).head(10)
    df_v_away = df_season[df_season['Visitante'] == v_sel].sort_values('Data', ascending=False).head(10)
    
    # GERAIS (Aqui pegamos todos os jogos do time na liga/temporada)
    df_m_geral = df_season[(df_season['Mandande'] == m_sel) | (df_season['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(10)
    df_v_geral = df_season[(df_season['Mandande'] == v_sel) | (df_season['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(10)

    # --- 2. ABAS DE FORMA E H2H ---
    st.divider()
    tab_casa_fora, tab_geral, tab_h2h = st.tabs(["🏠 Casa vs Fora", "🌍 Geral (10 jogos)", "⚔️ H2H"])

    with tab_casa_fora:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{m_sel} (Somente Casa)**")
            for _, r in df_m_home.iterrows():
                res = "✅" if r['Gols_Mandante_FT'] > r['Gols_Visitante_FT'] else ("🟧" if r['Gols_Mandante_FT'] == r['Gols_Visitante_FT'] else "❌")
                st.write(f"{res} {formatar_data_seguro(r['Data'])} vs {r['Visitante']} ({int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])})")
        with col2:
            st.markdown(f"**{v_sel} (Somente Fora)**")
            for _, r in df_v_away.iterrows():
                res = "✅" if r['Gols_Visitante_FT'] > r['Gols_Mandante_FT'] else ("🟧" if r['Gols_Mandante_FT'] == r['Gols_Visitante_FT'] else "❌")
                st.write(f"{res} {formatar_data_seguro(r['Data'])} vs {r['Mandande']} ({int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])})")

    with tab_geral:
        col1, col2 = st.columns(2)
        # Loop Geral Mandante
        with col1:
            st.markdown(f"**Últimos 10 Jogos: {m_sel}**")
            for _, r in df_m_geral.iterrows():
                sou_mandante = r['Mandande'] == m_sel
                adversario = r['Visitante'] if sou_mandante else r['Mandande']
                mando = "🏠" if sou_mandante else "✈️"
                # Lógica de resultado
                meus_gols = r['Gols_Mandante_FT'] if sou_mandante else r['Gols_Visitante_FT']
                gols_adv = r['Gols_Visitante_FT'] if sou_mandante else r['Gols_Mandante_FT']
                res = "✅" if meus_gols > gols_adv else ("🟧" if meus_gols == gols_adv else "❌")
                st.write(f"{res} {formatar_data_seguro(r['Data'])} {mando} vs {adversario} ({int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])})")
        
        # Loop Geral Visitante
        with col2:
            st.markdown(f"**Últimos 10 Jogos: {v_sel}**")
            for _, r in df_v_geral.iterrows():
                sou_mandante = r['Mandande'] == v_sel
                adversario = r['Visitante'] if sou_mandante else r['Mandande']
                mando = "🏠" if sou_mandante else "✈️"
                meus_gols = r['Gols_Mandante_FT'] if sou_mandante else r['Gols_Visitante_FT']
                gols_adv = r['Gols_Visitante_FT'] if sou_mandante else r['Gols_Mandante_FT']
                res = "✅" if meus_gols > gols_adv else ("🟧" if meus_gols == gols_adv else "❌")
                st.write(f"{res} {formatar_data_seguro(r['Data'])} {mando} vs {adversario} ({int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])})")

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

    # --- 3. ESTATÍSTICAS EM QUADROS ---
    st.divider()
    st.subheader("📈 Estatísticas Avançadas (Média, Mediana, Moda, DP, CV)")
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
            m1, v1 = st.columns(2)
            # Mandante
            m_feitos = df_m_home[col_m]
            m_levados = df_m_home[col_v]
            stats_m = pd.DataFrame({"Feitos": calcular_stats_completas(m_feitos), "Levados": calcular_stats_completas(m_levados), "Total Jogo": calcular_stats_completas(m_feitos + m_levados)}).T
            # Visitante
            v_feitos = df_v_away[col_v]
            v_levados = df_v_away[col_m]
            stats_v = pd.DataFrame({"Feitos": calcular_stats_completas(v_feitos), "Levados": calcular_stats_completas(v_levados), "Total Jogo": calcular_stats_completas(v_feitos + v_levados)}).T

            with m1:
                st.write(f"**{m_sel} (Casa)**")
                st.dataframe(stats_m.style.format("{:.2f}").background_gradient(cmap="RdYlGn", axis=0), use_container_width=True)
            with v1:
                st.write(f"**{v_sel} (Fora)**")
                st.dataframe(stats_v.style.format("{:.2f}").background_gradient(cmap="RdYlGn", axis=0), use_container_width=True)

    # --- 4. MINUTOS ---
    st.divider()
    st.subheader("⏰ Somatório de Gols por Minutos (Temporada Atual)")
    faixas_m = ["0-15_Mandante", "16-30_Mandante", "31-45+_Mandante", "46-60_Mandante", "61-75_Mandante", "76-90+_Mandante"]
    faixas_v = ["0-15_Visitante", "16-30_Visitante", "31-45+_Visitante", "46-60_Visitante", "61-75_Visitante", "76-90+_Visitante"]
    labels = ["0-15'", "16-30'", "31-45'", "46-60'", "61-75'", "76-90'"]

    c_min1, c_min2 = st.columns(2)
    with c_min1:
        soma_m = df_m_home[faixas_m].sum().values
        df_min_m = pd.DataFrame([soma_m], columns=labels, index=["Soma Gols"])
        st.write(f"**{m_sel}**")
        st.dataframe(df_min_m.style.background_gradient(cmap="RdYlGn", axis=1), use_container_width=True)
    with c_min2:
        soma_v = df_v_away[faixas_v].sum().values
        df_min_v = pd.DataFrame([soma_v], columns=labels, index=["Soma Gols"])
        st.write(f"**{v_sel}**")
        st.dataframe(df_min_v.style.background_gradient(cmap="RdYlGn", axis=1), use_container_width=True)
