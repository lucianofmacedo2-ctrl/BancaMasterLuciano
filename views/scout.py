import streamlit as st
import pandas as pd

def mostrar_scout(df):
    st.title("🔎 Scout de Times")

    try:
        # Filtros usando 'Liga' (corrigindo o erro de 'pais')
        c1, c2 = st.columns(2)
        liga_sel = c1.selectbox("Liga", sorted(df['Liga'].unique()))
        
        df_liga = df[df['Liga'] == liga_sel].copy()
        temp_sel = c2.selectbox("Temporada", sorted(df_liga['Temporada'].unique(), reverse=True))
        
        df_filt = df_liga[df_liga['Temporada'] == temp_sel].copy()
        df_filt['Data'] = pd.to_datetime(df_filt['Data'], dayfirst=True, errors='coerce')

        # Usando 'Mandande' conforme seu CSV
        times = sorted(df_filt['Mandande'].unique())
        m_sel = st.selectbox("Mandante (Casa)", times)
        v_sel = st.selectbox("Visitante (Fora)", [t for t in times if t != m_sel])

        df_m = df_filt[df_filt['Mandande'] == m_sel].sort_values('Data', ascending=False).head(10)
        df_v = df_filt[df_filt['Visitante'] == v_sel].sort_values('Data', ascending=False).head(10)

        st.divider()
        t1, t2, t3 = st.tabs(["📊 Forma Recente", "⏰ Minutos", "📈 Médias"])

        with t1:
            col1, col2 = st.columns(2)
            for col, time, dados, is_casa in [(col1, m_sel, df_m, True), (col2, v_sel, df_v, False)]:
                with col:
                    st.write(f"**{time}**")
                    for _, r in dados.head(5).iterrows():
                        gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
                        res = "✅" if (is_casa and gm > gv) or (not is_casa and gv > gm) else ("🟧" if gm == gv else "❌")
                        st.write(f"{res} vs {r['Visitante'] if is_casa else r['Mandande']} ({int(gm)}-{int(gv)})")

        with t2:
            st.subheader("Gols Marcados por Faixa (%)")
            faixas = ["0-15", "16-30", "31-45+", "46-60", "61-75", "76-90+"]
            c_m, c_v = st.columns(2)
            with c_m:
                v_m = [df_m[f"{f}_Mandante"].mean() * 100 for f in faixas]
                st.dataframe(pd.DataFrame([v_m], columns=faixas, index=[m_sel]).style.format("{:.1f}%").background_gradient(cmap="Greens", axis=1))
            with c_v:
                v_v = [df_v[f"{f}_Visitante"].mean() * 100 for f in faixas]
                st.dataframe(pd.DataFrame([v_v], columns=faixas, index=[v_sel]).style.format("{:.1f}%").background_gradient(cmap="Greens", axis=1))

        with t3:
            st.subheader("Médias (Últimos 10)")
            c_ma, c_va = st.columns(2)
            c_ma.metric(f"Média Cantos {m_sel}", f"{df_m['Cantos_Mandante'].mean():.2f}")
            c_va.metric(f"Média Cantos {v_sel}", f"{df_v['Cantos_Visitante'].mean():.2f}")

    except KeyError as e:
        st.error(f"Coluna ausente no CSV: {e}")
