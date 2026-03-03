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

    # --- NOVAS LÓGICAS PREDITIVAS ---
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

    df_m_cluster = filtrar_cluster(df_l[(df_l['Mandante']==m_sel)|(df_l['Visitante']==m_sel)], m_sel, v_sel, tab_geral).sort_values('Data', ascending=False).head(n_jogos)
    df_v_cluster = filtrar_cluster(df_l[(df_l['Mandante']==v_sel)|(df_l['Visitante']==v_sel)], v_sel, m_sel, tab_geral).sort_values('Data', ascending=False).head(n_jogos)

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

    # --- INTERFACE VISUAL ---
    st.divider()
    t_casa = calcular_tabela(df_temp, 'Casa')
    t_fora = calcular_tabela(df_temp, 'Fora')

    # --- 1. CARDS DE FORÇA E VALOR ---
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

    # --- 2. ÍNDICE DE MASSACRE E XG ---
    st.divider()
    st.subheader("🚀 Inteligência Quantitativa (xG e Pressão)")
    
    def stats_profissa(time, df_h):
        atq = extrair_metrica(df_h, time, 'DangerousAttacks_H', 'DangerousAttacks_A').mean()
        chutes = extrair_metrica(df_h, time, 'Shots_H', 'Shots_A').mean()
        xg = extrair_metrica(df_h, time, 'xG_Mandante', 'xG_Visitante').mean()
        gols = extrair_metrica(df_h, time, 'Gols_Mandante_FT', 'Gols_Visitante_FT').mean()
        cs = (extrair_metrica(df_h, time, 'Gols_Visitante_FT', 'Gols_Mandante_FT') == 0).mean() * 100
        return (atq*0.5 + chutes*0.5), xg, gols, cs

    im1, xg1, g1, cs1 = stats_profissa(m_sel, df_m_cluster)
    im2, xg2, g2, cs2 = stats_profissa(v_sel, df_v_cluster)

    col_a, col_b, col_c = st.columns(3)
    col_a.metric("Índice Massacre", f"{im1:.1f}", f"{im1-im2:.1f}")
    col_b.metric("Diferença xG", f"{g1-xg1:.2f}", delta_color="inverse")
    col_c.metric("Clean Sheet %", f"{cs1:.0f}%")

    # --- 3. SLOTS DE TEMPO ---
    st.subheader("⏰ Slots de Tempo (Gols Marcados)")
    def get_slot_stats(time, df_h):
        i = extrair_metrica(df_h, time, '0-15_Mandante', '0-15_Visitante').mean()
        f = extrair_metrica(df_h, time, '76-90+_Mandante', '76-90+_Visitante').mean()
        return i, f
    im_i, im_f = get_slot_stats(m_sel, df_m_cluster)
    iv_i, iv_f = get_slot_stats(v_sel, df_v_cluster)
    st.write(f"**Início (0-15'):** {m_sel} ({im_i:.2f}) vs {v_sel} ({iv_i:.2f}) | **Final (76-90'):** {m_sel} ({im_f:.2f}) vs {v_sel} ({iv_f:.2f})")

    # --- 4. CHECKLIST E RADAR ---
    st.divider()
    def check_detalhado(time, df_h):
        metricas = {"Gols": ('Gols_Mandante_FT', 'Gols_Visitante_FT'), "Cantos": ('Corners_H', 'Corners_A')}
        estaveis = []
        for nome, cols in metricas.items():
            d = extrair_metrica(df_h, time, cols[0], cols[1])
            if d.mean() > 0 and (d.std()/d.mean()) < 0.8: estaveis.append(nome)
        if estaveis: st.success(f"✅ {time} estável em: {', '.join(estaveis)}")

    check_detalhado(m_sel, df_m_cluster)
    check_detalhado(v_sel, df_v_cluster)

    def criar_radar(t1, t2, df_h1, df_h2):
        metrics = ['Gols', 'Cantos', 'Posse', 'Ataque', 'Chutes']
        def v(time, df_h):
            return [extrair_metrica(df_h, time, 'Total_Gols_FT', 'Total_Gols_FT').mean()*20,
                    extrair_metrica(df_h, time, 'Corners_H', 'Corners_A').mean()*10,
                    extrair_metrica(df_h, time, 'Possession_H', 'Possession_A').mean(),
                    extrair_metrica(df_h, time, 'DangerousAttacks_H', 'DangerousAttacks_A').mean(),
                    extrair_metrica(df_h, time, 'Shots_H', 'Shots_A').mean()*5]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=v(t1, df_h1), theta=metrics, fill='toself', name=t1))
        fig.add_trace(go.Scatterpolar(r=v(t2, df_h2), theta=metrics, fill='toself', name=t2))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
        st.plotly_chart(fig, use_container_width=True)

    criar_radar(m_sel, v_sel, df_m_cluster, df_v_cluster)

    # Gráfico de Área (Faixas de Tempo)
    labels_tempo = ["0-15'", "16-30'", "31-45'", "46-60'", "61-75'", "76-90'"]
    cols_m = ['0-15_Mandante', '16-30_Mandante', '31-45+_Mandante', '46-60_Mandante', '61-75_Mandante', '76-90+_Mandante']
    cols_v = ['0-15_Visitante', '16-30_Visitante', '31-45+_Visitante', '46-60_Visitante', '61-75_Visitante', '76-90+_Visitante']
    f_m = [extrair_metrica(df_m_cluster, m_sel, cm, cv).mean() for cm, cv in zip(cols_m, cols_v)]
    f_v = [extrair_metrica(df_v_cluster, v_sel, cm, cv).mean() for cm, cv in zip(cols_m, cols_v)]
    fig_area = go.Figure()
    fig_area.add_trace(go.Scatter(x=labels_tempo, y=f_m, fill='tozeroy', name=m_sel))
    fig_area.add_trace(go.Scatter(x=labels_tempo, y=f_v, fill='tozeroy', name=v_sel))
    st.plotly_chart(fig_area, use_container_width=True)

    # --- 5. TABELAS DETALHADAS (COM CORES E TOTAIS) ---
    st.divider()
    st.subheader("📉 Performance Detalhada (Média, DP e CV)")

    def color_stats(val):
        try:
            v = float(val)
            return 'background-color: #d4edda; color: #155724' if v < 0.8 and v > 0 else ''
        except: return ''

    def render_tabela_completa(df_m, df_v, t1, t2, titulo, dict_m):
        st.markdown(f"#### {titulo}")
        def proc(df_h, time, cols):
            s = extrair_metrica(df_h, time, cols[0], cols[1])
            m = s.mean(); std = s.std(); cv = std/m if m!=0 else 0
            return [m, s.median(), std, cv]
        res1 = pd.DataFrame([proc(df_m, t1, v) for v in dict_m.values()], index=dict_m.keys(), columns=['Média', 'Mediana', 'DP', 'CV'])
        res2 = pd.DataFrame([proc(df_v, t2, v) for v in dict_m.values()], index=dict_m.keys(), columns=['Média', 'Mediana', 'DP', 'CV'])
        ca, cb = st.columns(2)
        ca.write(f"**{t1}**"); ca.table(res1.style.format("{:.2f}").applymap(color_stats, subset=['DP', 'CV']))
        cb.write(f"**{t2}**"); cb.table(res2.style.format("{:.2f}").applymap(color_stats, subset=['DP', 'CV']))

    render_tabela_completa(df_m_cluster, df_v_cluster, m_sel, v_sel, "⚽ Gols FT", {
        "Marcados": ('Gols_Mandante_FT', 'Gols_Visitante_FT'),
        "Sofridos": ('Gols_Visitante_FT', 'Gols_Mandante_FT'),
        "TOTAL": ('Total_Gols_FT', 'Total_Gols_FT')
    })

    render_tabela_completa(df_m_cluster, df_v_cluster, m_sel, v_sel, "🚩 Cantos", {
        "Marcados": ('Corners_H', 'Corners_A'),
        "Sofridos": ('Corners_A', 'Corners_H'),
        "TOTAL": ('Total_Corners', 'Total_Corners')
    })

    render_tabela_completa(df_m_cluster, df_v_cluster, m_sel, v_sel, "🎯 Chutes", {
        "No Gol": ('ShotsOnTarget_H', 'ShotsOnTarget_A'),
        "Fora": ('ShotsOffTarget_H', 'ShotsOffTarget_A'),
        "TOTAL": ('Shots_H', 'Shots_A')
    })

    render_tabela_completa(df_m_cluster, df_v_cluster, m_sel, v_sel, "⚖️ Disciplina", {
        "Faltas Cometidas": ('Fouls_H', 'Fouls_A'),
        "Faltas Sofridas": ('Freekicks_H', 'Freekicks_A'),
        "Amarelos": ('Yellow_Cards_H', 'Yellow_Cards_A'),
        "TOTAL Cartões": ('Total_Cards_H', 'Total_Cards_A')
    })

    # --- 6. INCIDÊNCIA E HISTÓRICO ---
    st.divider()
    def calc_inc(df_h):
        m = {'O 0.5 HT': df_h['Total_Gols_HT']>0.5, 'O 1.5 FT': df_h['Total_Gols_FT']>1.5, 'BTTS': (df_h['Gols_Mandante_FT']>0)&(df_h['Gols_Visitante_FT']>0), 'O 8.5 Cantos': df_h['Total_Corners']>8.5}
        return pd.DataFrame([{'Mercado': k, 'Freq': f"{v.mean()*100:.1f}%", 'Odd': f"{1/v.mean():.2f}" if v.mean()>0 else 'N/A'} for k, v in m.items()])
    
    ci1, ci2 = st.columns(2)
    ci1.table(calc_inc(df_m_cluster)); ci2.table(calc_inc(df_v_cluster))

    def hist(df_h, time):
        df_f = df_h[(df_h['Mandante']==time)|(df_h['Visitante']==time)].sort_values('Data', ascending=False).head(8)
        return pd.DataFrame([{'Data': r['Data'], 'Placar': f"{int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])}", 'xG': f"{r['xG_Mandante']}-{r['xG_Visitante']}"} for _, r in df_f.iterrows()])
    
    st.write(f"**{m_sel}: Últimos**"); st.table(hist(df_l, m_sel))
    st.write(f"**{v_sel}: Últimos**"); st.table(hist(df_l, v_sel))
