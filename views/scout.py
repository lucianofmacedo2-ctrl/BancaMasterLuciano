import streamlit as st
import pandas as pd

def mostrar_scout(df):
    st.title("🔎 Scout Estatístico Profissional")

    try:
        # Filtros principais
        c1, c2 = st.columns(2)
        liga_sel = c1.selectbox("Selecione a Liga", sorted(df['Liga'].unique()))
        
        df_liga = df[df['Liga'] == liga_sel].copy()
        temp_sel = c2.selectbox("Temporada", sorted(df_liga['Temporada'].unique(), reverse=True))
        
        df_filt = df_liga[df_liga['Temporada'] == temp_sel].copy()
        df_filt['Data'] = pd.to_datetime(df_filt['Data'], dayfirst=True, errors='coerce')

        # Seleção de Times (Usando 'Mandande' com 'e' no final conforme seu CSV)
        times = sorted(df_filt['Mandande'].unique())
        c3, c4 = st.columns(2)
        m_sel = c3.selectbox("Mandante (Casa)", times)
        v_sel = c4.selectbox("Visitante (Fora)", [t for t in times if t != m_sel])

        # Bases de Dados - Últimos 10
        df_m = df_filt[df_filt['Mandande'] == m_sel].sort_values('Data', ascending=False).head(10)
        df_v = df_filt[df_filt['Visitante'] == v_sel].sort_values('Data', ascending=False).head(10)

        st.divider()
        tab1, tab2, tab3 = st.tabs(["📊 Forma Recente", "⏰ Gols por Minuto", "⚔️ H2H"])

        with tab1:
            col1, col2 = st.columns(2)
            for col, time, dados, is_casa in [(col1, m_sel, df_m, True), (col2, v_sel, df_v, False)]:
                with col:
                    st.markdown(f"**{time} ({'Casa' if is_casa else 'Fora'})**")
                    for _, r in dados.head(5).iterrows():
                        gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
                        if gm == gv: res = "🟧"
                        elif (is_casa and gm > gv) or (not is_casa and gv > gm): res = "✅"
                        else: res = "❌"
                        st.write(f"{res} vs {r['Visitante'] if is_casa else r['Mandande']} ({int(gm)}-{int(gv)})")

        with tab2:
            st.subheader("Análise de Minutos (Gols Marcados %)")
            faixas = ["0-15", "16-30", "31-45+", "46-60", "61-75", "76-90+"]
            c_fm, c_fv = st.columns(2)
            with c_fm:
                v_m = [df_m[f"{f}_Mandante"].mean() * 100 for f in faixas]
                st.dataframe(pd.DataFrame([v_m], columns=faixas, index=[m_sel]).style.format("{:.1f}%").background_gradient(cmap="Greens", axis=1))
            with c_fv:
                v_v = [df_v[f"{f}_Visitante"].mean() * 100 for f in faixas]
                st.dataframe(pd.DataFrame([v_v], columns=faixas, index=[v_sel]).style.format("{:.1f}%").background_gradient(cmap="Greens", axis=1))

        with tab3:
            h2h = df[((df['Mandande'] == m_sel) & (df['Visitante'] == v_sel)) | 
                     ((df['Mandande'] == v_sel) & (df['Visitante'] == m_sel))].sort_values('Data', ascending=False).head(5)
            if not h2h.empty:
                for _, r in h2h.iterrows():
                    st.write(f"📅 {pd.to_datetime(r['Data']).strftime('%d/%m/%Y')} | {r['Mandande']} {int(r['Gols_Mandante_FT'])}-{int(r['Gols_Visitante_FT'])} {r['Visitante']}")
            else:
                st.info("Sem confrontos diretos recentes.")

    except KeyError as e:
        st.error(f"Erro de coluna no CSV: {e}")
        st.info("O sistema tentou buscar uma coluna que não existe. Verifique se o arquivo CSV está correto.")
