import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from difflib import get_close_matches
from datetime import datetime

def mostrar_scout(df):
    st.markdown("## 🔎 Painel de Análise Profissional Ultra V7 - Full Intelligence")
    
    # 1. Ajuste e Limpeza de Colunas
    df.columns = [c.strip() for c in df.columns]
    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')

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
    n_jogos = st.sidebar.slider("Amostragem Base (Últimos Jogos)", 5, 50, 10)

    # --- FUNÇÕES DE APOIO ORIGINAIS REINTEGRADAS ---
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
        return max(coef, 0)

    # --- LÓGICA DE CLUSTER ---
    st.sidebar.subheader("🎯 Filtro de Cluster")
    use_cluster = st.sidebar.checkbox("Simular por Nível de Adversário")
    tab_geral = calcular_tabela(df_temp)
    
    def filtrar_cluster(df_input, time_alvo, adversario, tabela):
        if not use_cluster: return df_input
        if adversario not in tabela['Time'].values: return df_input
        pos_adv = tabela[tabela['Time'] == adversario]['Pos'].iloc[0]
        if pos_adv <= 6: cluster_aliados = tabela.head(8)['Time'].tolist()
        elif pos_adv >= len(tabela) - 5: cluster_aliados = tabela.tail(8)['Time'].tolist()
        else: cluster_aliados = tabela.iloc[pos_adv-4:pos_adv+4]['Time'].tolist()
        return df_input[(df_input['Mandante'].isin(cluster_aliados)) | (df_input['Visitante'].isin(cluster_aliados))]

    # DFs para Lógica de Cluster (Base Geral)
    df_m_cluster = filtrar_cluster(df_l[(df_l['Mandante']==m_sel)|(df_l['Visitante']==m_sel)], m_sel, v_sel, tab_geral).sort_values('Data', ascending=False).head(n_jogos)
    df_v_cluster = filtrar_cluster(df_l[(df_l['Mandante']==v_sel)|(df_l['Visitante']==v_sel)], v_sel, m_sel, tab_geral).sort_values('Data', ascending=False).head(n_jogos)

    # DFs para Mando Específico (Casa/Fora) conforme solicitado
    df_m_home = df_l[df_l['Mandante'] == m_sel].sort_values('Data', ascending=False).head(n_jogos)
    df_v_away = df_l[df_l['Visitante'] == v_sel].sort_values('Data', ascending=False).head(n_jogos)

    def calc_resiliencia(df_h, time):
        jogos_atras = 0; recuperados = 0
        for _, r in df_h.iterrows():
            sou_m = r['Mandante'] == time
            g_adv_ht = r['Gols_Visitante_HT'] if sou_m else r['Gols_Mandante_HT']
            g_meu_ft = r['Gols_Mandante_FT'] if sou_m else r['Gols_Visitante_FT']
            g_adv_ft = r['Gols_Visitante_FT'] if sou_m else r['Gols_Mandante_FT']
            if g_adv_ht > 0:
                jogos_atras += 1
                if g_meu_ft >= g_adv_ft: recuperados += 1
        return (recuperados / jogos_atras * 100) if jogos_atras > 0 else 0

    def calc_cansaco(df_h, time):
        if df_h.empty: return 7
        ult_jogo = df_h.sort_values('Data', ascending=False)['Data'].iloc[0]
        return (datetime.now() - ult_jogo).days

    # --- INTERFACE VISUAL INICIAL ---
    st.divider()
    t_casa = calcular_tabela(df_temp, 'Casa')
    t_fora = calcular_tabela(df_temp, 'Fora')

    cf_m = calcular_coeficiente(m_sel, df_temp, 'Mandante')
    cf_v = calcular_coeficiente(v_sel, df_temp, 'Visitante')
    total_f = cf_m + cf_v
    oj_m = 1/((cf_m / total_f) * 0.85) if total_f > 0 else 2.0
    oj_v = 1/((cf_v / total_f) * 0.85) if total_f > 0 else 2.0
    odd_atual_m = df_temp[df_temp['Mandante']==m_sel]['Odd_Mandante_FT'].iloc[0] if 'Odd_Mandante_FT' in df_temp.columns else 0

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### 🏠 {m_sel}")
        st.info(f"**Índice de Força: {cf_m:.2f}** | **Odd Justa: {oj_m:.2f}**")
        if odd_atual_m > oj_m: st.success(f"💎 VALOR: {odd_atual_m:.2f}")
        st.write(f"💪 **Resiliência:** {calc_resiliencia(df_m_cluster, m_sel):.0f}% | 🔋 **Descanso:** {calc_cansaco(df_m_cluster, m_sel)} dias")
        cc1, cc2 = st.columns(2)
        cc1.metric("Pos. Geral", f"{tab_geral[tab_geral['Time']==m_sel]['Pos'].iloc[0]}º")
        cc2.metric("Pos. Casa", f"{t_casa[t_casa['Time']==m_sel]['Pos'].iloc[0] if m_sel in t_casa['Time'].values else '?'}º")
        st.write(f"**Forma:** {get_forma_lista(df_temp, m_sel)}")

    with c2:
        st.markdown(f"### 🚌 {v_sel}")
        st.error(f"**Índice de Força: {cf_v:.2f}** | **Odd Justa: {oj_v:.2f}**")
        st.write(f"💪 **Resiliência:** {calc_resiliencia(df_v_cluster, v_sel):.0f}% | 🔋 **Descanso:** {calc_cansaco(df_v_cluster, v_sel)} dias")
        cv1, cv2 = st.columns(2)
        cv1.metric("Pos. Geral", f"{tab_geral[tab_geral['Time']==v_sel]['Pos'].iloc[0]}º")
        cv2.metric("Pos. Fora", f"{t_fora[t_fora['Time']==v_sel]['Pos'].iloc[0] if v_sel in t_fora['Time'].values else '?'}º")
        st.write(f"**Forma:** {get_forma_lista(df_temp, v_sel)}")

    # --- 1. INTELIGÊNCIA QUANTITATIVA (xG E PRESSÃO) - ATUALIZADO MANDO ---
    st.divider()
    st.subheader("🚀 Inteligência Quantitativa (Mando Específico)")
    
    def stats_profissa_mando(df_h, is_home):
        p = 'H' if is_home else 'A'
        atq = df_h[f'DangerousAttacks_{p}'].mean()
        chutes = df_h[f'Shots_{p}'].mean()
        xg = df_h['xG_Mandante' if is_home else 'xG_Visitante'].mean()
        gols = df_h['Gols_Mandante_FT' if is_home else 'Gols_Visitante_FT'].mean()
        gs = df_h['Gols_Visitante_FT' if is_home else 'Gols_Mandante_FT']
        cs = (gs == 0).mean() * 100
        return (atq*0.5 + chutes*0.5), xg, gols, cs

    im1, xg1, g1, cs1 = stats_profissa_mando(df_m_home, True)
    im2, xg2, g2, cs2 = stats_profissa_mando(df_v_away, False)

    col_q1, col_q2 = st.columns(2)
    with col_q1:
        st.write(f"**{m_sel} (Casa)**")
        st.metric("Índice Massacre", f"{im1:.1f}")
        st.metric("Diferença xG", f"{g1-xg1:.2f}")
        st.metric("Clean Sheet %", f"{cs1:.0f}%")
    with col_q2:
        st.write(f"**{v_sel} (Fora)**")
        st.metric("Índice Massacre", f"{im2:.1f}")
        st.metric("Diferença xG", f"{g2-xg2:.2f}")
        st.metric("Clean Sheet %", f"{cs2:.0f}%")

    # --- 2. SLOTS DE TEMPO ---
    st.subheader("⏰ Slots de Tempo (Gols Marcados)")
    def get_slot_stats_mando(df_h, is_home):
        p = 'Mandante' if is_home else 'Visitante'
        i = df_h[f'0-15_{p}'].mean()
        f = df_h[f'76-90+_{p}'].mean()
        return i, f
    im_i, im_f = get_slot_stats_mando(df_m_home, True)
    iv_i, iv_f = get_slot_stats_mando(df_v_away, False)
    st.write(f"**Início (0-15'):** {m_sel} ({im_i:.2f}) vs {v_sel} ({iv_i:.2f}) | **Final (76-90'):** {m_sel} ({im_f:.2f}) vs {v_sel} ({iv_f:.2f})")

    # --- 3. CHECKLIST DE PREVISIBILIDADE ---
    st.divider()
    def check_previsibilidade_detalhado(df_h, time, is_home):
        p_m = 'Mandante' if is_home else 'Visitante'
        p_s = 'Visitante' if is_home else 'Mandante'
        metricas = {
            "Gols Marcados": f'Gols_{p_m}_FT',
            "Gols Sofridos": f'Gols_{p_s}_FT',
            "Cantos": 'Total_Corners'
        }
        estaveis = []
        for nome, col in metricas.items():
            d = pd.to_numeric(df_h[col], errors='coerce').fillna(0)
            if d.mean() > 0 and (d.std()/d.mean()) < 0.75: estaveis.append(nome)
        if estaveis: st.success(f"✅ {time} previsível em: {', '.join(estaveis)}")
        else: st.warning(f"⚠️ {time} instável neste mando.")

    check_previsibilidade_detalhado(df_m_home, m_sel, True)
    check_previsibilidade_detalhado(df_v_away, v_sel, False)

    # --- 4. RADAR E ÁREA ---
    def criar_radar(t1, t2, df_h1, df_h2):
        metrics = ['Gols Marc.', 'Cantos Marc.', 'Posse', 'Ataque Per.', 'Chutes']
        def v(df_h, is_home):
            p = 'H' if is_home else 'A'
            g = 'Gols_Mandante_FT' if is_home else 'Gols_Visitante_FT'
            c = 'Corners_H' if is_home else 'Corners_A'
            return [df_h[g].mean()*25, df_h[c].mean()*12, df_h[f'Possession_{p}'].mean(), 
                    df_h[f'DangerousAttacks_{p}'].mean(), df_h[f'Shots_{p}'].mean()*6]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=v(df_h1, True), theta=metrics, fill='toself', name=t1))
        fig.add_trace(go.Scatterpolar(r=v(df_h2, False), theta=metrics, fill='toself', name=t2))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

    criar_radar(m_sel, v_sel, df_m_home, df_v_away)

    labels_tempo = ["0-15'", "16-30'", "31-45'", "46-60'", "61-75'", "76-90'"]
    def get_f(df_h, is_home):
        p = 'Mandante' if is_home else 'Visitante'
        cols = [f"0-15_{p}", f"16-30_{p}", f"31-45+_{p}", f"46-60_{p}", f"61-75_{p}", f"76-90+_{p}"]
        return [df_h[c].mean() for c in cols]
    
    fig_area = go.Figure()
    fig_area.add_trace(go.Scatter(x=labels_tempo, y=get_f(df_m_home, True), fill='tozeroy', name=f"{m_sel} (Gols)"))
    fig_area.add_trace(go.Scatter(x=labels_tempo, y=get_f(df_v_away, False), fill='tozeroy', name=f"{v_sel} (Gols)"))
    st.plotly_chart(fig_area, use_container_width=True)

    # --- 5. TABELAS DETALHADAS (MÉDIA, MEDIANA, MODA, DP, CV) ---
    st.divider()
    st.subheader("📉 Performance Detalhada (Mando Específico)")

    def color_stats(val):
        try:
            v = float(val)
            return 'background-color: #d4edda; color: #155724' if 0 < v < 0.8 else ''
        except: return ''

    def render_tabela_completa(titulo, dict_cols):
        st.markdown(f"#### {titulo}")
        def proc(df_h, cols):
            res = []
            for col in cols:
                s = pd.to_numeric(df_h[col], errors='coerce').fillna(0)
                m = s.mean(); med = s.median(); std = s.std(); cv = std/m if m!=0 else 0
                try: moda = s.mode()[0]
                except: moda = 0
                res.append([m, med, moda, std, cv])
            return res
        
        c_m = [v[0] for v in dict_cols.values()]
        c_v = [v[1] for v in dict_cols.values()]
        
        res1 = pd.DataFrame(proc(df_m_home, c_m), index=dict_cols.keys(), columns=['Média', 'Mediana', 'Moda', 'DP', 'CV'])
        res2 = pd.DataFrame(proc(df_v_away, c_v), index=dict_cols.keys(), columns=['Média', 'Mediana', 'Moda', 'DP', 'CV'])
        
        ca, cb = st.columns(2)
        ca.write(f"**{m_sel} (Casa)**"); ca.table(res1.style.format("{:.2f}").applymap(color_stats, subset=['DP', 'CV']))
        cb.write(f"**{v_sel} (Fora)**"); cb.table(res2.style.format("{:.2f}").applymap(color_stats, subset=['DP', 'CV']))

    render_tabela_completa("⚽ Gols FT", {
        "Marcados": ('Gols_Mandante_FT', 'Gols_Visitante_FT'),
        "Sofridos": ('Gols_Visitante_FT', 'Gols_Mandante_FT'),
        "TOTAL": ('Total_Gols_FT', 'Total_Gols_FT')
    })
    render_tabela_completa("⏱️ Gols HT", {
        "Marcados": ('Gols_Mandante_HT', 'Gols_Visitante_HT'),
        "Sofridos": ('Gols_Visitante_HT', 'Gols_Mandante_HT'),
        "TOTAL": ('Total_Gols_HT', 'Total_Gols_HT')
    })
    render_tabela_completa("🚩 Cantos FT", {
        "Marcados": ('Corners_H', 'Corners_A'),
        "Sofridos": ('Corners_A', 'Corners_H'),
        "TOTAL": ('Total_Corners', 'Total_Corners')
    })
    render_tabela_completa("🚩 Cantos HT", {
        "Marcados": ('Corners_HT_H', 'Corners_HT_A'),
        "Sofridos": ('Corners_HT_A', 'Corners_HT_H'),
        "TOTAL": ('Total_Corners_HT', 'Total_Corners_HT')
    })
    render_tabela_completa("🎯 Chutes FT", {
        "Feitos": ('Shots_H', 'Shots_A'),
        "Concedidos": ('Shots_A', 'Shots_H'),
        "TOTAL": ('Shots_H', 'Shots_A') # Ou coluna Total se houver
    })
    render_tabela_completa("🟨 Cartões", {
        "Causados (Adv)": ('Yellow_Cards_A', 'Yellow_Cards_H'),
        "Recebidos": ('Yellow_Cards_H', 'Yellow_Cards_A'),
        "TOTAL": ('Total_Cards_H', 'Total_Cards_A')
    })

    # --- 6. INCIDÊNCIA DE MERCADOS ---
    st.divider()
    def calc_inc(df_h):
        m = {
            'O 0.5 HT': df_h['Total_Gols_HT']>0.5, 
            'O 1.5 FT': df_h['Total_Gols_FT']>1.5, 
            'O 2.5 FT': df_h['Total_Gols_FT']>2.5,
            'BTTS': (df_h['Gols_Mandante_FT']>0)&(df_h['Gols_Visitante_FT']>0), 
            '4.5 Cantos HT': df_h['Total_Corners_HT']>4.5,
            '9.5 Cantos FT': df_h['Total_Corners']>9.5
        }
        return pd.DataFrame([{'Mercado': k, 'Freq': f"{v.mean()*100:.1f}%", 'Odd': f"{1/v.mean():.2f}" if v.mean()>0 else 'N/A'} for k, v in m.items()])
    
    ci1, ci2 = st.columns(2)
    ci1.write(f"**{m_sel} (Casa)**"); ci1.table(calc_inc(df_m_home))
    ci2.write(f"**{v_sel} (Fora)**"); ci2.table(calc_inc(df_v_away))

    # --- 7. ÚLTIMOS CONFRONTOS (MANDO ESPECÍFICO) ---
    def hist_detalhado(df_h):
        res = []
        for _, r in df_h.iterrows():
            res.append({
                'Data': r['Data'].strftime('%d/%m/%Y') if pd.notnull(r['Data']) else 'N/A',
                'Placar FT': f"{int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])}",
                'Placar HT': f"{int(r['Gols_Mandante_HT'])}x{int(r['Gols_Visitante_HT'])}",
                'Cantos HT': f"{int(r['Total_Corners_HT'])}",
                'Cantos FT': f"{int(r['Total_Corners'])}",
                'Odd M': r.get('Odd_Mandante_FT', 0),
                'Odd V': r.get('Odd_Visitante_FT', 0)
            })
        return pd.DataFrame(res)

    st.write(f"**{m_sel}: Últimos em Casa**"); st.table(hist_detalhado(df_m_home))
    st.write(f"**{v_sel}: Últimos Fora**"); st.table(hist_detalhado(df_v_away))
