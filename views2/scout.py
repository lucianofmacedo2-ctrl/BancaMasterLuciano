import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from difflib import get_close_matches

def mostrar_scout(df):
    st.markdown("## 🔎 Painel de Análise Profissional - Sistema 2")
    
    # 1. Ajuste e Limpeza de Colunas
    df.columns = [c.strip() for c in df.columns]

    # --- LÓGICA DE INDEXAÇÃO AUTOMÁTICA ---
    lista_ligas = sorted(df['Liga'].unique())
    idx_liga = 0
    # Nota: Usamos session_state específico do sistema 2 se houver integração de navegação
    if 'liga_scout_2' in st.session_state:
        matches_l = get_close_matches(st.session_state.liga_scout_2, lista_ligas, n=1, cutoff=0.6)
        if matches_l:
            idx_liga = lista_ligas.index(matches_l[0])

    # 2. SELEÇÃO DA LIGA
    liga_sel = st.selectbox("🏆 Escolha a Liga (S2)", lista_ligas, index=idx_liga, key="sel_liga_scout_2")
    df_l = df[df['Liga'] == liga_sel].copy()

    if 'Temporada' in df_l.columns:
        temp_atual = df_l['Temporada'].max()
        df_temp = df_l[df_l['Temporada'] == temp_atual].copy()
    else:
        df_temp = df_l.copy()

    # --- SELEÇÃO DE TIMES ---
    lista_times = sorted(df_l['Mandante'].unique())
    
    idx_casa = 0
    if 'time_casa_scout_2' in st.session_state:
        matches_m = get_close_matches(st.session_state.time_casa_scout_2, lista_times, n=1, cutoff=0.6)
        if matches_m:
            idx_casa = lista_times.index(matches_m[0])

    m_sel = st.selectbox("🏠 Time da Casa (S2)", lista_times, index=idx_casa, key="sel_casa_scout_2")
    
    visitantes_disp = [t for t in lista_times if t != m_sel]
    idx_fora = 0
    if 'time_fora_scout_2' in st.session_state:
        matches_v = get_close_matches(st.session_state.time_fora_scout_2, visitantes_disp, n=1, cutoff=0.6)
        if matches_v:
            idx_fora = visitantes_disp.index(matches_v[0])

    v_sel = st.selectbox("🚌 Time de Fora (S2)", visitantes_disp, index=idx_fora, key="sel_fora_scout_2")

    n_jogos = st.sidebar.slider("Amostragem S2 (Últimos Jogos)", 5, 50, 10, key="slider_scout_2")

    # --- FUNÇÕES DE APOIO ---
    def extrair_metrica(df_hist, time, col_h, col_a):
        m = df_hist[df_hist['Mandante'] == time][col_h]
        v = df_hist[df_hist['Visitante'] == time][col_a]
        return pd.to_numeric(pd.concat([m, v]), errors='coerce').fillna(0)

    def calcular_tabela(df_input, apenas_mando=None):
        stats = {}
        for _, r in df_input.iterrows():
            m, v = r['Mandante'], r['Visitante']
            gm, gv = float(r['Gols_Mandante_FT']), float(r['Gols_Visitante_FT'])
            for t in [m, v]:
                if t not in stats: stats[t] = {'P': 0, 'V': 0, 'SG': 0, 'J': 0}
            if apenas_mando == 'Casa':
                stats[m]['J'] += 1; stats[m]['SG'] += (gm - gv)
                if gm > gv: stats[m]['P'] += 3; stats[m]['V'] += 1
                elif gm == gv: stats[m]['P'] += 1
            elif apenas_mando == 'Fora':
                stats[v]['J'] += 1; stats[v]['SG'] += (gv - gm)
                if gv > gm: stats[v]['P'] += 3; stats[v]['V'] += 1
                elif gm == gv: stats[v]['P'] += 1
            else:
                stats[m]['J'] += 1; stats[v]['J'] += 1
                stats[m]['SG'] += (gm - gv); stats[v]['SG'] += (gv - gm)
                if gm > gv: stats[m]['P'] += 3; stats[m]['V'] += 1
                elif gm == gv: stats[m]['P'] += 1; stats[v]['P'] += 1
                else: stats[v]['P'] += 3; stats[v]['V'] += 1
        tab = pd.DataFrame.from_dict(stats, orient='index').reset_index().rename(columns={'index':'Time'})
        tab['PPG'] = tab['P'] / tab['J'].replace(0, 1)
        tab = tab.sort_values(by=['P', 'V', 'SG'], ascending=False).reset_index(drop=True)
        tab['Pos'] = tab.index + 1
        return tab

    def get_forma_lista(df_hist, time, modo='Geral'):
        if modo == 'Casa': df_f = df_hist[df_hist['Mandante'] == time]
        elif modo == 'Fora': df_f = df_hist[df_hist['Visitante'] == time]
        else: df_f = df_hist[(df_hist['Mandante'] == time) | (df_hist['Visitante'] == time)]
        df_f = df_f.sort_values('Data', ascending=False).head(5)
        res = []
        for _, r in df_f.iterrows():
            gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
            if gm == gv: res.append("🟡")
            elif (r['Mandante'] == time and gm > gv) or (r['Visitante'] == time and gv > gm): res.append("🟢")
            else: res.append("🔴")
        return " ".join(res) if res else "N/A"

    # --- CÁLCULO COEFICIENTE DE FORÇA ---
    def calcular_coeficiente(time, df_liga, posicao='Mandante'):
        df_t_geral = df_liga[(df_liga['Mandante'] == time) | (df_liga['Visitante'] == time)]
        df_t_split = df_liga[df_liga['Mandante'] == time] if posicao == 'Mandante' else df_liga[df_liga['Visitante'] == time]
        if df_t_split.empty or df_t_geral.empty: return 0.0
        
        tab_g = calcular_tabela(df_liga)
        ppg_g = tab_g[tab_g['Time'] == time]['PPG'].iloc[0] if time in tab_g['Time'].values else 0
        tab_s = calcular_tabela(df_liga, 'Casa' if posicao == 'Mandante' else 'Fora')
        ppg_s = tab_s[tab_s['Time'] == time]['PPG'].iloc[0] if time in tab_s['Time'].values else 0

        gm_g = extrair_metrica(df_t_geral, time, 'Gols_Mandante_FT', 'Gols_Visitante_FT').mean()
        gs_g = extrair_metrica(df_t_geral, time, 'Gols_Visitante_FT', 'Gols_Mandante_FT').mean()
        gm_s = df_t_split['Gols_Mandante_FT' if posicao == 'Mandante' else 'Gols_Visitante_FT'].mean()
        gs_s = df_t_split['Gols_Visitante_FT' if posicao == 'Mandante' else 'Gols_Mandante_FT'].mean()
        odd_avg = df_t_split['Odd_Mandante_FT' if posicao == 'Mandante' else 'Odd_Visitante_FT'].mean()
        posse = (df_t_split['Possession_H' if posicao == 'Mandante' else 'Possession_A'].mean()) / 10
        atq = (df_t_split['Attacks_H' if posicao == 'Mandante' else 'Attacks_A'].mean() + df_t_split['DangerousAttacks_H' if posicao == 'Mandante' else 'DangerousAttacks_A'].mean()) / 10
        shots = (df_t_split['Shots_H' if posicao == 'Mandante' else 'Shots_A'].mean() + df_t_split['ShotsOnTarget_H' if posicao == 'Mandante' else 'ShotsOnTarget_A'].mean())
        cantos = (df_t_split['Corners_H' if posicao == 'Mandante' else 'Corners_A'].mean()) / 4

        l_score = 0
        l_score += (df_t_split['Total_Gols_HT'] > 0.5).mean() * 10
        l_score += (df_t_split['Total_Gols_HT'] > 1.5).mean() * 5
        l_score += (df_t_split['Total_Gols_FT'] > 1.5).mean() * 10
        l_score += (df_t_split['Total_Gols_FT'] > 2.5).mean() * 5
        l_score += ((df_t_split['Gols_Mandante_HT']>0) & (df_t_split['Gols_Visitante_HT']>0)).mean() * 2
        l_score += ((df_t_split['Gols_Mandante_FT']>0) & (df_t_split['Gols_Visitante_FT']>0)).mean() * 5

        coef = (ppg_g) + (ppg_s * 2) + (gm_g) + (gm_s * 2) - (gs_g) - (gs_s * 2) - odd_avg + posse + atq + shots + cantos + l_score
        if gm_g > df_liga['Total_Gols_FT'].mean(): coef += 1
        return max(coef, 0)

    # --- 2. CARDS DE INFORMAÇÃO ---
    st.divider()
    t_geral = calcular_tabela(df_temp)
    t_casa = calcular_tabela(df_temp, 'Casa')
    t_fora = calcular_tabela(df_temp, 'Fora')

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### 🏠 {m_sel}")
        cf_m = calcular_coeficiente(m_sel, df_temp, 'Mandante')
        st.info(f"**Índice de Força: {cf_m:.2f}**")
        cc1, cc2 = st.columns(2)
        cc1.metric("Pos. Geral", f"{t_geral[t_geral['Time']==m_sel]['Pos'].iloc[0]}º")
        cc2.metric("Pos. Casa", f"{t_casa[t_casa['Time']==m_sel]['Pos'].iloc[0] if m_sel in t_casa['Time'].values else '?'}º")
        st.write(f"**Forma Geral:** {get_forma_lista(df_temp, m_sel)}")
        st.write(f"**Forma Casa:** {get_forma_lista(df_temp, m_sel, 'Casa')}")

    with c2:
        st.markdown(f"### 🚌 {v_sel}")
        cf_v = calcular_coeficiente(v_sel, df_temp, 'Visitante')
        st.error(f"**Índice de Força: {cf_v:.2f}**")
        cv1, cv2 = st.columns(2)
        cv1.metric("Pos. Geral", f"{t_geral[t_geral['Time']==v_sel]['Pos'].iloc[0]}º")
        cv2.metric("Pos. Fora", f"{t_fora[t_fora['Time']==v_sel]['Pos'].iloc[0] if v_sel in t_fora['Time'].values else '?'}º")
        st.write(f"**Forma Geral:** {get_forma_lista(df_temp, v_sel)}")
        st.write(f"**Forma Fora:** {get_forma_lista(df_temp, v_sel, 'Fora')}")

    # --- 3. RADAR DE ESTILO ---
    st.divider()
    st.subheader("🕸️ Radar de Estilo de Jogo (S2 - Normalizado)")
    def criar_radar(t1, t2, df_temp):
        metrics = ['Gols', 'Cantos', 'Posse', 'Ataque', 'Chutes']
        def get_vals(time):
            d = df_temp[(df_temp['Mandante']==time)|(df_temp['Visitante']==time)]
            return [extrair_metrica(d, time, 'Total_Gols_FT', 'Total_Gols_FT').mean()*20,
                    extrair_metrica(d, time, 'Corners_H', 'Corners_A').mean()*10,
                    extrair_metrica(d, time, 'Possession_H', 'Possession_A').mean(),
                    extrair_metrica(d, time, 'DangerousAttacks_H', 'DangerousAttacks_A').mean(),
                    extrair_metrica(d, time, 'Shots_H', 'Shots_A').mean()*5]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=get_vals(t1), theta=metrics, fill='toself', name=t1))
        fig.add_trace(go.Scatterpolar(r=get_vals(t2), theta=metrics, fill='toself', name=t2))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)
    criar_radar(m_sel, v_sel, df_temp)

    # --- 4. MOMENTUM ---
    st.subheader("📈 Momentum e Tendência xG (S2)")
    def plot_momentum(t1, t2, df_l):
        d1 = df_l[(df_l['Mandante']==t1)|(df_l['Visitante']==t1)].tail(10)
        d2 = df_l[(df_l['Mandante']==t2)|(df_l['Visitante']==t2)].tail(10)
        fig = go.Figure()
        fig.add_trace(go.Scatter(y=extrair_metrica(d1, t1, 'Total_xG', 'Total_xG'), mode='lines+markers', name=t1))
        fig.add_trace(go.Scatter(y=extrair_metrica(d2, t2, 'Total_xG', 'Total_xG'), mode='lines+markers', name=t2))
        st.plotly_chart(fig, use_container_width=True)
    plot_momentum(m_sel, v_sel, df_l)

    # --- 5. ESTATÍSTICAS DETALHADAS ---
    st.divider()
    st.subheader("📉 Estatísticas de Performance Detalhadas (S2)")
    
    def color_stats(val):
        color = 'background-color: #d4edda' if isinstance(val, float) and val < 1.0 else ''
        return color

    def st_tabela_estilizada(df_m, df_v, t1, t2, titulo, dicionario_metricas):
        st.markdown(f"#### {titulo}")
        def process(df_h, time, label, cols):
            s = extrair_metrica(df_h, time, cols[0], cols[1])
            m = s.mean(); std = s.std(); cv = std/m if m!=0 else 0
            return [label, m, s.median(), s.mode().iloc[0] if not s.mode().empty else 0, std, cv]
        
        cols_n = ['Métrica', 'Média', 'Mediana', 'Moda', 'DP', 'CV']
        ca, cb = st.columns(2)
        
        df1 = pd.DataFrame([process(df_m, t1, k, v) for k, v in dicionario_metricas.items()], columns=cols_n)
        df2 = pd.DataFrame([process(df_v, t2, k, v) for k, v in dicionario_metricas.items()], columns=cols_n)
        
        ca.write(f"**{t1}**")
        ca.table(df1.style.format({c: "{:.2f}" for c in cols_n[1:]}).applymap(color_stats, subset=['DP', 'CV']))
        cb.write(f"**{t2}**")
        cb.table(df2.style.format({c: "{:.2f}" for c in cols_n[1:]}).applymap(color_stats, subset=['DP', 'CV']))

    df_m_last = df_l[(df_l['Mandante']==m_sel)|(df_l['Visitante']==m_sel)].sort_values('Data', ascending=False).head(n_jogos)
    df_v_last = df_l[(df_l['Mandante']==v_sel)|(df_l['Visitante']==v_sel)].sort_values('Data', ascending=False).head(n_jogos)

    st_tabela_estilizada(df_m_last, df_v_last, m_sel, v_sel, "⚽ Gols", {"Marcados":('Gols_Mandante_FT','Gols_Visitante_FT'), "Sofridos":('Gols_Visitante_FT','Gols_Mandante_FT'), "Total (M+S)":('Total_Gols_FT','Total_Gols_FT')})
    st_tabela_estilizada(df_m_last, df_v_last, m_sel, v_sel, "🚩 Cantos", {"Marcados FT":('Corners_H','Corners_A'), "Sofridos FT":('Corners_A','Corners_H'), "Marcados HT":('Corners_H_HT','Corners_A_HT'), "Sofridos HT":('Corners_A_HT','Corners_H_HT')})
    st_tabela_estilizada(df_m_last, df_v_last, m_sel, v_sel, "🎯 Chutes", {"No Gol Marcados":('ShotsOnTarget_H','ShotsOnTarget_A'), "No Gol Sofridos":('ShotsOnTarget_A','ShotsOnTarget_H'), "Total":('Shots_H','Shots_A')})
    st_tabela_estilizada(df_m_last, df_v_last, m_sel, v_sel, "⚖️ Disciplina & xG", {"Faltas Sofridas":('Freekicks_H','Freekicks_A'), "Faltas Cometidas":('Fouls_H','Fouls_A'), "Amarelos":('Yellow_Cards_H','Yellow_Cards_A'), "xG":('xG_Mandante','xG_Visitante'), "Posse":('Possession_H','Possession_A')})

    # --- 6. CALCULADORA DE VALOR ---
    st.divider()
    st.subheader("💎 Calculadora de Valor e Incidência (S2)")
    def calc_inc_full(df_h):
        m = {
            'O 0.5 HT': df_h['Total_Gols_HT']>0.5, 'O 1.5 HT': df_h['Total_Gols_HT']>1.5, 'BTTS Sim HT': (df_h['Gols_Mandante_HT']>0)&(df_h['Gols_Visitante_HT']>0),
            'O 1.5 FT': df_h['Total_Gols_FT']>1.5, 'O 2.5 FT': df_h['Total_Gols_FT']>2.5, 'BTTS Sim FT': (df_h['Gols_Mandante_FT']>0)&(df_h['Gols_Visitante_FT']>0),
            'O 3.5 Cantos HT': df_h['Total_Corners_HT']>3.5, 'O 4.5 Cantos HT': df_h['Total_Corners_HT']>4.5,
            'O 8.5 Cantos FT': df_h['Total_Corners']>8.5, 'O 9.5 Cantos FT': df_h['Total_Corners']>9.5, 'O 10.5 Cantos FT': df_h['Total_Corners']>10.5
        }
        return pd.DataFrame([{'Mercado': k, 'Freq': f"{v.mean()*100:.1f}%", 'Odd Justa': f"{1/v.mean():.2f}" if v.mean()>0 else 'N/A'} for k, v in m.items()])
    
    ci1, ci2 = st.columns(2)
    ci1.write(f"**{m_sel}**"); ci1.table(calc_inc_full(df_m_last))
    ci2.write(f"**{v_sel}**"); ci2.table(calc_inc_full(df_v_last))

    # --- 7. HISTÓRICO DETALHADO ---
    st.divider()
    st.subheader("📝 Histórico Detalhado (S2)")
    def hist_final(df_h, time, modo='Geral'):
        if modo == 'Casa': df_f = df_h[df_h['Mandante'] == time]
        elif modo == 'Fora': df_f = df_h[df_h['Visitante'] == time]
        else: df_f = df_h[(df_h['Mandante']==time)|(df_h['Visitante']==time)]
        df_f = df_f.sort_values('Data', ascending=False).head(10)
        res = []
        for _, r in df_f.iterrows():
            res.append({
                'Data': r['Data'], 'Mando': 'Casa' if r['Mandante']==time else 'Fora', 'Oponente': r['Visitante'] if r['Mandante']==time else r['Mandante'],
                'FT': f"{int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])}", 'HT': f"{int(r['Gols_Mandante_HT'])}x{int(r['Gols_Visitante_HT'])}",
                'Cantos HT': r['Total_Corners_HT'], 'Cantos FT': r['Total_Corners'], 'xG': f"{r['xG_Mandante']}-{r['xG_Visitante']}",
                'Odd H': r['Odd_Mandante_FT'], 'Odd D': r['Odd_Empate_FT'], 'Odd A': r['Odd_Visitante_FT']
            })
        return pd.DataFrame(res)

    st.write(f"**{m_sel}: Últimos 10 Gerais**"); st.table(hist_final(df_l, m_sel))
    st.write(f"**{m_sel}: Últimos 10 em Casa**"); st.table(hist_final(df_l, m_sel, 'Casa'))
    st.write(f"**{v_sel}: Últimos 10 Gerais**"); st.table(hist_final(df_l, v_sel))
    st.write(f"**{v_sel}: Últimos 10 Fora**"); st.table(hist_final(df_l, v_sel, 'Fora'))
