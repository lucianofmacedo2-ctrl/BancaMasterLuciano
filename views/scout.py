import streamlit as st
import pandas as pd
import numpy as np

def mostrar_scout(df):
    st.title("🔎 Scout Estatístico Avançado")
    
    # Mapeamento de colunas para evitar o erro de KeyError
    cols = {c.lower(): c for c in df.columns}
    c_liga, c_temp = cols.get('liga', 'Liga'), cols.get('temporada', 'Temporada')
    c_mand, c_visi = cols.get('mandande', 'Mandande'), cols.get('visitante', 'Visitante')
    c_data = cols.get('data', 'Data')

    # --- FILTROS ---
    c1, c2 = st.columns(2)
    liga = c1.selectbox("Liga", sorted(df[c_liga].unique()))
    temp = c2.selectbox("Temporada", sorted(df[df[c_liga] == liga][c_temp].unique(), reverse=True))
    
    df_filt = df[(df[c_liga] == liga) & (df[c_temp] == temp)].copy()
    df_filt[c_data] = pd.to_datetime(df_filt[c_data])

    times = sorted(df_filt[c_mand].unique())
    m_sel = st.selectbox("Mandante (Casa)", times)
    v_sel = st.selectbox("Visitante (Fora)", [t for t in times if t != m_sel])

    # BASES ÚLTIMOS 10
    df_m_casa = df_filt[df_filt[c_mand] == m_sel].sort_values(c_data, ascending=False).head(10)
    df_v_fora = df_filt[df_filt[c_visi] == v_sel].sort_values(c_data, ascending=False).head(10)

    # --- ABAS ---
    tab_f, tab_h = st.tabs(["📊 Forma e Tendência", "⚔️ H2H"])

    with tab_f:
        f1, f2 = st.columns(2)
        with f1:
            st.markdown(f"**{m_sel} (Casa)**")
            for _, r in df_m_casa.head(5).iterrows():
                gm, gv = int(r['Gols_Mandante_FT']), int(r['Gols_Visitante_FT'])
                res = "✅" if gm > gv else ("🟧" if gm == gv else "❌")
                st.write(f"{res} {r[c_data].strftime('%d/%m')} vs {r[c_visi]} ({gm}-{gv})")
        with f2:
            st.markdown(f"**{v_sel} (Fora)**")
            for _, r in df_v_fora.head(5).iterrows():
                gm, gv = int(r['Gols_Mandante_FT']), int(r['Gols_Visitante_FT'])
                res = "✅" if gv > gm else ("🟧" if gm == gv else "❌")
                st.write(f"{res} {r[c_data].strftime('%d/%m')} vs {r[c_mand]} ({gm}-{gv})")

    # --- TABELA DE MINUTOS COLORIDA ---
    st.divider()
    st.subheader("⏰ Gols por Minutos (%)")
    f_m = ["0-15_Mandante", "16-30_Mandante", "31-45+_Mandante", "46-60_Mandante", "61-75_Mandante", "76-90+_Mandante"]
    f_v = ["0-15_Visitante", "16-30_Visitante", "31-45+_Visitante", "46-60_Visitante", "61-75_Visitante", "76-90+_Visitante"]
    
    col_tm1, col_tm2 = st.columns(2)
    with col_tm1:
        v_m = [df_m_casa[f].mean() * 100 for f in f_m]
        st.dataframe(pd.DataFrame([v_m], columns=["0-15", "16-30", "31-45", "46-60", "61-75", "90"], index=[m_sel]).style.format("{:.1f}%").background_gradient(cmap="Greens", axis=1), use_container_width=True)
    with col_tm2:
        v_v = [df_v_fora[f].mean() * 100 for f in f_v]
        st.dataframe(pd.DataFrame([v_v], columns=["0-15", "16-30", "31-45", "46-60", "61-75", "90"], index=[v_sel]).style.format("{:.1f}%").background_gradient(cmap="Greens", axis=1), use_container_width=True)

    # --- ESTATÍSTICAS PROFISSIONAIS ---
    st.divider()
    st.subheader("📊 Médias Detalhadas")
    # Tabela com Média, Mediana e CV%
    def get_full_stats(serie):
        return {"Média": serie.mean(), "Mediana": serie.median(), "CV%": (serie.std()/serie.mean()*100) if serie.mean()>0 else 0}

    s1, s2 = st.columns(2)
    with s1:
        st.markdown(f"**{m_sel} (Gols Feitos Casa)**")
        st.table(pd.DataFrame([get_full_stats(df_m_casa['Gols_Mandante_FT'])]).style.format(precision=2))
    with s2:
        st.markdown(f"**{v_sel} (Gols Feitos Fora)**")
        st.table(pd.DataFrame([get_full_stats(df_v_fora['Gols_Visitante_FT'])]).style.format(precision=2))
