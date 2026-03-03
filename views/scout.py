import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from difflib import get_close_matches

def mostrar_scout(df):
    st.markdown("## 🔎 Painel de Análise Profissional Ultra V3 - Inteligência Ativa")
    
    # 1. Ajuste e Limpeza de Colunas
    df.columns = [c.strip() for c in df.columns]

    # --- LÓGICA DE INDEXAÇÃO AUTOMÁTICA (SESSÃO) ---
    lista_ligas = sorted(df['Liga'].unique())
    idx_liga = 0
    if 'liga_scout' in st.session_state:
        matches_l = get_close_matches(st.session_state.liga_scout, lista_ligas, n=1, cutoff=0.6)
        if matches_l:
            idx_liga = lista_ligas.index(matches_l[0])

    # 2. SELEÇÃO DA LIGA E TEMPO
    liga_sel = st.selectbox("🏆 Escolha a Liga", lista_ligas, index=idx_liga)
    df_l = df[df['Liga'] == liga_sel].copy()

    if 'Temporada' in df_l.columns:
        temp_atual = df_l['Temporada'].max()
        df_temp = df_l[df_l['Temporada'] == temp_atual].copy()
    else:
        df_temp = df_l.copy()

    # --- SELEÇÃO DE TIMES ---
    lista_times = sorted(df_l['Mandante'].unique())
    
    idx_casa = 0
    if 'time_casa_scout' in st.session_state:
        matches_m = get_close_matches(st.session_state.time_casa_scout, lista_times, n=1, cutoff=0.6)
        if matches_m:
            idx_casa = lista_times.index(matches_m[0])

    m_sel = st.selectbox("🏠 Time da Casa", lista_times, index=idx_casa)
    
    visitantes_disp = [t for t in lista_times if t != m_sel]
    idx_fora = 0
    if 'time_fora_scout' in st.session_state:
        matches_v = get_close_matches(st.session_state.time_fora_scout, visitantes_disp, n=1, cutoff=0.6)
        if matches_v:
            idx_fora = visitantes_disp.index(matches_v[0])

    v_sel = st.selectbox("🚌 Time de Fora", visitantes_disp, index=idx_fora)

    n_jogos = st.sidebar.slider("Amostragem (Últimos Jogos)", 5, 50, 10)

    # --- FUNÇÕES DE APOIO (PRESERVADAS) ---
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
        gs_s = df_t_split['Gols_Visitante_FT' if posicao == 'Mandante' else 'Gols_Visitante_FT'].mean()
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

    # --- INÍCIO DA INTERFACE ---
    st.divider()
    t_geral = calcular_tabela(df_temp)
    t_casa = calcular_tabela(df_temp, 'Casa')
    t_fora = calcular_tabela(df_temp, 'Fora')

    # --- 1. CARDS DE FORÇA E ODD JUSTA (PAINEL DE VALOR) ---
    cf_m = calcular_coeficiente(m_sel, df_temp, 'Mandante')
    cf_v = calcular_coeficiente(v_sel, df_temp, 'Visitante')
    
    total_f = cf_m + cf_v
    if total_f > 0:
        prob_m = (cf_m / total_f) * 0.85
        prob_v = (cf_v / total_f) * 0.85
        oj_m, oj_v = 1/prob_m, 1/prob_v
    else: oj_m, oj_v = 2.0, 2.0

    # Busca a odd atual do mercado no DF para comparar valor
    odd_atual_m = df_temp[df_temp['Mandante']==m_sel]['Odd_Mandante_FT'].iloc[0] if 'Odd_Mandante_FT' in df_temp.columns else 0

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### 🏠 {m_sel}")
        st.info(f"**Índice de Força: {cf_m:.2f}**")
        st.metric("Odd Justa", f"{oj_m:.2f}")
        if odd_atual_m > oj_m:
            st.success(f"💎 VALOR: Casa paga {odd_atual_m:.2f} (Justa: {oj_m:.2f})")
        
        cc1, cc2 = st.columns(2)
        cc1.metric("Pos. Geral", f"{t_geral[t_geral['Time']==m_sel]['Pos'].iloc[0]}º")
        cc2.metric("Pos. Casa", f"{t_casa[t_casa['Time']==m_sel]['Pos'].iloc[0] if m_sel in t_casa['Time'].values else '?'}º")
        st.write(f"**Forma Geral:** {get_forma_lista(df_temp, m_sel)}")

    with c2:
        st.markdown(f"### 🚌 {v_sel}")
        st.error(f"**Índice de Força: {cf_v:.2f}**")
        st.metric("Odd Justa", f"{oj_v:.2f}")
        
        cv1, cv2 = st.columns(2)
        cv1.metric("Pos. Geral", f"{t_geral[t_geral['Time']==v_sel]['Pos'].iloc[0]}º")
        cv2.metric("Pos. Fora", f"{t_fora[t_fora['Time']==v_sel]['Pos'].iloc[0] if v_sel in t_fora['Time'].values else '?'}º")
        st.write(f"**Forma Geral:** {get_forma_lista(df_temp, v_sel)}")

    # --- 2. FILTRO DE CONSISTÊNCIA (SELOS) ---
    st.divider()
    st.subheader("🛡️ Checklist de Confiança Estatística")
    
    def verificar_consistencia(time, df_h):
        gols = extrair_metrica(df_h, time, 'Total_Gols_FT', 'Total_Gols_FT')
        if len(gols) > 0:
            cv = gols.std() / gols.mean() if gols.mean() > 0 else 1.0
            if cv < 0.8: st.success(f"✅ {time}: Estatística Estável (CV: {cv:.2f})")
            else: st.warning(f"⚠️ {time}: Time Irregular (CV: {cv:.2f})")
        
    df_m_last = df_l[(df_l['Mandante']==m_sel)|(df_l['Visitante']==m_sel)].sort_values('Data', ascending=False).head(n_jogos)
    df_v_last = df_l[(df_l['Mandante']==v_sel)|(df_l['Visitante']==v_sel)].sort_values('Data', ascending=False).head(n_jogos)
    
    sc1, sc2 = st.columns(2)
    with sc1: verificar_consistencia(m_sel, df_m_last)
    with sc2: verificar_consistencia(v_sel, df_v_last)

    # --- 3. RADAR E CONCLUSÃO DE ESTILO ---
    st.divider()
    st.subheader("🕸️ Radar e Conclusão de Estilos")
    
    def criar_radar_e_conclusao(t1, t2, df_temp, d1, d2):
        metrics = ['Gols', 'Cantos', 'Posse', 'Ataque', 'Chutes']
        def get_vals(time):
            d = df_temp[(df_temp['Mandante']==time)|(df_temp['Visitante']==time)]
            return [extrair_metrica(d, time, 'Total_Gols_FT', 'Total_Gols_FT').mean()*20,
                    extrair_metrica(d, time, 'Corners_H', 'Corners_A').mean()*10,
                    extrair_metrica(d, time, 'Possession_H', 'Possession_A').mean(),
                    extrair_metrica(d, time, 'DangerousAttacks_H', 'DangerousAttacks_A').mean(),
                    extrair_metrica(d, time, 'Shots_H', 'Shots_A').mean()*5]
        
        # Conclusão Lógica
        posse_m = d1['Possession_H'].mean()
        chutes_v_levados = d2['Shots_H'].mean()
        if posse_m > 55 and chutes_v_levados > 10:
            st.info(f"📝 **Cenário de Pressão:** {t1} domina a posse e {t2} permite muitas finalizações.")
        elif d1['xG_Mandante'].mean() > 1.6 and d2['xG_Visitante'].mean() > 1.6:
            st.info(f"📝 **Cenário de BTTS:** Ambos com alto volume de xG (Gols Esperados).")

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=get_vals(t1), theta=metrics, fill='toself', name=t1))
        fig.add_trace(go.Scatterpolar(r=get_vals(t2), theta=metrics, fill='toself', name=t2))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

    criar_radar_e_conclusao(m_sel, v_sel, df_temp, df_m_last, df_v_last)

    # --- 4. GOLS POR FAIXA DE TEMPO (GRÁFICO DE ÁREA) ---
    st.subheader("⏰ Distribuição de Gols (Ideal para Live)")
    labels_tempo = ["0-15'", "16-30'", "31-45'", "46-60'", "61-75'", "76-90'"]
    def get_f(time, df_h):
        d = df_h[(df_h['Mandante']==time)|(df_h['Visitante']==time)]
        cols_m = ['0-15_Mandante', '16-30_Mandante', '31-45+_Mandante', '46-60_Mandante', '61-75_Mandante', '76-90+_Mandante']
        cols_v = ['0-15_Visitante', '16-30_Visitante', '31-45+_Visitante', '46-60_Visitante', '61-75_Visitante', '76-90+_Visitante']
        return [extrair_metrica(d, time, cm, cv).mean() for cm, cv in zip(cols_m, cols_v)]
    
    f_m = get_f(m_sel, df_m_last)
    f_v = get_f(v_sel, df_v_last)
    
    fig_area = go.Figure()
    fig_area.add_trace(go.Scatter(x=labels_tempo, y=f_m, fill='tozeroy', name=m_sel))
    fig_area.add_trace(go.Scatter(x=labels_tempo, y=f_v, fill='tozeroy', name=v_sel))
    st.plotly_chart(fig_area, use_container_width=True)

    # --- 5. ESTATÍSTICAS DETALHADAS (DISPERSÃO DP/CV) ---
    st.divider()
    st.subheader("📉 Performance Detalhada (Média, DP e CV)")
    
    def color_stats(val):
        return 'background-color: #d4edda' if isinstance(val, float) and val < 1.0 else ''

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
        ca.write(f"**{t1}**"); ca.table(df1.style.format({c: "{:.2f}" for c in cols_n[1:]}).applymap(color_stats, subset=['DP', 'CV']))
        cb.write(f"**{t2}**"); cb.table(df2.style.format({c: "{:.2f}" for c in cols_n[1:]}).applymap(color_stats, subset=['DP', 'CV']))

    st_tabela_estilizada(df_m_last, df_v_last, m_sel, v_sel, "⚽ Gols", {"Marcados":('Gols_Mandante_FT','Gols_Visitante_FT'), "Sofridos":('Gols_Visitante_FT','Gols_Mandante_FT'), "Total":('Total_Gols_FT','Total_Gols_FT')})
    st_tabela_estilizada(df_m_last, df_v_last, m_sel, v_sel, "🚩 Cantos", {"Marcados":('Corners_H','Corners_A'), "Sofridos":('Corners_A','Corners_H')})
    st_tabela_estilizada(df_m_last, df_v_last, m_sel, v_sel, "🎯 Chutes", {"No Gol":('ShotsOnTarget_H','ShotsOnTarget_A'), "Total":('Shots_H','Shots_A')})

    # --- 6. CALCULADORA DE INCIDÊNCIA (PRESERVADA) ---
    st.divider()
    st.subheader("💎 Calculadora de Incidência e Odds")
    def calc_inc_full(df_h):
        m = {
            'O 0.5 HT': df_h['Total_Gols_HT']>0.5, 'O 1.5 FT': df_h['Total_Gols_FT']>1.5, 'O 2.5 FT': df_h['Total_Gols_FT']>2.5,
            'BTTS Sim FT': (df_h['Gols_Mandante_FT']>0)&(df_h['Gols_Visitante_FT']>0), 'O 9.5 Cantos FT': df_h['Total_Corners']>9.5
        }
        return pd.DataFrame([{'Mercado': k, 'Freq': f"{v.mean()*100:.1f}%", 'Odd Justa': f"{1/v.mean():.2f}" if v.mean()>0 else 'N/A'} for k, v in m.items()])
    
    ci1, ci2 = st.columns(2)
    ci1.write(f"**{m_sel}**"); ci1.table(calc_inc_full(df_m_last))
    ci2.write(f"**{v_sel}**"); ci2.table(calc_inc_full(df_v_last))

    # --- 7. HISTÓRICO (PRESERVADO) ---
    st.divider()
    st.subheader("📝 Histórico Recente")
    def hist_final(df_h, time):
        df_f = df_h[(df_h['Mandante']==time)|(df_h['Visitante']==time)].sort_values('Data', ascending=False).head(10)
        res = []
        for _, r in df_f.iterrows():
            res.append({'Data': r['Data'], 'Placar': f"{int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])}", 'Cantos': r['Total_Corners'], 'xG': f"{r['xG_Mandante']}-{r['xG_Visitante']}"})
        return pd.DataFrame(res)

    st.write(f"**{m_sel}: Últimos Jogos**"); st.table(hist_final(df_l, m_sel))
    st.write(f"**{v_sel}: Últimos Jogos**"); st.table(hist_final(df_l, v_sel))
