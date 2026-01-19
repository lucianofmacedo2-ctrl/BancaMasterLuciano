import streamlit as st
import pandas as pd
import numpy as np

def mostrar_scout(df):
    st.title("🔎 Scout Estatístico Profissional")

    # Mapeamento para não dar erro de KeyError
    cols = {c.lower().strip(): c for c in df.columns}
    c_liga = cols.get('liga', 'Liga'); c_temp = cols.get('temporada', 'Temporada')
    c_mand = cols.get('mandande', 'Mandande'); c_visi = cols.get('visitante', 'Visitante')
    c_data = cols.get('data', 'Data')

    # Filtros Superiores
    c1, c2 = st.columns(2)
    liga_sel = c1.selectbox("Liga", sorted(df[c_liga].unique()))
    temp_sel = c2.selectbox("Temporada", sorted(df[df[c_liga] == liga_sel][c_temp].unique(), reverse=True))
    
    df_filt = df[(df[c_liga] == liga_sel) & (df[c_temp] == temp_sel)].copy()
    df_filt[c_data] = pd.to_datetime(df_filt[c_data], errors='coerce')

    times = sorted(df_filt[c_mand].unique())
    m_sel = st.selectbox("Mandante", times)
    v_sel = st.selectbox("Visitante", [t for t in times if t != m_sel])

    # Dados Filtrados (Últimos 10)
    df_m_casa = df_filt[df_filt[c_mand] == m_sel].sort_values(c_data, ascending=False).head(10)
    df_v_fora = df_filt[df_filt[c_visi] == v_sel].sort_values(c_data, ascending=False).head(10)

    # ABAS DE DESEMPENHO
    st.divider()
    t_geral, t_mando, t_h2h = st.tabs(["📊 Geral", "🏠 Por Mando", "⚔️ H2H"])

    with t_geral:
        f1, f2 = st.columns(2)
        df_m_g = df_filt[(df_filt[c_mand]==m_sel) | (df_filt[c_visi]==m_sel)].sort_values(c_data, ascending=False).head(10)
        df_v_g = df_filt[(df_filt[c_mand]==v_sel) | (df_filt[c_visi]==v_sel)].sort_values(c_data, ascending=False).head(10)
        for col, time, dados in [(f1, m_sel, df_m_g), (f2, v_sel, df_v_g)]:
            with col:
                st.write(f"**{time} (Últimos 10)**")
                for _, r in dados.iterrows():
                    is_h = r[c_mand] == time
                    res = "✅" if (is_h and r['Gols_Mandante_FT'] > r['Gols_Visitante_FT']) or (not is_h and r['Gols_Visitante_FT'] > r['Gols_Mandante_FT']) else ("🟧" if r['Gols_Mandante_FT'] == r['Gols_Visitante_FT'] else "❌")
                    st.write(f"{res} {r[c_data].strftime('%d/%m')} vs {r[c_visi] if is_h else r[c_mand]} ({int(r['Gols_Mandante_FT'])}-{int(r['Gols_Visitante_FT'])})")

    with t_mando:
        f3, f4 = st.columns(2)
        with f3:
            st.write(f"**{m_sel} em Casa**")
            for _, r in df_m_casa.head(5).iterrows():
                res = "✅" if r['Gols_Mandante_FT'] > r['Gols_Visitante_FT'] else ("🟧" if r['Gols_Mandante_FT'] == r['Gols_Visitante_FT'] else "❌")
                st.write(f"{res} vs {r[c_visi]} ({int(r['Gols_Mandante_FT'])}-{int(r['Gols_Visitante_FT'])})")
        with f4:
            st.write(f"**{v_sel} Fora**")
            for _, r in df_v_fora.head(5).iterrows():
                res = "✅" if r['Gols_Visitante_FT'] > r['Gols_Mandante_FT'] else ("🟧" if r['Gols_Mandante_FT'] == r['Gols_Visitante_FT'] else "❌")
                st.write(f"{res} vs {r[c_mand]} ({int(r['Gols_Mandante_FT'])}-{int(r['Gols_Visitante_FT'])})")

    with t_h2h:
        df_h = df[((df[c_mand]==m_sel)&(df[c_visi]==v_sel))|((df[c_mand]==v_sel)&(df[c_visi]==m_sel))].sort_values(c_data, ascending=False).head(10)
        if not df_h.empty:
            for _, r in df_h.iterrows(): st.write(f"📅 {pd.to_datetime(r[c_data]).strftime('%d/%m/%y')} | {r[c_mand]} {int(r['Gols_Mandante_FT'])}-{int(r['Gols_Visitante_FT'])} {r[c_visi]}")
        else: st.info("Sem H2H.")

    # TABELAS DE MINUTOS E MÉDIAS
    st.divider()
    st.subheader("⏰ Gols por Faixa (%)")
    f_m = ["0-15_Mandante", "16-30_Mandante", "31-45+_Mandante", "46-60_Mandante", "61-75_Mandante", "76-90+_Mandante"]
    f_v = ["0-15_Visitante", "16-30_Visitante", "31-45+_Visitante", "46-60_Visitante", "61-75_Visitante", "76-90+_Visitante"]
    
    c_f1, c_f2 = st.columns(2)
    for col, time, faixas, dados in [(c_f1, m_sel, f_m, df_m_casa), (c_f2, v_sel, f_v, df_v_fora)]:
        with col:
            st.write(f"**{time}**")
            vals = [dados[f].mean() * 100 for f in faixas]
            df_faixa = pd.DataFrame([vals], columns=["0-15", "16-30", "31-45", "46-60", "61-75", "76-90"], index=["%"])
            st.dataframe(df_faixa.style.format("{:.1f}%").applymap(lambda v: 'background-color: rgba(46, 204, 113, 0.3)' if v > 20 else ''), use_container_width=True)

    # MÉDIAS DETALHADAS
    st.divider()
    st.subheader("📊 Médias, Medianas e CV%")
    metrics = {"Gols": ("Gols_Mandante_FT", "Gols_Visitante_FT"), "Cantos": ("Cantos_Mandante", "Cantos_Visitante")}
    for label, (cm, cv) in metrics.items():
        st.write(f"**{label}**")
        c_m, c_v = st.columns(2)
        with c_m:
            s = df_m_casa[cm]; st.write(f"Feitos {m_sel}: Média {s.mean():.2f} | Mediana {s.median()} | CV {s.std()/s.mean()*100:.1f}%")
        with c_v:
            s = df_v_fora[cv]; st.write(f"Feitos {v_sel}: Média {s.mean():.2f} | Mediana {s.median()} | CV {s.std()/s.mean()*100:.1f}%")
