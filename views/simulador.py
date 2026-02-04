import streamlit as st
import pandas as pd

def mostrar_simulador(df):
    st.markdown("## 🎲 Simulador de Confrontos")
    st.write("Projeção de placar e probabilidades baseada em médias de ataque e defesa.")

    # 1. Limpeza
    df.columns = [c.strip() for c in df.columns]

    # 2. SELEÇÃO DE TIMES (Mesma lógica do Scout)
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
        # Gols Pró
        gp = pd.concat([df_t[df_t['Mandante'] == time]['Gols_Mandante_FT'], df_t[df_t['Visitante'] == time]['Gols_Visitante_FT']]).mean()
        # Gols Contra
        gc = pd.concat([df_t[df_t['Mandante'] == time]['Gols_Visitante_FT'], df_t[df_t['Visitante'] == time]['Gols_Mandante_FT']]).mean()
        return gp, gc

    gp_m, gc_m = get_team_stats(df_l, m_sel)
    gp_v, gc_v = get_team_stats(df_l, v_sel)

    # 4. PROJEÇÃO (Fórmula: (Gols Pró Time A + Gols Contra Time B) / 2)
    exp_gols_m = (gp_m + gc_v) / 2
    exp_gols_v = (gp_v + gc_m) / 2

    st.divider()

    # --- EXIBIÇÃO DO PLACAR PROJETADO ---
    c_res1, c_res2, c_res3 = st.columns([2, 1, 2])
    with c_res1:
        st.subheader(m_sel)
        st.title(f"{exp_gols_m:.2f}")
        st.caption("Gols Estimados")
    with c_res2:
        st.title("VS")
    with c_res3:
        st.subheader(v_sel)
        st.title(f"{exp_gols_v:.2f}")
        st.caption("Gols Estimados")

    st.divider()

    # --- PROBABILIDADES DE MERCADO ---
    st.markdown("### 📈 Probabilidades Estimadas")
    
    # Estimativa simples baseada na soma das expectativas
    total_exp = exp_gols_m + exp_gols_v
    prob_btts = ( (gp_m > 0.8) and (gp_v > 0.8) ) # Lógica simplificada
    
    col_p1, col_p2, col_p3 = st.columns(3)
    
    def format_prob(val):
        color = "green" if val > 60 else "orange" if val > 40 else "red"
        return f"<h2 style='color:{color}; text-align:center;'>{val:.1f}%</h2>"

    # Cálculo aproximado de probabilidade
    p_over15 = min(95.0, (total_exp / 1.5) * 50)
    p_over25 = min(90.0, (total_exp / 2.5) * 50)
    p_btts = 70.0 if (gp_m > 1 and gp_v > 1) else 45.0

    with col_p1:
        st.markdown("<p style='text-align:center;'>Over 1.5 FT</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_over15), unsafe_allow_html=True)
    with col_p2:
        st.markdown("<p style='text-align:center;'>Over 2.5 FT</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_over25), unsafe_allow_html=True)
    with col_p3:
        st.markdown("<p style='text-align:center;'>Ambas Marcam</p>", unsafe_allow_html=True)
        st.markdown(format_prob(p_btts), unsafe_allow_html=True)

    st.info("💡 **Dica:** Esta simulação cruza o ataque de um time com a defesa do outro. É uma tendência matemática, não uma garantia.")
