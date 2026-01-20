import streamlit as st
import pandas as pd
import numpy as np

# Função auxiliar para calcular estatísticas avançadas
def calcular_estatisticas_avancadas(serie):
    if len(serie) == 0:
        return {k: 0.0 for k in ["Média", "Mediana", "Moda", "Desvio Padrão", "CV (%)"]}
    
    media = serie.mean()
    mediana = serie.median()
    try:
        moda = serie.mode()[0] if not serie.mode().empty else 0
    except:
        moda = 0
    desvio = serie.std()
    cv = (desvio / media * 100) if media > 0 else 0
    
    return {
        "Média": media,
        "Mediana": mediana,
        "Moda": moda,
        "Desvio Padrão": desvio,
        "CV (%)": cv
    }

def mostrar_scout(df):
    st.title("🔎 Scout Estatístico Profissional")

    if 'Liga' not in df.columns:
        st.error("Erro de Colunas. Verifique o CSV.")
        return

    # --- 1. FILTROS ---
    c1, c2 = st.columns(2)
    
    # Filtro de Liga e Temporada
    ligas = sorted(df['Liga'].unique())
    liga_sel = c1.selectbox("Liga", ligas)
    
    df_liga = df[df['Liga'] == liga_sel].copy()
    temps = sorted(df_liga['Temporada'].unique(), reverse=True)
    temp_sel = c2.selectbox("Temporada", temps)
    
    # Base da Temporada Selecionada
    df_season = df_liga[df_liga['Temporada'] == temp_sel].copy()
    df_season['Data'] = pd.to_datetime(df_season['Data'], dayfirst=True, errors='coerce')

    # Seleção de Times
    times = sorted(df_season['Mandande'].unique())
    c3, c4 = st.columns(2)
    m_sel = c3.selectbox("Mandante (Casa)", times)
    v_sel = c4.selectbox("Visitante (Fora)", [t for t in times if t != m_sel])

    # BASES DE DADOS ESPECÍFICAS (Últimos 10 jogos)
    # Mandante jogando em CASA
    df_m_home = df_season[df_season['Mandande'] == m_sel].sort_values('Data', ascending=False).head(10)
    # Visitante jogando FORA
    df_v_away = df_season[df_season['Visitante'] == v_sel].sort_values('Data', ascending=False).head(10)
    
    # Bases Gerais (Últimos 10 jogos em qualquer mando)
    df_m_geral = df_season[(df_season['Mandande'] == m_sel) | (df_season['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(10)
    df_v_geral = df_season[(df_season['Mandande'] == v_sel) | (df_season['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(10)

    # --- 2. FORMA E H2H (ABAS) ---
    st.divider()
    st.subheader("📊 Forma e Histórico")
    
    tab_forma_especifica, tab_forma_geral, tab_h2h = st.tabs([
        "🏠 Forma (Casa vs Fora)", 
        "🌍 Forma Geral (Últimos 10)", 
        "⚔️ Confronto Direto (H2H)"
    ])

    # ABA 1: Forma Específica (Casa vs Fora)
    with tab_forma_especifica:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{m_sel} (Jogando em Casa)**")
            if df_m_home.empty:
                st.info("Sem jogos em casa.")
            for _, r in df_m_home.iterrows():
                gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
                res = "✅" if gm > gv else ("🟧" if gm == gv else "❌")
                st.write(f"{res} {r['Data'].strftime('%d/%m')} vs {r['Visitante']} ({int(gm)}x{int(gv)})")

        with col2:
            st.markdown(f"**{v_sel} (Jogando Fora)**")
            if df_v_away.empty:
                st.info("Sem jogos fora.")
            for _, r in df_v_away.iterrows():
                gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
                res = "✅" if gv > gm else ("🟧" if gm == gv else "❌")
                st.write(f"{res} {r['Data'].strftime('%d/%m')} vs {r['Mandande']} ({int(gm)}x{int(gv)})")

    # ABA 2: Forma Geral
    with tab_forma_geral:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**{m_sel} (Geral)**")
            for _, r in df_m_geral.iterrows():
                is_home = r['Mandande'] == m_sel
                gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
                placar_time = gm if is_home else gv
                placar_adv = gv if is_home else gm
                res = "✅" if placar_time > placar_adv else ("🟧" if placar_time == placar_adv else "❌")
                adv = r['Visitante'] if is_home else r['Mandande']
                mando = "🏠" if is_home else "✈️"
                st.write(f"{res} {r['Data'].strftime('%d/%m')} {mando} vs {adv} ({int(gm)}x{int(gv)})")

        with col2:
            st.markdown(f"**{v_sel} (Geral)**")
            for _, r in df_v_geral.iterrows():
                is_home = r['Mandande'] == v_sel
                gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
                placar_time = gm if is_home else gv
                placar_adv = gv if is_home else gm
                res = "✅" if placar_time > placar_adv else ("🟧" if placar_time == placar_adv else "❌")
                adv = r['Visitante'] if is_home else r['Mandande']
                mando = "🏠" if is_home else "✈️"
                st.write(f"{res} {r['Data'].strftime('%d/%m')} {mando} vs {adv} ({int(gm)}x{int(gv)})")

    # ABA 3: H2H (Confrontos Diretos)
    with tab_h2h:
        # H2H Específico (Mando de campo exato)
        h2h_especifico = df_liga[(df_liga['Mandande'] == m_sel) & (df_liga['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(10)
        # H2H Geral (Qualquer mando)
        h2h_geral = df_liga[((df_liga['Mandande'] == m_sel) & (df_liga['Visitante'] == v_sel)) | 
                            ((df_liga['Mandande'] == v_sel) & (df_liga['Visitante'] == m_sel))].sort_values('Data', ascending=False).head(10)

        c_h1, c_h2 = st.columns(2)
        with c_h1:
            st.markdown(f"**H2H na Casa do {m_sel}**")
            if h2h_especifico.empty:
                st.info("Nenhum registro recente.")
            for _, r in h2h_especifico.iterrows():
                st.write(f"📅 {r['Data'].strftime('%d/%m/%y')} | {r['Mandande']} {int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])} {r['Visitante']}")
        
        with c_h2:
            st.markdown("**H2H Geral (Qualquer Campo)**")
            if h2h_geral.empty:
                st.info("Nenhum registro recente.")
            for _, r in h2h_geral.iterrows():
                st.write(f"📅 {r['Data'].strftime('%d/%m/%y')} | {r['Mandande']} {int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])} {r['Visitante']}")

    # --- 3. ESTATÍSTICAS AVANÇADAS (QUADROS) ---
    st.divider()
    st.subheader("📈 Estatísticas Avançadas (Média, Mediana, Moda, DP, CV)")
    
    # Definição das Métricas
    # Tupla: (Nome Exibição, Coluna Mandante, Coluna Visitante)
    metricas = [
        ("Gols HT", "Gols_Mandante_HT", "Gols_Visitante_HT"),
        ("Gols FT", "Gols_Mandante_FT", "Gols_Visitante_FT"),
        ("Cantos", "Cantos_Mandante", "Cantos_Visitante"),
        ("Chutes ao Gol", "Chutes_Gol_Mandante", "Chutes_Gol_Visitante"),
        ("Chutes Fora", "Chutes_Fora_Mandante", "Chutes_Fora_Visitante"),
        ("Finalizações Totais", "Finalizações_Totais_Mandante", "Finalizações_Totais_Visitante")
    ]

    for nome_metrica, col_m, col_v in metricas:
        with st.expander(f"📊 Detalhes: {nome_metrica}", expanded=True):
            col_left, col_right = st.columns(2)
            
            # Mandante (Casa)
            with col_left:
                st.markdown(f"##### {m_sel} (Em Casa)")
                
                # Dados
                feitos = df_m_home[col_m]
                levados = df_m_home[col_v]
                total = feitos + levados
                
                df_stats_m = pd.DataFrame({
                    "Feitos": calcular_estatisticas_avancadas(feitos),
                    "Levados": calcular_estatisticas_avancadas(levados),
                    "Jogo (Total)": calcular_estatisticas_avancadas(total)
                }).T
                # Estilização Condicional
                st.dataframe(df_stats_m.style.format("{:.2f}").background_gradient(cmap="RdYlGn", subset=["Média", "Mediana"]), use_container_width=True)

            # Visitante (Fora)
            with col_right:
                st.markdown(f"##### {v_sel} (Fora)")
                
                # Dados (Invertidos para perspectiva do visitante)
                # O visitante "Faz" o que está na coluna Visitante e "Leva" o que está na coluna Mandante
                feitos = df_v_away[col_v]
                levados = df_v_away[col_m]
                total = feitos + levados
                
                df_stats_v = pd.DataFrame({
                    "Feitos": calcular_estatisticas_avancadas(feitos),
                    "Levados": calcular_estatisticas_avancadas(levados),
                    "Jogo (Total)": calcular_estatisticas_avancadas(total)
                }).T
                st.dataframe(df_stats_v.style.format("{:.2f}").background_gradient(cmap="RdYlGn", subset=["Média", "Mediana"]), use_container_width=True)

    # --- 4. ANÁLISE DE MINUTOS (TEMPORADA ATUAL) ---
    st.divider()
    st.subheader("⏰ Momento do Gol (Temporada Atual)")
    st.info("Soma de gols marcados por faixa de minutos na temporada atual.")

    faixas_m = ["0-15_Mandante", "16-30_Mandante", "31-45+_Mandante", "46-60_Mandante", "61-75_Mandante", "76-90+_Mandante"]
    faixas_v = ["0-15_Visitante", "16-30_Visitante", "31-45+_Visitante", "46-60_Visitante", "61-75_Visitante", "76-90+_Visitante"]
    labels = ["0-15'", "16-30'", "31-45+'", "46-60'", "61-75'", "76-90+'"]

    # Filtra todos os jogos do time na temporada (Casa e Fora para ter o dado completo ou apenas mando?)
    # O pedido foi "mandante jogando em casa e visitante fora". Vamos manter esse filtro.
    
    c_min1, c_min2 = st.columns(2)
    
    with c_min1:
        st.markdown(f"**{m_sel} (Em Casa)**")
        # Soma os gols em cada faixa
        soma_m = [df_m_home[f].sum() for f in faixas_m]
        df_faixa_m = pd.DataFrame([soma_m], columns=labels, index=["Gols"])
        # Destaque visual (Verde = mais gols, Vermelho = menos gols)
        st.dataframe(df_faixa_m.style.background_gradient(cmap="RdYlGn", axis=1).format("{:.0f}"), use_container_width=True)

    with c_min2:
        st.markdown(f"**{v_sel} (Fora)**")
        soma_v = [df_v_away[f].sum() for f in faixas_v]
        df_faixa_v = pd.DataFrame([soma_v], columns=labels, index=["Gols"])
        st.dataframe(df_faixa_v.style.background_gradient(cmap="RdYlGn", axis=1).format("{:.0f}"), use_container_width=True)
