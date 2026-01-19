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
    liga = c1.selectbox("Liga", sorted(df['liga'].unique()))
    temp = c2.selectbox("Temporada", sorted(df[df['liga'] == liga]['temporada'].unique(), reverse=True))
    
    df_filt = df[(df['liga'] == liga) & (df['temporada'] == temp)].copy()
    df_filt['data'] = pd.to_datetime(df_filt['data'], errors='coerce')

    times = sorted(df_filt['mandande'].unique())
    c3, c4 = st.columns(2)
    m_sel = c3.selectbox("Mandante (Casa)", times)
    v_sel = c4.selectbox("Visitante (Fora)", [t for t in times if t != m_sel])

    # --- 2. ANÁLISE DE FORMA E H2H (ABAS) ---
    st.divider()
    
    tab_geral, tab_especifica, tab_h2h = st.tabs([
        "📊 Últimos 10 Geral", 
        "🏠 Forma Local (Casa/Fora)", 
        "⚔️ Confronto Direto (H2H)"
    ])

    with tab_geral:
        st.subheader("Desempenho Geral (Casa & Fora)")
        f1, f2 = st.columns(2)
        df_m_geral = df_filt[(df_filt['mandande'] == m_sel) | (df_filt['visitante'] == m_sel)].sort_values('data', ascending=False).head(10)
        df_v_geral = df_filt[(df_filt['mandande'] == v_sel) | (df_filt['visitante'] == v_sel)].sort_values('data', ascending=False).head(10)
        
        for col, time, dados in [(f1, m_sel, df_m_geral), (f2, v_sel, df_v_geral)]:
            with col:
                st.markdown(f"**{time}**")
                for _, r in dados.iterrows():
                    is_home = r['mandande'] == time
                    gm, gv = r['gols_mandante_ft'], r['gols_visitante_ft']
                    if gm == gv: res = "🟧"
                    elif (is_home and gm > gv) or (not is_home and gv > gm): res = "✅"
                    else: res = "❌"
                    oponente = r['visitante'] if is_home else r['mandande']
                    st.write(f"{res} {r['data'].strftime('%d/%m')} {'🏠' if is_home else '✈️'} vs {oponente} ({int(gm)}-{int(gv)})")

    with tab_especifica:
        st.subheader("Desempenho por Mando de Campo")
        f3, f4 = st.columns(2)
        df_m_casa = df_filt[df_filt['mandande'] == m_sel].sort_values('data', ascending=False).head(10)
        df_v_fora = df_filt[df_filt['visitante'] == v_sel].sort_values('data', ascending=False).head(10)
        
        with f3:
            st.markdown(f"**{m_sel} (Somente Casa)**")
            for _, r in df_m_casa.head(5).iterrows():
                gm, gv = r['gols_mandante_ft'], r['gols_visitante_ft']
                res = "✅" if gm > gv else ("🟧" if gm == gv else "❌")
                st.write(f"{res} {r['data'].strftime('%d/%m')} vs {r['visitante']} ({int(gm)}-{int(gv)})")
        with f4:
            st.markdown(f"**{v_sel} (Somente Fora)**")
            for _, r in df_v_fora.head(5).iterrows():
                gm, gv = r['gols_visitante_ft'] > r['gols_mandante_ft']
                res = "✅" if gv else ("🟧" if r['gols_mandante_ft'] == r['gols_visitante_ft'] else "❌")
                st.write(f"{res} {r['data'].strftime('%d/%m')} vs {r['mandande']} ({int(r['gols_mandante_ft'])}-{int(r['gols_visitante_ft'])})")

    with tab_h2h:
        st.subheader(f"⚔️ {m_sel} vs {v_sel}")
        h1, h2 = st.columns(2)
        
        # H2H GERAL (Independente do mando)
        df_h2h_geral = df[( (df['mandande'] == m_sel) & (df['visitante'] == v_sel) ) | 
                          ( (df['mandande'] == v_sel) & (df['visitante'] == m_sel) )].sort_values('data', ascending=False).head(10)
        
        # H2H NESTA CASA (Mandante sendo Mandante e Visitante sendo Visitante)
        df_h2h_casa = df[(df['mandande'] == m_sel) & (df['visitante'] == v_sel)].sort_values('data', ascending=False).head(10)

        with h1:
            st.markdown("**Últimos 10 Confrontos (Geral)**")
            if not df_h2h_geral.empty:
                for _, r in df_h2h_geral.iterrows():
                    gm, gv = int(r['gols_mandante_ft']), int(r['gols_visitante_ft'])
                    st.write(f"📅 {pd.to_datetime(r['data']).strftime('%d/%m/%Y')} | {r['mandande']} {gm}-{gv} {r['visitante']}")
            else:
                st.info("Sem confrontos diretos registrados.")

        with h2:
            st.markdown(f"**Nesta Casa ({m_sel} como Mandante)**")
            if not df_h2h_casa.empty:
                for _, r in df_h2h_casa.iterrows():
                    gm, gv = int(r['gols_mandante_ft']), int(r['gols_visitante_ft'])
                    res = "✅" if gm > gv else ("🟧" if gm == gv else "❌")
                    st.write(f"{res} {pd.to_datetime(r['data']).strftime('%d/%m/%Y')} | {gm}-{gv} vs {v_sel}")
            else:
                st.info("Sem confrontos diretos nesta casa.")

    # --- 3. ESTATÍSTICAS DETALHADAS (MANTIDAS) ---
    st.divider()
    st.subheader("📊 Análise Estatística Profissional")
    
    def get_col(palavra):
        for c in df_filt.columns:
            if palavra.lower() in c.lower(): return c
        return None

    metrics_map = {
        "Gols HT": (get_col("gols_mandante_ht"), get_col("gols_visitante_ht")),
        "Gols FT": (get_col("gols_mandante_ft"), get_col("gols_visitante_ft")),
        "Cantos": (get_col("cantos_mandante"), get_col("cantos_visitante")),
        "Chutes Gol": (get_col("chutes_gol_mandante"), get_col("chutes_gol_visitante")),
        "Chutes Fora": (get_col("chutes_fora_mandante"), get_col("chutes_fora_visitante"))
    }

    def calcular_metricas(dados):
        if dados is None or dados.empty or dados.isnull().all():
            return {"Média": 0, "Mediana": 0, "Moda": 0, "Desvio P.": 0, "CV (%)": 0}
        media = dados.mean()
        desvio = dados.std()
        moda_series = dados.mode()
        moda = moda_series.iloc[0] if not moda_series.empty else 0
        return {
            "Média": media, "Mediana": dados.median(), "Moda": moda, 
            "Desvio P.": desvio, "CV (%)": (desvio / media * 100) if media > 0 else 0
        }

    def style_cv(val):
        if not isinstance(val, (int, float)): return ''
        if val < 20: return 'background-color: rgba(0, 255, 204, 0.2); color: #00ffcc;'
        if val < 40: return 'color: #ffaa00;'
        return 'color: #ff4b4b;'

    for label, (col_m, col_v) in metrics_map.items():
        if col_m and col_v:
            st.write(f"#### {label}")
            c_res1, c_res2 = st.columns(2)
            with c_res1:
                st.markdown(f"**{m_sel} (Em Casa)**")
                m_f = calcular_metricas(df_m_casa[col_m])
                m_s = calcular_metricas(df_m_casa[col_v])
                st.dataframe(pd.DataFrame([m_f, m_s], index=["Feitos", "Sofridos"]).style.format(precision=2).applymap(style_cv, subset=['CV (%)']), use_container_width=True)
            with c_res2:
                st.markdown(f"**{v_sel} (Fora)**")
                v_f = calcular_metricas(df_v_fora[col_v])
                v_s = calcular_metricas(df_v_fora[col_m])
                st.dataframe(pd.DataFrame([v_f, v_s], index=["Feitos", "Sofridos"]).style.format(precision=2).applymap(style_cv, subset=['CV (%)']), use_container_width=True)
            st.divider()
