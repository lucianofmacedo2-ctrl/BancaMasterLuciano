import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
from difflib import get_close_matches

def mostrar_simulador(df):
    # CSS para Cards Premium
    st.markdown("""
        <style>
        .main-card {
            background-color: #f8f9fa;
            border-radius: 15px;
            padding: 20px;
            border-left: 5px solid #007bff;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .metric-card {
            background-color: #ffffff;
            border: 1px solid #eee;
            border-radius: 10px;
            padding: 15px;
            text-align: center;
            box-shadow: 1px 1px 5px rgba(0,0,0,0.05);
            height: 100%;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #1f1f1f;
        }
        .stat-label {
            font-size: 13px;
            color: #666;
            text-transform: uppercase;
            font-weight: 600;
        }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("## 🎲 Simulador de Confrontos Ultra Pro")
    
    # 1. Limpeza e Identificação
    df.columns = [c.strip() for c in df.columns]
    col_cn_h = 'Corners_H' if 'Corners_H' in df.columns else 'Cantos_Mandante'
    col_cn_a = 'Corners_A' if 'Corners_A' in df.columns else 'Cantos_Visitante'
    col_cn_h_ht = 'Corners_H_HT'
    col_cn_a_ht = 'Corners_A_HT'
    col_tc_h = 'Total_Cards_H'
    col_tc_a = 'Total_Cards_A'

    # --- LÓGICA DE INDEXAÇÃO ---
    lista_ligas = sorted(df['Liga'].unique())
    idx_liga = 0
    if 'liga_simulador' in st.session_state:
        matches_l = get_close_matches(st.session_state.liga_simulador, lista_ligas, n=1, cutoff=0.6)
        if matches_l: idx_liga = lista_ligas.index(matches_l[0])

    liga_sel = st.selectbox("🏆 Selecione a Liga", lista_ligas, index=idx_liga)
    df_l = df[df['Liga'] == liga_sel].copy()
    lista_times = sorted(df_l['Mandante'].unique())
    
    idx_casa = 0
    if 'time_casa_simulador' in st.session_state:
        matches_m = get_close_matches(st.session_state.time_casa_simulador, lista_times, n=1, cutoff=0.6)
        if matches_m: idx_casa = lista_times.index(matches_m[0])

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        m_sel = st.selectbox("🏠 Mandante", lista_times, index=idx_casa)
    
    visitantes_disp = sorted([t for t in lista_times if t != m_sel])
    idx_fora = 0
    if 'time_fora_simulador' in st.session_state:
        matches_v = get_close_matches(st.session_state.time_fora_simulador, visitantes_disp, n=1, cutoff=0.6)
        if matches_v: idx_fora = visitantes_disp.index(matches_v[0])

    with col_s2:
        v_sel = st.selectbox("🚌 Visitante", visitantes_disp, index=idx_fora)

    # 3. CÁLCULO DAS MÉDIAS
    def get_team_stats(df_liga, time):
        df_t = df_liga[(df_liga['Mandante'] == time) | (df_liga['Visitante'] == time)].sort_values('Data', ascending=False).head(10)
        gp = pd.to_numeric(pd.concat([df_t[df_t['Mandante'] == time]['Gols_Mandante_FT'], df_t[df_t['Visitante'] == time]['Gols_Visitante_FT']]), errors='coerce').fillna(0)
        gc = pd.to_numeric(pd.concat([df_t[df_t['Mandante'] == time]['Gols_Visitante_FT'], df_t[df_t['Visitante'] == time]['Gols_Mandante_FT']]), errors='coerce').fillna(0)
        conf = 1 - (gp.std() / (gp.mean() + 0.1)) 
        conf = max(min(conf, 1), 0)
        gp_ht = pd.to_numeric(pd.concat([df_t[df_t['Mandante'] == time]['Gols_Mandante_HT'], df_t[df_t['Visitante'] == time]['Gols_Visitante_HT']]), errors='coerce').fillna(0).mean()
        gc_ht = pd.to_numeric(pd.concat([df_t[df_t['Mandante'] == time]['Gols_Visitante_HT'], df_t[df_t['Visitante'] == time]['Gols_Mandante_HT']]), errors='coerce').fillna(0).mean()
        cp = pd.to_numeric(pd.concat([df_t[df_t['Mandante'] == time][col_cn_h], df_t[df_t['Visitante'] == time][col_cn_a]]), errors='coerce').fillna(0).mean()
        cc = pd.to_numeric(pd.concat([df_t[df_t['Mandante'] == time][col_cn_a], df_t[df_t['Visitante'] == time][col_cn_h]]), errors='coerce').fillna(0).mean()
        cp_ht = pd.to_numeric(pd.concat([df_t[df_t['Mandante'] == time].get(col_cn_h_ht, pd.Series(0)), df_t[df_t['Visitante'] == time].get(col_cn_a_ht, pd.Series(0))]), errors='coerce').fillna(0).mean()
        cc_ht = pd.to_numeric(pd.concat([df_t[df_t['Mandante'] == time].get(col_cn_a_ht, pd.Series(0)), df_t[df_t['Visitante'] == time].get(col_cn_h_ht, pd.Series(0))]), errors='coerce').fillna(0).mean()
        tcp = pd.to_numeric(pd.concat([df_t[df_t['Mandante'] == time].get(col_tc_h, pd.Series(0)), df_t[df_t['Visitante'] == time].get(col_tc_a, pd.Series(0))]), errors='coerce').fillna(0).mean()
        tcc = pd.to_numeric(pd.concat([df_t[df_t['Mandante'] == time].get(col_tc_a, pd.Series(0)), df_t[df_t['Visitante'] == time].get(col_tc_h, pd.Series(0))]), errors='coerce').fillna(0).mean()
        return gp.mean(), gc.mean(), gp_ht, gc_ht, cp, cc, cp_ht, cc_ht, tcp, tcc, conf

    s_m = get_team_stats(df_l, m_sel)
    s_v = get_team_stats(df_l, v_sel)

    # 4. PROJEÇÕES
    exp_gols_m = (s_m[0] + s_v[1]) / 2
    exp_gols_v = (s_v[0] + s_m[1]) / 2
    exp_g_ht_m = (s_m[2] + s_v[3]) / 2
    exp_g_ht_v = (s_v[2] + s_m[3]) / 2
    
    st.divider()

    # --- HEADER DE PLACAR ---
    st.markdown(f"""
        <div class='main-card'>
            <div style='display: flex; justify-content: space-around; align-items: center;'>
                <div style='text-align: center;'>
                    <h3 style='margin:0;'>{m_sel}</h3>
                    <div class='stat-value'>{exp_gols_m:.2f}</div>
                    <div class='stat-label'>Gols Projetados</div>
                </div>
                <div style='font-size: 30px; font-weight: bold; color: #ccc;'>VS</div>
                <div style='text-align: center;'>
                    <h3 style='margin:0;'>{v_sel}</h3>
                    <div class='stat-value'>{exp_gols_v:.2f}</div>
                    <div class='stat-label'>Gols Projetados</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    conf_media = (s_m[10] + s_v[10]) / 2
    st.write(f"📊 **Índice de Previsibilidade:** {conf_media*100:.1f}%")
    st.progress(conf_media)

    def card_prob(titulo, valor):
        cor = "#28a745" if valor > 60 else "#fd7e14" if valor > 40 else "#dc3545"
        return f"""<div class='metric-card'><div class='stat-label'>{titulo}</div><div class='stat-value' style='color: {cor};'>{valor:.1f}%</div></div>"""

    # --- SEÇÃO GOLS ---
    st.markdown("### ⚽ Análise de Gols (Poisson)")
    total_ft = exp_gols_m + exp_gols_v
    p_btts = ((1 - poisson.pmf(0, exp_gols_m)) * (1 - poisson.pmf(0, exp_gols_v))) * 100
    
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(card_prob("Over 1.5 FT", (1 - poisson.cdf(1, total_ft)) * 100), unsafe_allow_html=True)
    c2.markdown(card_prob("Over 2.5 FT", (1 - poisson.cdf(2, total_ft)) * 100), unsafe_allow_html=True)
    c3.markdown(card_prob("Ambas Marcam", p_btts), unsafe_allow_html=True)
    c4.markdown(card_prob("Over 0.5 HT", (1 - poisson.cdf(0, (exp_g_ht_m + exp_g_ht_v))) * 100), unsafe_allow_html=True)

    # --- SEÇÃO CANTOS ---
    st.markdown("### 🚩 Análise de Cantos")
    total_cn_ht = (s_m[6] + s_v[7] + s_v[6] + s_m[7]) / 2
    total_cn_ft = (s_m[4] + s_v[5] + s_v[4] + s_m[5]) / 2
    
    cc1, cc2, cc3 = st.columns(3)
    cc1.markdown(card_prob("Over 4.5 HT", (1 - poisson.cdf(4, total_cn_ht)) * 100), unsafe_allow_html=True)
    cc2.markdown(card_prob("Over 8.5 FT", (1 - poisson.cdf(8, total_cn_ft)) * 100), unsafe_allow_html=True)
    cc3.markdown(card_prob("Over 9.5 FT", (1 - poisson.cdf(9, total_cn_ft)) * 100), unsafe_allow_html=True)

    # --- SEÇÃO CARTÕES ---
    st.markdown("### 🟨 Análise de Cartões")
    # Exp_cards_time = (O que o time recebe + O que o adversário causa) / 2
    exp_c_m = (s_m[8] + s_v[9]) / 2
    exp_c_v = (s_v[8] + s_m[9]) / 2
    total_cr_ft = exp_c_m + exp_c_v
    p_btts_c = ((1 - poisson.pmf(0, exp_c_m)) * (1 - poisson.pmf(0, exp_c_v))) * 100
    
    cr1, cr2, cr3 = st.columns(3)
    cr1.markdown(card_prob("Over 2.5 Cartões", (1 - poisson.cdf(2, total_cr_ft)) * 100), unsafe_allow_html=True)
    cr2.markdown(card_prob("Over 3.5 Cartões", (1 - poisson.cdf(3, total_cr_ft)) * 100), unsafe_allow_html=True)
    cr3.markdown(card_prob("Ambas Recebem", p_btts_c), unsafe_allow_html=True)

    # --- TOP PLACARES ---
    st.markdown("### 🏆 Top 3 Placares Exatos")
    prob_matrix = np.outer(poisson.pmf(np.arange(5), exp_gols_m), poisson.pmf(np.arange(5), exp_gols_v))
    placares = []
    for i in range(5):
        for j in range(5):
            placares.append((f"{i} x {j}", prob_matrix[i, j] * 100))
    placares = sorted(placares, key=lambda x: x[1], reverse=True)[:3]
    
    cols_pl = st.columns(3)
    for i, (placar, prob) in enumerate(placares):
        cols_pl[i].markdown(f"""<div style='background:#1f1f1f; color:white; border-radius:10px; padding:10px; text-align:center;'><small>Rank {i+1}</small><br><b style='font-size:20px;'>{placar}</b><br><span style='color:#00ff00;'>{prob:.1f}%</span></div>""", unsafe_allow_html=True)

    st.divider()
    st.info(f"💡 **Resumo Final:** Projeção de {total_ft:.2f} gols, {total_cn_ft:.1f} cantos e {total_cr_ft:.1f} cartões totais.")
