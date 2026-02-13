import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
from difflib import get_close_matches

def mostrar_simulador(df):
    st.markdown("## 🎲 Simulador de Confrontos")
    st.write("Projeção de placar, cantos e cartões baseada em médias de ataque e defesa.")

    # 1. Limpeza
    df.columns = [c.strip() for c in df.columns]
    
    # Identificação dinâmica das colunas
    col_cn_h = 'Corners_H' if 'Corners_H' in df.columns else 'Cantos_Mandante'
    col_cn_a = 'Corners_A' if 'Corners_A' in df.columns else 'Cantos_Visitante'
    
    # Colunas HT
    col_cn_h_ht = 'Corners_H_HT'
    col_cn_a_ht = 'Corners_A_HT'
    
    # Colunas de Cartões
    col_tc_h = 'Total_Cards_H'
    col_tc_a = 'Total_Cards_A'

    # --- LÓGICA DE INDEXAÇÃO AUTOMÁTICA (ADICIONADO) ---
    lista_ligas = sorted(df['Liga'].unique())
    idx_liga = 0
    if 'liga_simulador' in st.session_state:
        matches_l = get_close_matches(st.session_state.liga_simulador, lista_ligas, n=1, cutoff=0.6)
        if matches_l:
            idx_liga = lista_ligas.index(matches_l[0])

    # 2. SELEÇÃO DE TIMES
    liga_sel = st.selectbox("🏆 Selecione a Liga", lista_ligas, index=idx_liga)
    df_l = df[df['Liga'] == liga_sel].copy()

    lista_times = sorted(df_l['Mandante'].unique())
    
    idx_casa = 0
    if 'time_casa_simulador' in st.session_state:
        matches_m = get_close_matches(st.session_state.time_casa_simulador, lista_times, n=1, cutoff=0.6)
        if matches_m:
            idx_casa = lista_times.index(matches_m[0])

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        m_sel = st.selectbox("🏠 Mandante", lista_times, index=idx_casa)
    
    visitantes_disp = sorted([t for t in lista_times if t != m_sel])
    idx_fora = 0
    if 'time_fora_simulador' in st.session_state:
        matches_v = get_close_matches(st.session_state.time_fora_simulador, visitantes_disp, n=1, cutoff=0.6)
        if matches_v:
            idx_fora = visitantes_disp.index(matches_v[0])

    with col_s2:
        v_sel = st.selectbox("🚌 Visitante", visitantes_disp, index=idx_fora)

    # 3. CÁLCULO DAS MÉDIAS (Últimos 10 jogos)
    def get_team_stats(df_liga, time):
        df_t = df_liga[(df_liga['Mandante'] == time) | (df_liga['Visitante'] == time)].sort_values('Data', ascending=False).head(10)
        
        # Gols FT
        gp = pd.concat([df_t[df_t['Mandante'] == time]['Gols_Mandante_FT'], df_t[df_t['Visitante'] == time]['Gols_Visitante_FT']]).mean()
        gc = pd.concat([df_t[df_t['Mandante'] == time]['Gols_Visitante_FT'], df_t[df_t['Visitante'] == time]['Gols_Mandante_FT']]).mean()
        
        # Gols HT
        gp_ht = pd.concat([df_t[df_t['Mandante'] == time]['Gols_Mandante_HT'], df_t[df_t['Visitante'] == time]['Gols_Visitante_HT']]).mean()
        gc_ht = pd.concat([df_t[df_t['Mandante'] == time]['Gols_Visitante_HT'], df_t[df_t['Visitante'] == time]['Gols_Mandante_HT']]).mean()
        
        # Cantos FT
        cp = pd.concat([df_t[df_t['Mandante'] == time][col_cn_h], df_t[df_t['Visitante'] == time][col_cn_a]]).mean()
        cc = pd.concat([df_t[df_t['Mandante'] == time][col_cn_a], df_t[df_t['Visitante'] == time][col_cn_h]]).mean()

        # Cantos HT
        cp_ht = pd.concat([df_t[df_t['Mandante'] == time].get(col_cn_h_ht, pd.Series(0)), df_t[df_t['Visitante'] == time].get(col_cn_a_ht, pd.Series(0))]).mean()
        cc_ht = pd.concat([df_t[df_t['Mandante'] == time].get(col_cn_a_ht, pd.Series(0)), df_t[df_t['Visitante'] == time].get(col_cn_h_ht, pd.Series(0))]).mean()
        
        # Cartões
        tcp = pd.concat([df_t[df_t['Mandante'] == time].get(col_tc_h, pd.Series(0)), df_t[df_t['Visitante'] == time].get(col_tc_a, pd.Series(0))]).mean()
        tcc = pd.concat([df_t[df_t['Mandante'] == time].get(col_tc_a, pd.Series(0)), df_t[df_t['Visitante'] == time].get(col_tc_h, pd.Series(0))]).mean()
        
        return gp, gc, gp_ht, gc_ht, cp, cc, cp_ht, cc_ht, tcp, tcc

    gp_m, gc_m, gph_m, gch_m, cp_m, cc_m, cph_m, cch_m, tcp_m, tcc_m = get_team_stats(df_l, m_sel)
    gp_v, gc_v, gph_v, gch_v, cp_v, cc_v, cph_v, cch_v, tcp_v, tcc_v = get_team_stats(df_l, v_sel)

    # 4. PROJEÇÕES (Ataque de um contra Defesa do outro)
    exp_gols_m = (gp_m + gc_v) / 2
    exp_gols_v = (gp_v + gc_m) / 2
    exp_gols_h_m = (gph_m + gch_v) / 2
    exp_gols_h_v = (gph_v + gch_m) / 2
    exp_cantos_m = (cp_m + cc_v) / 2
    exp_cantos_v = (cp_v + cc_m) / 2
    exp_cantos_h_m = (cph_m + cch_v) / 2
    exp_cantos_h_v = (cph_v + cch_m) / 2
    exp_cards_m = (tcp_m + tcc_v) / 2
    exp_cards_v = (tcp_v + tcc_m) / 2

    st.divider()

    # --- EXIBIÇÃO DO PLACAR PROJETADO ---
    c_res1, c_res2, c_res3 = st.columns([2, 1, 2])
    with c_res1:
        st.subheader(m_sel)
        st.title(f"{exp_gols_m:.2f}")
        st.caption(f"HT: {exp_gols_h_m:.2f} | C.HT: {exp_cantos_h_m:.1f} | Cards: {exp_cards_m:.1f}")
    with c_res2:
        st.title("VS")
    with c_res3:
        st.subheader(v_sel)
        st.title(f"{exp_gols_v:.2f}")
        st.caption(f"HT: {exp_gols_h_v:.2f} | C.HT: {exp_cantos_h_v:.1f} | Cards: {exp_cards_v:.1f}")

    st.divider()

    def format_prob(val):
        color = "green" if val > 60 else "orange" if val > 40 else "red"
        return f"<h2 style='color:{color}; text-align:center;'>{val:.1f}%</h2>"

    # --- PROBABILIDADES: GOLS HT ---
    st.markdown("### 📈 Probabilidades Estimadas: Gols HT")
    total_exp_gols_ht = exp_gols_h_m + exp_gols_h_v
    p_over05_ht = (1 - poisson.cdf(0, total_exp_gols_ht)) * 100
    p_over15_ht = (1 - poisson.cdf(1, total_exp_gols_ht)) * 100
    p_btts_ht = ( (1 - poisson.pmf(0, exp_gols_h_m)) * (1 - poisson.pmf(0, exp_gols_h_v)) ) * 100

    col_ht1, col_ht2, col_ht3 = st.columns(3)
    with col_ht1:
        st.markdown("<p style='text-align:center;'>Over 0.5 HT</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_over05_ht), unsafe_allow_html=True)
    with col_ht2:
        st.markdown("<p style='text-align:center;'>Over 1.5 HT</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_over15_ht), unsafe_allow_html=True)
    with col_ht3:
        st.markdown("<p style='text-align:center;'>Ambas Marcam HT</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_btts_ht), unsafe_allow_html=True)

    # --- PROBABILIDADES: GOLS FT ---
    st.markdown("### 📈 Probabilidades Estimadas: Gols FT")
    total_exp_gols = exp_gols_m + exp_gols_v
    p_over15 = (1 - poisson.cdf(1, total_exp_gols)) * 100
    p_over25 = (1 - poisson.cdf(2, total_exp_gols)) * 100
    p_btts = ( (1 - poisson.pmf(0, exp_gols_m)) * (1 - poisson.pmf(0, exp_gols_v)) ) * 100

    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.markdown("<p style='text-align:center;'>Over 1.5 FT</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_over15), unsafe_allow_html=True)
    with col_p2:
        st.markdown("<p style='text-align:center;'>Over 2.5 FT</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_over25), unsafe_allow_html=True)
    with col_p3:
        st.markdown("<p style='text-align:center;'>Ambas Marcam FT</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_btts), unsafe_allow_html=True)

    # --- PROBABILIDADES: CANTOS HT ---
    st.markdown("### 📈 Probabilidades Estimadas: Cantos HT")
    total_exp_cantos_ht = exp_cantos_h_m + exp_cantos_h_v
    p_cn35_ht = (1 - poisson.cdf(3, total_exp_cantos_ht)) * 100
    p_cn45_ht = (1 - poisson.cdf(4, total_exp_cantos_ht)) * 100
    p_cn55_ht = (1 - poisson.cdf(5, total_exp_cantos_ht)) * 100

    col_cht1, col_cht2, col_cht3 = st.columns(3)
    with col_cht1:
        st.markdown("<p style='text-align:center;'>Over 3.5 Cantos HT</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_cn35_ht), unsafe_allow_html=True)
    with col_cht2:
        st.markdown("<p style='text-align:center;'>Over 4.5 Cantos HT</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_cn45_ht), unsafe_allow_html=True)
    with col_cht3:
        st.markdown("<p style='text-align:center;'>Over 5.5 Cantos HT</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_cn55_ht), unsafe_allow_html=True)

    # --- PROBABILIDADES: CANTOS FT ---
    st.markdown("### 📈 Probabilidades Estimadas: Cantos FT")
    total_exp_cantos = exp_cantos_m + exp_cantos_v
    p_cn85 = (1 - poisson.cdf(8, total_exp_cantos)) * 100
    p_cn95 = (1 - poisson.cdf(9, total_exp_cantos)) * 100
    p_cn105 = (1 - poisson.cdf(10, total_exp_cantos)) * 100

    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        st.markdown("<p style='text-align:center;'>Over 8.5 Cantos FT</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_cn85), unsafe_allow_html=True)
    with col_c2:
        st.markdown("<p style='text-align:center;'>Over 9.5 Cantos FT</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_cn95), unsafe_allow_html=True)
    with col_c3:
        st.markdown("<p style='text-align:center;'>Over 10.5 Cantos FT</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_cn105), unsafe_allow_html=True)

    # --- PROBABILIDADES: CARTÕES ---
    st.markdown("### 📈 Probabilidades Estimadas: Cartões FT")
    total_exp_cards = exp_cards_m + exp_cards_v
    p_car15 = (1 - poisson.cdf(1, total_exp_cards)) * 100
    p_car25 = (1 - poisson.cdf(2, total_exp_cards)) * 100
    p_car35 = (1 - poisson.cdf(3, total_exp_cards)) * 100

    col_car1, col_car2, col_car3 = st.columns(3)
    with col_car1:
        st.markdown("<p style='text-align:center;'>Over 1.5 Cartões FT</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_car15), unsafe_allow_html=True)
    with col_car2:
        st.markdown("<p style='text-align:center;'>Over 2.5 Cartões FT</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_car25), unsafe_allow_html=True)
    with col_car3:
        st.markdown("<p style='text-align:center;'>Over 3.5 Cartões FT</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_car35), unsafe_allow_html=True)

    st.info(f"💡 **Resumo da Projeção:** Total Gols FT: {total_exp_gols:.2f} | Total Cantos FT: {total_exp_cantos:.1f} | Total Cartões: {total_exp_cards:.1f}")
