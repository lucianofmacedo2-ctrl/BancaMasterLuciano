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
        
        # Ajustado de 'pais' para 'Liga' conforme seu CSV
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
        tab_geral, tab_especifica, tab_h2h = st.tabs(["📊 Últimos 10 Geral", "🏠 Forma Casa/Fora", "⚔️ H2H"])

        with tab_geral:
            f1, f2 = st.columns(2)
            df_m_geral = df_filt[(df_filt['Mandande'] == m_sel) | (df_filt['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(10)
            df_v_geral = df_filt[(df_filt['Mandande'] == v_sel) | (df_filt['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(10)
            
            for col, time, dados in [(f1, m_sel, df_m_geral), (f2, v_sel, df_v_geral)]:
                with col:
                    st.markdown(f"**{time}**")
                    for _, r in dados.iterrows():
                        is_home = r['Mandande'] == time
                        gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
                        if gm == gv: res = "🟧"
                        elif (is_home and gm > gv) or (not is_home and gv > gm): res = "✅"
                        else: res = "❌"
                        st.write(f"{res} {r['Data'].strftime('%d/%m')} vs {r['Visitante'] if is_home else r['Mandande']} ({int(gm)}-{int(gv)})")

        with tab_h2h:
            df_h2h = df[((df['Mandande'] == m_sel) & (df['Visitante'] == v_sel)) | 
                        ((df['Mandande'] == v_sel) & (df['Visitante'] == m_sel))].sort_values('Data', ascending=False).head(5)
            if not df_h2h.empty:
                for _, r in df_h2h.iterrows():
                    st.write(f"📅 {pd.to_datetime(r['Data']).strftime('%d/%m/%y')} | {r['Mandande']} {int(r['Gols_Mandante_FT'])}-{int(r['Gols_Visitante_FT'])} {r['Visitante']}")
            else:
                st.info("Sem H2H registrado.")

        # --- 3. TABELA DE MINUTOS (Nomes exatos das suas colunas) ---
        st.divider()
        st.subheader("⏰ Gols por Faixa de Minutos (%)")
        
        faixas_m = ["0-15_Mandante", "16-30_Mandante", "31-45+_Mandante", "46-60_Mandante", "61-75_Mandante", "76-90+_Mandante"]
        faixas_v = ["0-15_Visitante", "16-30_Visitante", "31-45+_Visitante", "46-60_Visitante", "61-75_Visitante", "76-90+_Visitante"]
        labels = ["0-15'", "16-30'", "31-45'", "46-60'", "61-75'", "76-90'"]

        c_fm, c_fv = st.columns(2)
        with c_fm:
            val_m = [df_m_casa[f].mean() * 100 for f in faixas_m]
            st.dataframe(pd.DataFrame([val_m], columns=labels, index=[m_sel]).style.format("{:.1f}%").background_gradient(cmap="Greens", axis=1), use_container_width=True)
        
        with c_fv:
            val_v = [df_v_fora[f].mean() * 100 for f in faixas_v]
            st.dataframe(pd.DataFrame([val_v], columns=labels, index=[v_sel]).style.format("{:.1f}%").background_gradient(cmap="Greens", axis=1), use_container_width=True)

        # --- 4. MÉDIAS E MEDIANAS ---
        st.divider()
        st.subheader("📊 Estatísticas Detalhadas")
        m1, m2 = st.columns(2)
        with m1:
            st.write(f"**{m_sel} (Gols FT)**")
            st.write(f"Média: {df_m_casa['Gols_Mandante_FT'].mean():.2f} | Mediana: {df_m_casa['Gols_Mandante_FT'].median()}")
            st.write(f"**{m_sel} (Cantos)**")
            st.write(f"Média: {df_m_casa['Cantos_Mandante'].mean():.2f}")
        with m2:
            st.write(f"**{v_sel} (Gols FT)**")
            st.write(f"Média: {df_v_fora['Gols_Visitante_FT'].mean():.2f} | Mediana: {df_v_fora['Gols_Visitante_FT'].median()}")
            st.write(f"**{v_sel} (Cantos)**")
            st.write(f"Média: {df_v_fora['Cantos_Visitante'].mean():.2f}")

    except KeyError as e:
        st.error(f"Erro de coluna: {e}")
        st.info("Verifique se os nomes das colunas no CSV estão exatamente como o esperado.")
