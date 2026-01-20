import streamlit as st
import pandas as pd
import numpy as np

def mostrar_scout(df):
    st.title("🔎 Scout Estatístico Avançado")
    
    if df.empty:
        st.error("Dados não encontrados. Verifique o arquivo CSV.")
        return

    # --- 1. FILTROS ---
    c1, c2 = st.columns(2)
    
    # Nomes exatos do seu CSV
    liga = c1.selectbox("Liga", sorted(df['Liga'].unique()))
    temp = c2.selectbox("Temporada", sorted(df[df['Liga'] == liga]['Temporada'].unique(), reverse=True))
    
    df_filt = df[(df['Liga'] == liga) & (df['Temporada'] == temp)].copy()
    df_filt['Data'] = pd.to_datetime(df_filt['Data'], errors='coerce')

    times = sorted(df_filt['Mandande'].unique())
    c3, c4 = st.columns(2)
    m_sel = c3.selectbox("Mandante (Casa)", times)
    v_sel = c4.selectbox("Visitante (Fora)", [t for t in times if t != m_sel])

    # --- BASES DE DADOS (Últimos 10 jogos) ---
    df_m_casa = df_filt[df_filt['Mandande'] == m_sel].sort_values('Data', ascending=False).head(10)
    df_v_fora = df_filt[df_filt['Visitante'] == v_sel].sort_values('Data', ascending=False).head(10)

    # --- 2. ABAS DE FORMA E H2H ---
    st.divider()
    tab_geral, tab_especifica, tab_h2h = st.tabs(["📊 Últimos 10 Geral", "🏠 Forma Local", "⚔️ H2H"])

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
                    oponente = r['Visitante'] if is_home else r['Mandande']
                    st.write(f"{res} {r['Data'].strftime('%d/%m')} {'🏠' if is_home else '✈️'} vs {oponente} ({int(gm)}-{int(gv)})")

    with tab_especifica:
        f3, f4 = st.columns(2)
        with f3:
            st.markdown(f"**{m_sel} (Somente Casa)**")
            for _, r in df_m_casa.head(5).iterrows():
                gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
                res = "✅" if gm > gv else ("🟧" if gm == gv else "❌")
                st.write(f"{res} {r['Data'].strftime('%d/%m')} vs {r['Visitante']} ({int(gm)}-{int(gv)})")
        with f4:
            st.markdown(f"**{v_sel} (Somente Fora)**")
            for _, r in df_v_fora.head(5).iterrows():
                gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
                res = "✅" if gv > gm else ("🟧" if gm == gv else "❌")
                st.write(f"{res} {r['Data'].strftime('%d/%m')} vs {r['Mandande']} ({int(gm)}-{int(gv)})")

    with tab_h2h:
        df_h2h = df[((df['Mandande'] == m_sel) & (df['Visitante'] == v_sel)) | 
                    ((df['Mandande'] == v_sel) & (df['Visitante'] == m_sel))].sort_values('Data', ascending=False).head(10)
        if not df_h2h.empty:
            for _, r in df_h2h.iterrows():
                st.write(f"📅 {pd.to_datetime(r['Data']).strftime('%d/%m/%y')} | {r['Mandande']} {int(r['Gols_Mandante_FT'])}-{int(r['Gols_Visitante_FT'])} {r['Visitante']}")
        else: st.info("Sem H2H registrado.")

    # --- 3. INCIDÊNCIA DE GOLS (%) ---
    st.divider()
    st.subheader("🎯 Incidência de Gols (%)")
    def calc_perc(serie, corte):
        return (serie > corte).sum() / len(serie) * 100 if len(serie) > 0 else 0

    c_inc1, c_inc2 = st.columns(2)
    for col, time, dados in [(c_inc1, m_sel, df_m_casa), (c_inc2, v_sel, df_v_fora)]:
        with col:
            st.markdown(f"**{time}**")
            data_inc = {
                "0.5": [calc_perc(dados['Total_Gols_HT'], 0.5), calc_perc(dados['Total_Gols_FT'], 0.5)],
                "1.5": [calc_perc(dados['Total_Gols_HT'], 1.5), calc_perc(dados['Total_Gols_FT'], 1.5)],
                "2.5": [calc_perc(dados['Total_Gols_HT'], 2.5), calc_perc(dados['Total_Gols_FT'], 2.5)],
                "3.5": [calc_perc(dados['Total_Gols_HT'], 3.5), calc_perc(dados['Total_Gols_FT'], 3.5)]
            }
            st.table(pd.DataFrame(data_inc, index=["Over HT %", "Over FT %"]).style.format("{:.1f}%"))

    # --- 4. GOLS POR FAIXA DE MINUTOS (%) ---
    st.divider()
    st.subheader("⏰ Gols por Faixa de Minutos (%)")
    
    faixas_m = ["0-15_Mandante", "16-30_Mandante", "31-45+_Mandante", "46-60_Mandante", "61-75_Mandante", "76-90+_Mandante"]
    faixas_v = ["0-15_Visitante", "16-30_Visitante", "31-45+_Visitante", "46-60_Visitante", "61-75_Visitante", "76-90+_Visitante"]
    labels = ["0-15'", "16-30'", "31-45'", "46-60'", "61-75'", "76-90'"]

    c_f1, c_f2 = st.columns(2)
    with c_f1:
        st.markdown(f"**{m_sel} (Marcados em Casa)**")
        vals_m = [df_m_casa[f].mean() * 100 for f in faixas_m]
        df_faixa_m = pd.DataFrame([vals_m], columns=labels, index=["% Gols"])
        st.dataframe(df_faixa_m.style.format("{:.1f}%").background_gradient(cmap="Greens", axis=1), use_container_width=True)
    
    with c_f2:
        st.markdown(f"**{v_sel} (Marcados Fora)**")
        vals_v = [df_v_fora[f].mean() * 100 for f in faixas_v]
        df_faixa_v = pd.DataFrame([vals_v], columns=labels, index=["% Gols"])
        st.dataframe(df_faixa_v.style.format("{:.1f}%").background_gradient(cmap="Greens", axis=1), use_container_width=True)

    # --- 5. ESTATÍSTICAS DETALHADAS (PROFISSIONAL) ---
    st.divider()
    st.subheader("📊 Análise Estatística Profissional")

    metrics = {
        "Gols FT": ("Gols_Mandante_FT", "Gols_Visitante_FT"),
        "Gols HT": ("Gols_Mandante_HT", "Gols_Visitante_HT"),
        "Cantos": ("Cantos_Mandante", "Cantos_Visitante"),
        "Chutes Gol": ("Chutes_Gol_Mandante", "Chutes_Gol_Visitante"),
        "Chutes Fora": ("Chutes_Fora_Mandante", "Chutes_Fora_Visitante")
    }

    def get_stats(dados, col_f, col_s):
        f, s = dados[col_f], dados[col_s]
        res = {}
        for nome, serie in [("Feitos", f), ("Sofridos", s)]:
            cv = (serie.std() / serie.mean() * 100) if serie.mean() > 0 else 0
            res[nome] = {"Média": serie.mean(), "Mediana": serie.median(), "CV (%)": cv}
        return pd.DataFrame(res).T

    for label, (cm, cv) in metrics.items():
        st.write(f"#### {label}")
        c_m, c_v = st.columns(2)
        with c_m:
            st.markdown(f"**{m_sel}**")
            st.dataframe(get_stats(df_m_casa, cm, cv).style.format(precision=2), use_container_width=True)
        with c_v:
            st.markdown(f"**{v_sel}**")
            st.dataframe(get_stats(df_v_fora, cv, cm).style.format(precision=2), use_container_width=True)
