import streamlit as st
import pandas as pd
import numpy as np

def mostrar_scout(df):
    st.title("🔎 Scout Estatístico Avançado")
    
    if df.empty:
        st.error("A base de dados está vazia.")
        return

    # --- 1. FILTROS ---
    try:
        c1, c2 = st.columns(2)
        
        # Correção: Usando 'Liga' em vez de 'pais'
        lista_ligas = sorted(df['Liga'].unique())
        liga_sel = c1.selectbox("Selecione a Liga", lista_ligas)
        
        df_liga = df[df['Liga'] == liga_sel].copy()
        
        lista_temps = sorted(df_liga['Temporada'].unique(), reverse=True)
        temp_sel = c2.selectbox("Temporada", lista_temps)
        
        df_filt = df_liga[df_liga['Temporada'] == temp_sel].copy()
        df_filt['Data'] = pd.to_datetime(df_filt['Data'], dayfirst=True, errors='coerce')

        # Seleção de Times (Usando 'Mandande' conforme seu CSV)
        times = sorted(df_filt['Mandande'].unique())
        c3, c4 = st.columns(2)
        m_sel = c3.selectbox("Mandante (Casa)", times)
        v_sel = c4.selectbox("Visitante (Fora)", [t for t in times if t != m_sel])

        # --- BASES DE DADOS (Últimos 10 jogos) ---
        df_m_casa = df_filt[df_filt['Mandande'] == m_sel].sort_values('Data', ascending=False).head(10)
        df_v_fora = df_filt[df_filt['Visitante'] == v_sel].sort_values('Data', ascending=False).head(10)

        # --- 2. ABAS DE FORMA E H2H ---
        st.divider()
        tab_forma, tab_minutos, tab_stats = st.tabs(["📊 Forma Recente", "⏰ Gols por Minuto", "📉 Estatísticas"])

        with tab_forma:
            f1, f2 = st.columns(2)
            for col, time, dados, is_home_filter in [(f1, m_sel, df_m_casa, True), (f2, v_sel, df_v_fora, False)]:
                with col:
                    st.markdown(f"**{time} ({'Casa' if is_home_filter else 'Fora'})**")
                    for _, r in dados.head(5).iterrows():
                        gm, gv = int(r['Gols_Mandante_FT']), int(r['Gols_Visitante_FT'])
                        if gm == gv: res = "🟧"
                        elif (is_home_filter and gm > gv) or (not is_home_filter and gv > gm): res = "✅"
                        else: res = "❌"
                        st.write(f"{res} vs {r['Visitante'] if is_home_filter else r['Mandande']} ({gm}-{gv})")

        with tab_minutos:
            st.subheader("Frequência de Gols Marcados (%)")
            faixas_m = ["0-15_Mandante", "16-30_Mandante", "31-45+_Mandante", "46-60_Mandante", "61-75_Mandante", "76-90+_Mandante"]
            faixas_v = ["0-15_Visitante", "16-30_Visitante", "31-45+_Visitante", "46-60_Visitante", "61-75_Visitante", "76-90+_Visitante"]
            labels = ["0-15'", "16-30'", "31-45'", "46-60'", "61-75'", "76-90'"]

            c_m, c_v = st.columns(2)
            with c_m:
                v_m = [df_m_casa[f].mean() * 100 for f in faixas_m]
                st.dataframe(pd.DataFrame([v_m], columns=labels, index=[m_sel]).style.format("{:.1f}%").background_gradient(cmap="Greens", axis=1))
            with c_v:
                v_v = [df_v_fora[f].mean() * 100 for f in faixas_v]
                st.dataframe(pd.DataFrame([v_v], columns=labels, index=[v_sel]).style.format("{:.1f}%").background_gradient(cmap="Greens", axis=1))

        with tab_stats:
            st.subheader("Médias de Desempenho (Últimos 10)")
            s1, s2 = st.columns(2)
            s1.metric(f"Média Gols {m_sel}", f"{df_m_casa['Gols_Mandante_FT'].mean():.2f}")
            s1.metric(f"Média Cantos {m_sel}", f"{df_m_casa['Cantos_Mandante'].mean():.2f}")
            s2.metric(f"Média Gols {v_sel}", f"{df_v_fora['Gols_Visitante_FT'].mean():.2f}")
            s2.metric(f"Média Cantos {v_sel}", f"{df_v_fora['Cantos_Visitante'].mean():.2f}")

    except KeyError as e:
        st.error(f"Coluna não encontrada: {e}")
