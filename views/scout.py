import streamlit as st
import pandas as pd
import numpy as np
from difflib import get_close_matches

def mostrar_scout(df):
    st.markdown("## 🔎 Painel de Análise Profissional")
    
    # 1. Ajuste das colunas
    df.columns = [c.strip() for c in df.columns]

    # --- LÓGICA DE INDEXAÇÃO AUTOMÁTICA ---
    lista_ligas = sorted(df['Liga'].unique())
    idx_liga = 0
    if 'liga_scout' in st.session_state:
        matches_l = get_close_matches(st.session_state.liga_scout, lista_ligas, n=1, cutoff=0.6)
        if matches_l:
            idx_liga = lista_ligas.index(matches_l[0])

    # 2. SELEÇÃO DA LIGA
    liga_sel = st.selectbox("🏆 Escolha a Liga", lista_ligas, index=idx_liga)
    df_l = df[df['Liga'] == liga_sel].copy()

    # --- TIMES DA LIGA SELECIONADA ---
    lista_times = sorted(df_l['Mandante'].unique())
    
    idx_casa = 0
    if 'time_casa_scout' in st.session_state:
        matches_m = get_close_matches(st.session_state.time_casa_scout, lista_times, n=1, cutoff=0.6)
        if matches_m:
            idx_casa = lista_times.index(matches_m[0])

    # 3. SELEÇÃO DOS TIMES
    m_sel = st.selectbox("🏠 Time da Casa", lista_times, index=idx_casa)
    
    visitantes_disp = [t for t in lista_times if t != m_sel]
    idx_fora = 0
    if 'time_fora_scout' in st.session_state:
        matches_v = get_close_matches(st.session_state.time_fora_scout, visitantes_disp, n=1, cutoff=0.6)
        if matches_v:
            idx_fora = visitantes_disp.index(matches_v[0])

    v_sel = st.selectbox("🚌 Time de Fora", visitantes_disp, index=idx_fora)

    # 4. CONFIGURAÇÃO (Sidebar)
    n_jogos = st.sidebar.slider("Amostragem (Últimos Jogos)", 5, 50, 10)
    
    st.divider()
    st.subheader(f"📊 {m_sel} vs {v_sel}")

    # --- FUNÇÕES DE CÁLCULO (MANTIDAS DO ORIGINAL) ---
    def calcular_posicoes(df_liga):
        stats = {}
        for _, r in df_liga.iterrows():
            m, v = r['Mandante'], r['Visitante']
            gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
            for t in [m, v]:
                if t not in stats: stats[t] = {'P': 0, 'V': 0, 'SG': 0}
            stats[m]['SG'] += (gm - gv); stats[v]['SG'] += (gv - gm)
            if gm > gv: stats[m]['P'] += 3; stats[m]['V'] += 1
            elif gm == gv: stats[m]['P'] += 1; stats[v]['P'] += 1
            else: stats[v]['P'] += 3; stats[v]['V'] += 1
        tab = pd.DataFrame.from_dict(stats, orient='index').reset_index().rename(columns={'index':'Time'})
        tab = tab.sort_values(by=['P', 'V', 'SG'], ascending=False).reset_index(drop=True)
        tab['Pos'] = tab.index + 1
        return tab

    def get_forma(df_hist, time, apenas_mando=False, mando="Casa"):
        if apenas_mando:
            if mando == "Casa":
                df_f = df_hist[df_hist['Mandante'] == time].sort_values('Data', ascending=False).head(5)
            else:
                df_f = df_hist[df_hist['Visitante'] == time].sort_values('Data', ascending=False).head(5)
        else:
            df_f = df_hist[(df_hist['Mandante'] == time) | (df_hist['Visitante'] == time)].sort_values('Data', ascending=False).head(5)
        
        resultados = []
        for _, r in df_f.iterrows():
            if r['Gols_Mandante_FT'] == r['Gols_Visitante_FT']: resultados.append("🟡")
            elif (r['Mandante'] == time and r['Gols_Mandante_FT'] > r['Gols_Visitante_FT']) or \
                 (r['Visitante'] == time and r['Gols_Visitante_FT'] > r['Gols_Mandante_FT']): resultados.append("🟢")
            else: resultados.append("🔴")
        return " ".join(resultados)

    # --- EXECUÇÃO DA TABELA ---
    tabela_liga = calcular_posicoes(df_l)
    try:
        pos_m = tabela_liga[tabela_liga['Time'] == m_sel]['Pos'].values[0]
        pos_v = tabela_liga[tabela_liga['Time'] == v_sel]['Pos'].values[0]
        dif = abs(pos_m - pos_v)

        st.markdown("""
            <style>
            div[data-testid="stMetricValue"] > div { text-align: center !important; color: #000000 !important; font-weight: bold !important; justify-content: center !important; }
            div[data-testid="stMetricLabel"] > div { text-align: center !important; justify-content: center !important; color: #31333F !important; }
            [data-testid="stMetric"] { text-align: center; display: flex; flex-direction: column; align-items: center; }
            [data-testid="stTable"] td, [data-testid="stTable"] th { text-align: center !important; }
            </style>
            """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1: st.metric(label=f"Posição {m_sel}", value=f"{pos_m}º")
        with c2: st.metric(label=f"Posição {v_sel}", value=f"{pos_v}º")
        with c3: st.metric(label="Diferença de Tabela", value=f"{dif} pos.")
    except:
        st.info("Selecione os times.")

    st.divider()
    
    # --- NOVAS MÉTRICAS DE XG E POSSE (DO ARQUIVO TXT) ---
    def get_avg_metric(df_hist, time, col_h, col_a):
        val = pd.concat([df_hist[df_hist['Mandante'] == time][col_h], df_hist[df_hist['Visitante'] == time][col_a]])
        return val.mean()

    df_m_last = df_l[(df_l['Mandante'] == m_sel) | (df_l['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(n_jogos)
    df_v_last = df_l[(df_l['Mandante'] == v_sel) | (df_l['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(n_jogos)

    st.markdown("### 🚀 Expectativa e Pressão")
    cx1, cx2, cx3, cx4 = st.columns(4)
    with cx1: st.metric("xG Médio", f"{get_avg_metric(df_m_last, m_sel, 'xG_Mandante', 'xG_Visitante'):.2f}")
    with cx2: st.metric("Posse Bola %", f"{get_avg_metric(df_m_last, m_sel, 'Possession_H', 'Possession_A'):.1f}%")
    with cx3: st.metric("Ataques Perigosos", f"{get_avg_metric(df_m_last, m_sel, 'DangerousAttacks_H', 'DangerousAttacks_A'):.1f}")
    with cx4: st.metric("Chutes no Gol", f"{get_avg_metric(df_m_last, m_sel, 'ShotsOnTarget_H', 'ShotsOnTarget_A'):.1f}")

    st.divider()
    st.markdown("### 📈 Forma Recente (Últimos 5 Jogos)")
    cf1, cf2 = st.columns(2)
    with cf1:
        st.write(f"**{m_sel}**")
        st.write(f"Geral: {get_forma(df_l, m_sel)}")
        st.write(f"Em Casa: {get_forma(df_l, m_sel, True, 'Casa')}")
    with cf2:
        st.write(f"**{v_sel}**")
        st.write(f"Geral: {get_forma(df_l, v_sel)}")
        st.write(f"Fora: {get_forma(df_l, v_sel, True, 'Fora')}")

    # --- TABELA TÉCNICA COMPLETA ---
    st.divider()
    st.markdown("### 📉 Estatísticas Técnicas (Últimos Jogos)")

    def get_stats_combo(series):
        if series.empty: return [0.0]*5
        series = pd.to_numeric(series, errors='coerce').fillna(0)
        mean = series.mean(); median = series.median()
        mode = series.mode().iloc[0] if not series.mode().empty else 0.0
        std = series.std(); cv = (std / mean) if mean != 0 else 0.0
        return [mean, median, mode, std, cv]

    def preparar_tabela_tecnica(df_hist, time):
        # Mapeamento de colunas dinâmico conforme o TXT
        col_cn_h = 'Corners_H'; col_cn_a = 'Corners_A'
        col_cn_h_ht = 'Corners_H_HT'; col_cn_a_ht = 'Corners_A_HT'
        
        g_pro_ft = pd.concat([df_hist[df_hist['Mandante'] == time]['Gols_Mandante_FT'], df_hist[df_hist['Visitante'] == time]['Gols_Visitante_FT']])
        g_con_ft = pd.concat([df_hist[df_hist['Mandante'] == time]['Gols_Visitante_FT'], df_hist[df_hist['Visitante'] == time]['Gols_Mandante_FT']])
        
        c_pro_ft = pd.concat([df_hist[df_hist['Mandante'] == time].get(col_cn_h, pd.Series(0)), df_hist[df_hist['Visitante'] == time].get(col_cn_a, pd.Series(0))])
        c_con_ft = pd.concat([df_hist[df_hist['Mandante'] == time].get(col_cn_a, pd.Series(0)), df_hist[df_hist['Visitante'] == time].get(col_cn_h, pd.Series(0))])
        
        # Inclusão de novos dados do TXT: Shots e Fouls
        shots = pd.concat([df_hist[df_hist['Mandante'] == time].get('Shots_H', pd.Series(0)), df_hist[df_hist['Visitante'] == time].get('Shots_A', pd.Series(0))])
        fouls = pd.concat([df_hist[df_hist['Mandante'] == time].get('Fouls_H', pd.Series(0)), df_hist[df_hist['Visitante'] == time].get('Fouls_A', pd.Series(0))])

        data = [
            ['Gols Marcados (FT)']+get_stats_combo(g_pro_ft), 
            ['Gols Sofridos (FT)']+get_stats_combo(g_con_ft), 
            ['Cantos FT (Pro)']+get_stats_combo(c_pro_ft), 
            ['Cantos FT (Contra)']+get_stats_combo(c_con_ft),
            ['Finalizações (Total)']+get_stats_combo(shots),
            ['Faltas Cometidas']+get_stats_combo(fouls)
        ]
        return pd.DataFrame(data, columns=['Métrica', 'Média', 'Mediana', 'Moda', 'DP', 'CV'])

    col_t1, col_t2 = st.columns(2)
    with col_t1: 
        st.write(f"📈 **Estatísticas: {m_sel}**")
        st.table(preparar_tabela_tecnica(df_m_last, m_sel).style.format({c: "{:.2f}" for c in ['Média', 'Mediana', 'Moda', 'DP', 'CV']}))
    with col_t2: 
        st.write(f"📈 **Estatísticas: {v_sel}**")
        st.table(preparar_tabela_tecnica(df_v_last, v_sel).style.format({c: "{:.2f}" for c in ['Média', 'Mediana', 'Moda', 'DP', 'CV']}))

    # --- INCIDÊNCIA DE MERCADOS (%) ---
    st.divider()
    st.markdown("### 💰 Incidência de Mercados (%)")
    def calcular_incidencia(df_hist):
        df_hist = df_hist.copy()
        df_hist['Total_HT'] = pd.to_numeric(df_hist['Gols_Mandante_HT'], errors='coerce').fillna(0) + pd.to_numeric(df_hist['Gols_Visitante_HT'], errors='coerce').fillna(0)
        df_hist['Total_FT'] = pd.to_numeric(df_hist['Gols_Mandante_FT'], errors='coerce').fillna(0) + pd.to_numeric(df_hist['Gols_Visitante_FT'], errors='coerce').fillna(0)
        df_hist['BTTS_FT'] = (pd.to_numeric(df_hist['Gols_Mandante_FT']) > 0) & (pd.to_numeric(df_hist['Gols_Visitante_FT']) > 0)
        
        # Novos mercados do TXT
        df_hist['Over05_HT_Check'] = df_hist['Total_HT'] > 0.5
        df_hist['Over25_FT_Check'] = df_hist['Total_FT'] > 2.5

        linhas = [
            {'Mercado': 'Over 0.5 Gols HT', 'Freq (%)': f"{(df_hist['Over05_HT_Check']).mean()*100:.2f}%"},
            {'Mercado': 'Over 1.5 Gols FT', 'Freq (%)': f"{(df_hist['Total_FT'] > 1.5).mean()*100:.2f}%"},
            {'Mercado': 'Over 2.5 Gols FT', 'Freq (%)': f"{(df_hist['Over25_FT_Check']).mean()*100:.2f}%"},
            {'Mercado': 'Ambas Marcam FT', 'Freq (%)': f"{df_hist['BTTS_FT'].mean()*100:.2f}%"}
        ]
        return pd.DataFrame(linhas)

    cm1, cm2 = st.columns(2)
    with cm1: st.table(calcular_incidencia(df_m_last))
    with cm2: st.table(calcular_incidencia(df_v_last))

    # --- DISTRIBUIÇÃO POR MINUTOS ---
    st.divider()
    st.markdown("### ⏰ Distribuição de Gols por Minutos")
    faixas = ['0-15', '16-30', '31-45+', '46-60', '61-75', '76-90+']
    def preparar_minutos(df_hist, time):
        marc, sofr = [], []
        for f in faixas:
            col_m = f'{f}_Mandante'; col_v = f'{f}_Visitante'
            m = 0; s = 0
            if col_m in df_hist.columns and col_v in df_hist.columns:
                m = df_hist[df_hist['Mandante'] == time][col_m].sum() + df_hist[df_hist['Visitante'] == time][col_v].sum()
                s = df_hist[df_hist['Mandante'] == time][col_v].sum() + df_hist[df_hist['Visitante'] == time][col_m].sum()
            marc.append(int(m)); sofr.append(int(s))
        return pd.DataFrame({'Intervalo': faixas, 'Gols Marcados': marc, 'Gols Sofridos': sofr})
    
    def highlight_max(s):
        is_max = s == s.max()
        return ['background-color: #1f77b4; color: white; font-weight: bold' if v and v > 0 else '' for v in is_max]
    
    cmin1, cmin2 = st.columns(2)
    with cmin1: st.table(preparar_minutos(df_m_last, m_sel).style.apply(highlight_max, subset=['Gols Marcados', 'Gols Sofridos']))
    with cmin2: st.table(preparar_minutos(df_v_last, v_sel).style.apply(highlight_max, subset=['Gols Marcados', 'Gols Sofridos']))

    # --- HISTÓRICO COM ODDS (ADICIONADO DO TXT) ---
    st.divider()
    st.markdown("### 📝 Histórico Detalhado e Odds")
    
    def preparar_historico_odds(df_hist, time):
        df_hist = df_hist.copy()
        df_hist['Data'] = pd.to_datetime(df_hist['Data'], errors='coerce')
        df_f = df_hist[(df_hist['Mandante'] == time) | (df_hist['Visitante'] == time)].sort_values('Data', ascending=False).head(10)
        
        jogos = []
        for _, r in df_f.iterrows():
            oponente = r['Visitante'] if r['Mandante'] == time else r['Mandante']
            mando = "Casa" if r['Mandante'] == time else "Fora"
            placar = f"{int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])}"
            
            jogos.append({
                'Data': r['Data'].strftime('%d/%m/%Y') if pd.notnull(r['Data']) else "N/A",
                'Oponente': oponente,
                'Resultado': placar,
                'Odd H HT': r.get('Odd_H_HT', 0),
                'Odd Over 2.5 FT': r.get('Odd_Over25_FT', 0),
                'Odd BTTS Sim': r.get('Odd_BTTS_Sim', 0)
            })
        return pd.DataFrame(jogos)

    clist1, clist2 = st.columns(2)
    with clist1:
        st.write(f"**Últimos Jogos: {m_sel}**")
        st.table(preparar_historico_odds(df_l, m_sel))
    with clist2:
        st.write(f"**Últimos Jogos: {v_sel}**")
        st.table(preparar_historico_odds(df_l, v_sel))
