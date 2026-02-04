import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson

def mostrar_simulador(df):
    st.markdown("## 🎲 Simulador de Confrontos")
    st.write("Projeção de placar, cantos e probabilidades baseada em médias de ataque e defesa.")

    # 1. Limpeza
    df.columns = [c.strip() for c in df.columns]
    
    # Identificação dinâmica das colunas de cantos (evita erro de nome de coluna)
    col_cn_h = 'Corners_H' if 'Corners_H' in df.columns else 'Cantos_Mandante'
    col_cn_a = 'Corners_A' if 'Corners_A' in df.columns else 'Cantos_Visitante'

    # 2. SELEÇÃO DE TIMES
    lista_ligas = sorted(df['Liga'].unique())
    liga_sel = st.selectbox("🏆 Selecione a Liga", lista_ligas)
    df_l = df[df['Liga'] == liga_sel].copy()

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        m_sel = st.selectbox("🏠 Mandante", sorted(df_l['Mandante'].unique()))
    with col_s2:
        v_sel = st.selectbox("🚌 Visitante", sorted([t for t in df_l['Mandante'].unique() if t != m_sel]))

    # 3. CÁLCULO DAS MÉDIAS (Últimos 10 jogos)
    def get_team_stats(df_liga, time):
        df_t = df_liga[(df_liga['Mandante'] == time) | (df_liga['Visitante'] == time)].sort_values('Data', ascending=False).head(10)
        
        # Gols
        gp = pd.concat([df_t[df_t['Mandante'] == time]['Gols_Mandante_FT'], df_t[df_t['Visitante'] == time]['Gols_Visitante_FT']]).mean()
        gc = pd.concat([df_t[df_t['Mandante'] == time]['Gols_Visitante_FT'], df_t[df_t['Visitante'] == time]['Gols_Mandante_FT']]).mean()
        
        # Cantos (Mapeamento de quem faz e quem sofre)
        cp = pd.concat([df_t[df_t['Mandante'] == time][col_cn_h], df_t[df_t['Visitante'] == time][col_cn_a]]).mean()
        cc = pd.concat([df_t[df_t['Mandante'] == time][col_cn_a], df_t[df_t['Visitante'] == time][col_cn_h]]).mean()
        
        return gp, gc, cp, cc

    gp_m, gc_m, cp_m, cc_m = get_team_stats(df_l, m_sel)
    gp_v, gc_v, cp_v, cc_v = get_team_stats(df_l, v_sel)

    # 4. PROJEÇÕES (Fórmula: (Pró Time A + Contra Time B) / 2)
    exp_gols_m = (gp_m + gc_v) / 2
    exp_gols_v = (gp_v + gc_m) / 2
    
    exp_cantos_m = (cp_m + cc_v) / 2
    exp_cantos_v = (cp_v + cc_m) / 2
    total_exp_cantos = exp_cantos_m + exp_cantos_v

    st.divider()

    # --- EXIBIÇÃO DO PLACAR PROJETADO ---
    c_res1, c_res2, c_res3 = st.columns([2, 1, 2])
    with c_res1:
        st.subheader(m_sel)
        st.title(f"{exp_gols_m:.2f}")
        st.caption(f"Gols Estimados | Cantos: {exp_cantos_m:.1f}")
    with c_res2:
        st.title("VS")
    with c_res3:
        st.subheader(v_sel)
        st.title(f"{exp_gols_v:.2f}")
        st.caption(f"Gols Estimados | Cantos: {exp_cantos_v:.1f}")

    st.divider()

    # --- PROBABILIDADES DE MERCADO (GOLS) ---
    st.markdown("### 📈 Probabilidades Estimadas: Gols")
    total_exp_gols = exp_gols_m + exp_gols_v
    
    col_p1, col_p2, col_p3 = st.columns(3)
    
    def format_prob(val):
        color = "green" if val > 60 else "orange" if val > 40 else "red"
        return f"<h2 style='color:{color}; text-align:center;'>{val:.1f}%</h2>"

    p_over15 = (1 - poisson.cdf(1, total_exp_gols)) * 100
    p_over25 = (1 - poisson.cdf(2, total_exp_gols)) * 100
    p_btts = ( (1 - poisson.pmf(0, exp_gols_m)) * (1 - poisson.pmf(0, exp_gols_v)) ) * 100

    with col_p1:
        st.markdown("<p style='text-align:center;'>Over 1.5 FT</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_over15), unsafe_allow_html=True)
    with col_p2:
        st.markdown("<p style='text-align:center;'>Over 2.5 FT</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_over25), unsafe_allow_html=True)
    with col_p3:
        st.markdown("<p style='text-align:center;'>Ambas Marcam</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_btts), unsafe_allow_html=True)

    # --- PROBABILIDADES DE MERCADO (CANTOS) ---
    st.markdown("### 📈 Probabilidades Estimadas: Cantos FT")
    col_c1, col_c2, col_c3 = st.columns(3)
    
    p_cn85 = (1 - poisson.cdf(8, total_exp_cantos)) * 100
    p_cn95 = (1 - poisson.cdf(9, total_exp_cantos)) * 100
    p_cn105 = (1 - poisson.cdf(10, total_exp_cantos)) * 100

    with col_c1:
        st.markdown("<p style='text-align:center;'>Over 8.5 Cantos</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_cn85), unsafe_allow_html=True)
    with col_c2:
        st.markdown("<p style='text-align:center;'>Over 9.5 Cantos</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_cn95), unsafe_allow_html=True)
    with col_c3:
        st.markdown("<p style='text-align:center;'>Over 10.5 Cantos</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_cn105), unsafe_allow_html=True)

    st.info(f"💡 **Expectativa de Cantos:** O simulador projeta um total de **{total_exp_cantos:.1f}** cantos para este confronto (M: {exp_cantos_m:.1f} | V: {exp_cantos_v:.1f}).")
