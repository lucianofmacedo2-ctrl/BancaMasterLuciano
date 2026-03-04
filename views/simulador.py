import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson
from difflib import get_close_matches

def mostrar_simulador(df):
    # CSS Premium - Foco em Alto Contraste e Cores Dinâmicas
    st.markdown("""
        <style>
        .main-card {
            background-color: #0e1117;
            border-radius: 15px;
            padding: 20px;
            border: 1px solid #30363d;
            box-shadow: 0px 4px 15px rgba(0,0,0,0.5);
            margin-bottom: 20px;
            color: white;
        }
        .metric-card {
            background-color: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 15px;
            text-align: center;
            transition: 0.3s;
            height: 100%;
        }
        .metric-card:hover { border-color: #58a6ff; }
        
        /* Labels sempre em branco para contraste máximo */
        .stat-label { 
            font-size: 11px; 
            color: #ffffff; 
            text-transform: uppercase; 
            font-weight: 700; 
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        
        .stat-value { font-size: 26px; font-weight: bold; margin: 5px 0; }
        
        .trend-badge {
            display: inline-block; width: 22px; height: 22px; border-radius: 50%;
            margin: 0 2px; font-size: 11px; line-height: 22px; text-align: center; color: white; font-weight: bold;
        }
        .power-bar-container { background-color: #30363d; border-radius: 10px; height: 12px; width: 100%; margin: 10px 0; overflow: hidden;}
        .power-bar-fill { height: 100%; border-radius: 10px; transition: 0.5s; }
        </style>
    """, unsafe_allow_html=True)

    df.columns = [c.strip() for c in df.columns]

    # --- LÓGICA DE SELEÇÃO ---
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
        m_sel = st.selectbox("🏠 Mandante (Casa)", lista_times, index=idx_casa)
    
    visitantes_disp = sorted([t for t in lista_times if t != m_sel])
    idx_fora = 0
    if 'time_fora_simulador' in st.session_state:
        matches_v = get_close_matches(st.session_state.time_fora_simulador, visitantes_disp, n=1, cutoff=0.6)
        if matches_v: idx_fora = visitantes_disp.index(matches_v[0])

    with col_s2:
        v_sel = st.selectbox("🚌 Visitante (Fora)", visitantes_disp, index=idx_fora)

    # --- CÁLCULOS (CASA vs FORA) ---
    def get_team_stats_full(df_liga, time, local):
        if local == 'home':
            df_t = df_liga[df_liga['Mandante'] == time].sort_values('Data', ascending=False).head(8)
            gp = pd.to_numeric(df_t['Gols_Mandante_FT'], errors='coerce').fillna(0)
            gc = pd.to_numeric(df_t['Gols_Visitante_FT'], errors='coerce').fillna(0)
            posse = pd.to_numeric(df_t['Possession_H'], errors='coerce').fillna(50).mean()
            cn_ft = pd.to_numeric(df_t['Corners_H'], errors='coerce').fillna(0).mean()
            cn_ht = pd.to_numeric(df_t.get('Corners_H_HT', 0), errors='coerce').fillna(0).mean()
            cards = pd.to_numeric(df_t.get('Total_Cards_H', 0), errors='coerce').fillna(0).mean()
            p_0_15 = pd.to_numeric(df_t.get('0-15_Mandante', 0), errors='coerce').fillna(0).mean()
            viradas = len(df_t[(df_t['Gols_Visitante_HT'] > df_t['Gols_Mandante_HT']) & (df_t['Gols_Mandante_FT'] >= df_t['Gols_Visitante_FT'])])
        else:
            df_t = df_liga[df_liga['Visitante'] == time].sort_values('Data', ascending=False).head(8)
            gp = pd.to_numeric(df_t['Gols_Visitante_FT'], errors='coerce').fillna(0)
            gc = pd.to_numeric(df_t['Gols_Mandante_FT'], errors='coerce').fillna(0)
            posse = pd.to_numeric(df_t['Possession_A'], errors='coerce').fillna(50).mean()
            cn_ft = pd.to_numeric(df_t['Corners_A'], errors='coerce').fillna(0).mean()
            cn_ht = pd.to_numeric(df_t.get('Corners_A_HT', 0), errors='coerce').fillna(0).mean()
            cards = pd.to_numeric(df_t.get('Total_Cards_A', 0), errors='coerce').fillna(0).mean()
            p_0_15 = pd.to_numeric(df_t.get('0-15_Visitante', 0), errors='coerce').fillna(0).mean()
            viradas = len(df_t[(df_t['Gols_Mandante_HT'] > df_t['Gols_Visitante_HT']) & (df_t['Gols_Visitante_FT'] >= df_t['Gols_Mandante_FT'])])

        tendencia = []
        for _, r in df_t.head(5).iterrows():
            g_total = pd.to_numeric(r['Gols_Mandante_FT']) + pd.to_numeric(r['Gols_Visitante_FT'])
            if g_total > 2.5: tendencia.append(('O', '#238636'))
            else: tendencia.append(('U', '#da3633'))

        return gp.mean(), gc.mean(), cn_ft, cn_ht, cards, p_0_15, (viradas/len(df_t)*100 if len(df_t)>0 else 0), posse, tendencia

    s_m = get_team_stats_full(df_l, m_sel, 'home')
    s_v = get_team_stats_full(df_l, v_sel, 'away')

    exp_m = (s_m[0] + s_v[1]) / 2
    exp_v = (s_v[0] + s_m[1]) / 2
    total_g = exp_m + exp_v

    # Função auxiliar para cor dinâmica do valor
    def get_val_color(prob, threshold=60):
        return "#3fb950" if prob >= threshold else "#ffffff"

    # --- HEADER ---
    st.markdown(f"""
        <div class='main-card'>
            <div style='display: flex; justify-content: space-around; align-items: center;'>
                <div style='text-align: center;'>
                    <h3 style='margin:0; color:#58a6ff;'>{m_sel}</h3>
                    <div style='margin:8px 0;'>{' '.join([f"<span class='trend-badge' style='background:{c};'>{t}</span>" for t, c in s_m[8]])}</div>
                    <div class='stat-value' style='color:#ffffff;'>{exp_m:.2f}</div>
                    <div class='stat-label'>Gols Projetados</div>
                </div>
                <div style='font-size: 30px; font-weight: bold; color: #30363d;'>VS</div>
                <div style='text-align: center;'>
                    <h3 style='margin:0; color:#58a6ff;'>{v_sel}</h3>
                    <div style='margin:8px 0;'>{' '.join([f"<span class='trend-badge' style='background:{c};'>{t}</span>" for t, c in s_v[8]])}</div>
                    <div class='stat-value' style='color:#ffffff;'>{exp_v:.2f}</div>
                    <div class='stat-label'>Gols Projetados</div>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # --- PODER DE FOGO ---
    st.markdown("### ⚔️ Poder de Fogo (Ataque vs Defesa)")
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        p_m = min((s_m[0] / (s_v[1] + 0.1)) * 50, 100)
        st.write(f"**Ataque {m_sel}** vs Defesa {v_sel}")
        st.markdown(f"<div class='power-bar-container'><div class='power-bar-fill' style='width:{p_m}%; background:#238636;'></div></div>", unsafe_allow_html=True)
    with col_p2:
        p_v = min((s_v[0] / (s_m[1] + 0.1)) * 50, 100)
        st.write(f"**Ataque {v_sel}** vs Defesa {m_sel}")
        st.markdown(f"<div class='power-bar-container'><div class='power-bar-fill' style='width:{p_v}%; background:#238636;'></div></div>", unsafe_allow_html=True)

    # --- POSSE DE BOLA ---
    st.markdown("### 🏟️ Domínio de Campo (Posse)")
    t_posse = s_m[7] + s_v[7]
    pc_m = (s_m[7] / t_posse) * 100
    st.markdown(f"""
        <div style='display: flex; justify-content: space-between; margin-bottom: 5px; color:white; font-weight:bold;'>
            <span>{m_sel}: {pc_m:.1f}%</span>
            <span>{v_sel}: {100-pc_m:.1f}%</span>
        </div>
        <div class='power-bar-container'><div style='display: flex; height: 100%;'><div style='width:{pc_m}%; background:#58a6ff;'></div><div style='width:{100-pc_m}%; background:#238636;'></div></div></div>
    """, unsafe_allow_html=True)

    # --- INTELIGÊNCIA ---
    st.markdown("### ⚡ Inteligência de Momentos")
    ci1, ci2, ci3, ci4 = st.columns(4)
    prob_15 = (1 - poisson.pmf(0, (s_m[5] + s_v[5])/2)) * 100
    prob_vir = (s_m[6]+s_v[6])/2
    cs_m = poisson.pmf(0, exp_v)*100
    cs_v = poisson.pmf(0, exp_m)*100

    ci1.markdown(f"<div class='metric-card'><div class='stat-label'>Pressão 0-15'</div><div class='stat-value' style='color:{get_val_color(prob_15, 30)};'>{prob_15:.1f}%</div></div>", unsafe_allow_html=True)
    ci2.markdown(f"<div class='metric-card'><div class='stat-label'>Prob. Virada</div><div class='stat-value' style='color:{get_val_color(prob_vir, 15)};'>{prob_vir:.1f}%</div></div>", unsafe_allow_html=True)
    ci3.markdown(f"<div class='metric-card'><div class='stat-label'>Clean Sheet (C)</div><div class='stat-value' style='color:{get_val_color(cs_m, 40)};'>{cs_m:.1f}%</div></div>", unsafe_allow_html=True)
    ci4.markdown(f"<div class='metric-card'><div class='stat-label'>Clean Sheet (F)</div><div class='stat-value' style='color:{get_val_color(cs_v, 40)};'>{cs_v:.1f}%</div></div>", unsafe_allow_html=True)

    # --- GOLS ---
    st.markdown("### ⚽ Projeções de Gols")
    btts = ((1 - poisson.pmf(0, exp_m)) * (1 - poisson.pmf(0, exp_v))) * 100
    ov15 = (1 - poisson.cdf(1, total_g))*100
    ov25 = (1 - poisson.cdf(2, total_g))*100
    ov05ht = (1 - poisson.pmf(0, total_g/2.2))*100

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='metric-card'><div class='stat-label'>Over 1.5 FT</div><div class='stat-value' style='color:{get_val_color(ov15, 75)};'>{ov15:.1f}%</div></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='metric-card'><div class='stat-label'>Over 2.5 FT</div><div class='stat-value' style='color:{get_val_color(ov25, 60)};'>{ov25:.1f}%</div></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='metric-card'><div class='stat-label'>Ambas Marcam</div><div class='stat-value' style='color:{get_val_color(btts, 55)};'>{btts:.1f}%</div></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='metric-card'><div class='stat-label'>Over 0.5 HT</div><div class='stat-value' style='color:{get_val_color(ov05ht, 70)};'>{ov05ht:.1f}%</div></div>", unsafe_allow_html=True)

    # --- CANTOS ---
    st.markdown("### 🚩 Mercado de Cantos (Timing)")
    c_ht = s_m[3] + s_v[3]
    c_ft = s_m[2] + s_v[2]
    cc1, cc2, cc3 = st.columns(3)
    cc1.markdown(f"<div class='metric-card'><div class='stat-label'>Cantos 1º Tempo</div><div class='stat-value' style='color:#ffffff;'>{c_ht:.1f}</div></div>", unsafe_allow_html=True)
    cc2.markdown(f"<div class='metric-card'><div class='stat-label'>Cantos 2º Tempo</div><div class='stat-value' style='color:#ffffff;'>{c_ft - c_ht:.1f}</div></div>", unsafe_allow_html=True)
    cc3.markdown(f"<div class='metric-card'><div class='stat-label'>Total Cantos FT</div><div class='stat-value' style='color:#3fb950;'>{c_ft:.1f}</div></div>", unsafe_allow_html=True)

    # --- CARTÕES ---
    st.markdown("### 🟨 Mercado de Cartões")
    t_c = s_m[4] + s_v[4]
    cr1, cr2, cr3 = st.columns(3)
    o35c = (1-poisson.cdf(3, t_c))*100
    cr1.markdown(f"<div class='metric-card'><div class='stat-label'>Over 3.5 Cards</div><div class='stat-value' style='color:{get_val_color(o35c, 65)};'>{o35c:.1f}%</div></div>", unsafe_allow_html=True)
    cr2.markdown(f"<div class='metric-card'><div class='stat-label'>Over 4.5 Cards</div><div class='stat-value' style='color:{get_val_color((1-poisson.cdf(4, t_c))*100, 50)};'>{(1-poisson.cdf(4, t_c))*100:.1f}%</div></div>", unsafe_allow_html=True)
    cr3.markdown(f"<div class='metric-card'><div class='stat-label'>Média Total</div><div class='stat-value' style='color:#ffffff;'>{t_c:.1f}</div></div>", unsafe_allow_html=True)

    # --- PLACARES ---
    st.markdown("### 🏆 Top 3 Placares Exatos")
    prob_mat = np.outer(poisson.pmf(np.arange(5), exp_m), poisson.pmf(np.arange(5), exp_v))
    plcs = []
    for i in range(5):
        for j in range(5): plcs.append((f"{i} x {j}", prob_mat[i, j] * 100))
    plcs = sorted(plcs, key=lambda x: x[1], reverse=True)[:3]
    cp1, cp2, cp3 = st.columns(3)
    for i, (p, prob) in enumerate(plcs):
        [cp1, cp2, cp3][i].markdown(f"<div style='background:#0d1117; border: 1px solid #30363d; border-radius:10px; padding:10px; text-align:center;'><small style='color:#ffffff'>Rank {i+1}</small><br><b style='color:#ffffff; font-size:20px;'>{p}</b><br><span style='color:#3fb950;'>{prob:.1f}%</span></div>", unsafe_allow_html=True)

    st.divider()
    st.info(f"💡 **Análise Profissional:** Dados baseados nos últimos 8 jogos do **{m_sel} em Casa** e **{v_sel} Fora**.")
