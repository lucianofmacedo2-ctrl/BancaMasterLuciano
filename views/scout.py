import streamlit as st
import pandas as pd
import numpy as np

def mostrar_scout(df):
    st.markdown("## 🔎 Painel de Análise")
    
    # 1. Ajuste das colunas
    df.columns = [c.strip() for c in df.columns]

    # --- LÓGICA DE INDEXAÇÃO AUTOMÁTICA ---
    lista_ligas = sorted(df['Liga'].unique())
    idx_liga = 0
    if 'liga_scout' in st.session_state:
        if st.session_state.liga_scout in lista_ligas:
            idx_liga = lista_ligas.index(st.session_state.liga_scout)

    # 2. SELEÇÃO DA LIGA
    liga_sel = st.selectbox("🏆 Escolha a Liga", lista_ligas, index=idx_liga)
    df_l = df[df['Liga'] == liga_sel].copy()

    # --- TIMES DA LIGA SELECIONADA ---
    lista_times = sorted(df_l['Mandante'].unique())
    
    idx_casa = 0
    if 'time_casa_scout' in st.session_state and st.session_state.time_casa_scout in lista_times:
        idx_casa = lista_times.index(st.session_state.time_casa_scout)

    # 3. SELEÇÃO DOS TIMES
    m_sel = st.selectbox("🏠 Time da Casa", lista_times, index=idx_casa)
    
    visitantes_disp = [t for t in lista_times if t != m_sel]
    idx_fora = 0
    if 'time_fora_scout' in st.session_state and st.session_state.time_fora_scout in visitantes_disp:
        idx_fora = visitantes_disp.index(st.session_state.time_fora_scout)

    v_sel = st.selectbox("🚌 Time de Fora", visitantes_disp, index=idx_fora)

    # 4. CONFIGURAÇÃO (Sidebar)
    n_jogos = st.sidebar.slider("Amostragem (Últimos Jogos)", 5, 50, 10)
    
    st.divider()
    st.subheader(f"📊 {m_sel} vs {v_sel}")

    # --- FUNÇÕES INTERNAS ---
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

    st.divider()
    st.markdown("### 📉 Estatísticas Técnicas (Últimos Jogos)")
    
    df_m_last = df_l[(df_l['Mandante'] == m_sel) | (df_l['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(n_jogos)
    df_v_last = df_l[(df_l['Mandante'] == v_sel) | (df_l['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(n_jogos)

    def get_stats_combo(series):
        if series.empty: return [0.0]*5
        series = pd.to_numeric(series, errors='coerce').fillna(0)
        mean = series.mean(); median = series.median()
        mode = series.mode().iloc[0] if not series.mode().empty else 0.0
        std = series.std(); cv = (std / mean) if mean != 0 else 0.0
        return [mean, median, mode, std, cv]

    def preparar_tabela_tecnica(df_hist, time):
        # NOMES EXATOS DAS COLUNAS CONFORME SEU BANCO
        col_cn_h = 'Corners_H' if 'Corners_H' in df_hist.columns else 'Cantos_Mandante'
        col_cn_a = 'Corners_A' if 'Corners_A' in df_hist.columns else 'Cantos_Visitante'
        
        col_yc_h = 'Yellow_Cards_H'
        col_yc_a = 'Yellow_Cards_A'
        col_rc_h = 'Red_Cards_H'
        col_rc_a = 'Red_Cards_A'
        col_tc_h = 'Total_Cards_H'
        col_tc_a = 'Total_Cards_A'

        g_pro_ft = pd.concat([df_hist[df_hist['Mandante'] == time]['Gols_Mandante_FT'], df_hist[df_hist['Visitante'] == time]['Gols_Visitante_FT']])
        g_con_ft = pd.concat([df_hist[df_hist['Mandante'] == time]['Gols_Visitante_FT'], df_hist[df_hist['Visitante'] == time]['Gols_Mandante_FT']])
        
        c_pro_ft = pd.concat([df_hist[df_hist['Mandante'] == time].get(col_cn_h, pd.Series(0)), df_hist[df_hist['Visitante'] == time].get(col_cn_a, pd.Series(0))])
        c_con_ft = pd.concat([df_hist[df_hist['Mandante'] == time].get(col_cn_a, pd.Series(0)), df_hist[df_hist['Visitante'] == time].get(col_cn_h, pd.Series(0))])

        # Cartões Cometidos (Pro) e Causados (Contra)
        y_cometidos = pd.concat([df_hist[df_hist['Mandante'] == time].get(col_yc_h, pd.Series(0)), df_hist[df_hist['Visitante'] == time].get(col_yc_a, pd.Series(0))])
        y_causados = pd.concat([df_hist[df_hist['Mandante'] == time].get(col_yc_a, pd.Series(0)), df_hist[df_hist['Visitante'] == time].get(col_yc_h, pd.Series(0))])
        
        r_cometidos = pd.concat([df_hist[df_hist['Mandante'] == time].get(col_rc_h, pd.Series(0)), df_hist[df_hist['Visitante'] == time].get(col_rc_a, pd.Series(0))])
        r_causados = pd.concat([df_hist[df_hist['Mandante'] == time].get(col_rc_a, pd.Series(0)), df_hist[df_hist['Visitante'] == time].get(col_rc_h, pd.Series(0))])

        t_cometidos = pd.concat([df_hist[df_hist['Mandante'] == time].get(col_tc_h, pd.Series(0)), df_hist[df_hist['Visitante'] == time].get(col_tc_a, pd.Series(0))])
        t_causados = pd.concat([df_hist[df_hist['Mandante'] == time].get(col_tc_a, pd.Series(0)), df_hist[df_hist['Visitante'] == time].get(col_tc_h, pd.Series(0))])

        data = [
            ['Gols Marcados (FT)']+get_stats_combo(g_pro_ft), 
            ['Gols Sofridos (FT)']+get_stats_combo(g_con_ft), 
            ['Cantos FT (Pro)']+get_stats_combo(c_pro_ft), 
            ['Cantos FT (Contra)']+get_stats_combo(c_con_ft),
            ['Amarelos (Cometidos)']+get_stats_combo(y_cometidos),
            ['Amarelos (Causados)']+get_stats_combo(y_causados),
            ['Vermelhos (Cometidos)']+get_stats_combo(r_cometidos),
            ['Vermelhos (Causados)']+get_stats_combo(r_causados),
            ['Total Cartões (Cometidos)']+get_stats_combo(t_cometidos),
            ['Total Cartões (Causados)']+get_stats_combo(t_causados)
        ]
        return pd.DataFrame(data, columns=['Métrica', 'Média', 'Mediana', 'Moda', 'DP', 'CV'])

    col_t1, col_t2 = st.columns(2)
    with col_t1: 
        st.write(f"📈 **Estatísticas: {m_sel}**")
        st.table(preparar_tabela_tecnica(df_m_last, m_sel).style.format({c: "{:.2f}" for c in ['Média', 'Mediana', 'Moda', 'DP', 'CV']}))
    with col_t2: 
        st.write(f"📈 **Estatísticas: {v_sel}**")
        st.table(preparar_tabela_tecnica(df_v_last, v_sel).style.format({c: "{:.2f}" for c in ['Média', 'Mediana', 'Moda', 'DP', 'CV']}))

    st.divider()
    st.markdown("### 💰 Incidência de Mercados (%)")
    def calcular_incidencia(df_hist):
        df_hist = df_hist.copy()
        df_hist['Total_FT'] = pd.to_numeric(df_hist['Gols_Mandante_FT'], errors='coerce') + pd.to_numeric(df_hist['Gols_Visitante_FT'], errors='coerce')
        df_hist['BTTS_FT'] = (pd.to_numeric(df_hist['Gols_Mandante_FT']) > 0) & (pd.to_numeric(df_hist['Gols_Visitante_FT']) > 0)
        
        # SOMA TOTAL DE CARTÕES NO JOGO
        df_hist['Soma_Cartoes'] = pd.to_numeric(df_hist['Total_Cards_H'], errors='coerce').fillna(0) + pd.to_numeric(df_hist['Total_Cards_A'], errors='coerce').fillna(0)

        linhas = [
            {'Mercado': 'Over 1.5 Gols', 'Freq (%)': f"{(df_hist['Total_FT'] > 1.5).mean()*100:.2f}%"},
            {'Mercado': 'Over 2.5 Gols', 'Freq (%)': f"{(df_hist['Total_FT'] > 2.5).mean()*100:.2f}%"},
            {'Mercado': 'Ambas Marcam', 'Freq (%)': f"{df_hist['BTTS_FT'].mean()*100:.2f}%"},
            {'Mercado': 'Over 3.5 Cartões', 'Freq (%)': f"{(df_hist['Soma_Cartoes'] > 3.5).mean()*100:.2f}%"},
            {'Mercado': 'Over 4.5 Cartões', 'Freq (%)': f"{(df_hist['Soma_Cartoes'] > 4.5).mean()*100:.2f}%"},
            {'Mercado': 'Over 5.5 Cartões', 'Freq (%)': f"{(df_hist['Soma_Cartoes'] > 5.5).mean()*100:.2f}%"}
        ]
        return pd.DataFrame(linhas)

    cm1, cm2 = st.columns(2)
    with cm1: st.table(calcular_incidencia(df_m_last))
    with cm2: st.table(calcular_incidencia(df_v_last))

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

    st.divider()
    st.markdown("### 📝 Histórico Detalhado (Últimos 10 Jogos)")
    
    def preparar_historico_lista(df_hist, time):
        df_hist = df_hist.copy()
        df_hist['Data'] = pd.to_datetime(df_hist['Data'], errors='coerce')
        df_f = df_hist[(df_hist['Mandante'] == time) | (df_hist['Visitante'] == time)].sort_values('Data', ascending=False).head(10)
        
        jogos = []
        for _, r in df_f.iterrows():
            oponente = r['Visitante'] if r['Mandante'] == time else r['Mandante']
            mando = "Casa" if r['Mandante'] == time else "Fora"
            try:
                placar = f"{int(r['Gols_Mandante_FT'])} x {int(r['Gols_Visitante_FT'])}"
                cartoes = f"{int(pd.to_numeric(r['Total_Cards_H'], errors='coerce')) + int(pd.to_numeric(r['Total_Cards_A'], errors='coerce'))}"
            except:
                placar = "N/A"
                cartoes = "N/A"
            dt_str = r['Data'].strftime('%d/%m/%Y') if pd.notnull(r['Data']) else "N/A"
            jogos.append({'Data': dt_str, 'Mando': mando, 'Oponente': oponente, 'Placar': placar, 'Cartões T.': cartoes})
        return pd.DataFrame(jogos)

    clist1, clist2 = st.columns(2)
    with clist1:
        st.write(f"**Jogos de {m_sel}**")
        st.table(preparar_historico_lista(df_l, m_sel))
    with clist2:
        st.write(f"**Jogos de {v_sel}**")
        st.table(preparar_historico_lista(df_l, v_sel))
