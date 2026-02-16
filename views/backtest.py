import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from difflib import get_close_matches

def mostrar_scout(df):
    st.markdown("## 🔎 Painel de Análise Profissional Ultra")
    
    # 1. Ajuste e Limpeza de Colunas 
    df.columns = [c.strip() for c in df.columns]

    # --- LÓGICA DE INDEXAÇÃO AUTOMÁTICA ---
    lista_ligas = sorted(df['Liga'].unique()) [cite: 1, 5]
    idx_liga = 0
    if 'liga_scout' in st.session_state:
        matches_l = get_close_matches(st.session_state.liga_scout, lista_ligas, n=1, cutoff=0.6)
        if matches_l:
            idx_liga = lista_ligas.index(matches_l[0])

    # 2. SELEÇÃO DA LIGA 
    liga_sel = st.selectbox("🏆 Escolha a Liga", lista_ligas, index=idx_liga)
    df_l = df[df['Liga'] == liga_sel].copy()

    # --- TIMES DA LIGA SELECIONADA ---
    lista_times = sorted(df_l['Mandante'].unique()) [cite: 1, 5]
    
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
    mando_only = st.sidebar.checkbox("Analisar apenas Casa/Fora (Split)")

    st.divider()
    st.subheader(f"📊 {m_sel} vs {v_sel}")

    # --- FUNÇÕES DE APOIO ---
    def extrair_metrica(df_hist, time, col_h, col_a):
        m = df_hist['Mandante'] == time
        v = df_hist['Visitante'] == time
        return pd.concat([df_hist[m][col_h], df_hist[v][col_a]])

    def calcular_posicoes(df_liga):
        stats = {}
        for _, r in df_liga.iterrows():
            m, v = r['Mandante'], r['Visitante']
            gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT'] [cite: 1, 2, 5]
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
            df_f = df_hist[df_hist['Mandante' if mando=="Casa" else 'Visitante'] == time].sort_values('Data', ascending=False).head(5)
        else:
            df_f = df_hist[(df_hist['Mandante'] == time) | (df_hist['Visitante'] == time)].sort_values('Data', ascending=False).head(5)
        
        resultados = []
        for _, r in df_f.iterrows():
            if r['Gols_Mandante_FT'] == r['Gols_Visitante_FT']: resultados.append("🟡")
            elif (r['Mandante'] == time and r['Gols_Mandante_FT'] > r['Gols_Visitante_FT']) or \
                 (r['Visitante'] == time and r['Gols_Visitante_FT'] > r['Gols_Mandante_FT']): resultados.append("🟢")
            else: resultados.append("🔴")
        return " ".join(resultados)

    # --- FILTRAGEM DOS JOGOS ---
    if mando_only:
        df_m_last = df_l[df_l['Mandante'] == m_sel].sort_values('Data', ascending=False).head(n_jogos)
        df_v_last = df_l[df_l['Visitante'] == v_sel].sort_values('Data', ascending=False).head(n_jogos)
    else:
        df_m_last = df_l[(df_l['Mandante'] == m_sel) | (df_l['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(n_jogos)
        df_v_last = df_l[(df_l['Mandante'] == v_sel) | (df_l['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(n_jogos)

    # --- MÉTRICAS DE TOPO ---
    tabela_liga = calcular_posicoes(df_l)
    try:
        pos_m = tabela_liga[tabela_liga['Time'] == m_sel]['Pos'].values[0]
        pos_v = tabela_liga[tabela_liga['Time'] == v_sel]['Pos'].values[0]
        
        st.markdown("""<style>
            div[data-testid="stMetricValue"] > div { text-align: center !important; color: #1f77b4 !important; font-weight: bold !important; justify-content: center !important; }
            div[data-testid="stMetricLabel"] > div { text-align: center !important; justify-content: center !important; color: #31333F !important; }
            [data-testid="stMetric"] { text-align: center; display: flex; flex-direction: column; align-items: center; background: #f0f2f6; padding: 10px; border-radius: 10px; }
            </style>""", unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric(label=f"Pos {m_sel}", value=f"{pos_m}º")
        with c2: st.metric(label=f"Pos {v_sel}", value=f"{pos_v}º")
        with c3: st.metric(label="Forma Casa", value=get_forma(df_l, m_sel, True, 'Casa'))
        with c4: st.metric(label="Forma Fora", value=get_forma(df_l, v_sel, True, 'Fora'))
    except: st.info("Aguardando seleção...")

    # --- RADAR NORMALIZADO  ---
    st.divider()
    st.subheader("🕸️ Radar de Estilo de Jogo (Dados Normalizados)")
    
    def criar_radar_normalizado(df_m, df_v, t1, t2):
        metrics = ['xG', 'Posse %', 'Atq. Perigosos', 'Finalizações', 'Cantos', 'Faltas'] [cite: 1, 2, 5]
        
        def get_means(df_h, t):
            return [
                extrair_metrica(df_h, t, 'xG_Mandante', 'xG_Visitante').mean(), [cite: 1, 2, 5]
                extrair_metrica(df_h, t, 'Possession_H', 'Possession_A').mean(), [cite: 1, 2, 5]
                extrair_metrica(df_h, t, 'DangerousAttacks_H', 'DangerousAttacks_A').mean(), [cite: 1, 2, 5]
                extrair_metrica(df_h, t, 'Shots_H', 'Shots_A').mean(), [cite: 1, 2, 5]
                extrair_metrica(df_h, t, 'Corners_H', 'Corners_A').mean(), [cite: 1, 2, 5]
                extrair_metrica(df_h, t, 'Fouls_H', 'Fouls_A').mean() [cite: 1, 2, 5]
            ]

        m1 = get_means(df_m, t1)
        m2 = get_means(df_v, t2)

        # Lógica de Normalização (Escala 0-100) 
        max_values = [3.0, 100.0, 100.0, 20.0, 12.0, 20.0]
        norm1 = [(v / m) * 100 for v, m in zip(m1, max_values)]
        norm2 = [(v / m) * 100 for v, m in zip(m2, max_values)]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=norm1, theta=metrics, fill='toself', name=t1, line_color='blue', hoverinfo="text", text=[f"{v:.2f}" for v in m1]))
        fig.add_trace(go.Scatterpolar(r=norm2, theta=metrics, fill='toself', name=t2, line_color='red', hoverinfo="text", text=[f"{v:.2f}" for v in m2]))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True, height=450)
        return fig

    st.plotly_chart(criar_radar_normalizado(df_m_last, df_v_last, m_sel, v_sel), use_container_width=True)

    # --- MOMENTUM DE GOLS  ---
    st.divider()
    st.subheader("⏱️ Momentum de Gols (Faixas de 15 min)") [cite: 3, 4]
    faixas = ['0-15', '16-30', '31-45+', '46-60', '61-75', '76-90+'] [cite: 3, 4]
    
    def plot_momentum(df_m, df_v, t1, t2):
        def get_marcados(df_hist, t):
            return [df_hist[df_hist['Mandante']==t][f'{f}_Mandante'].sum() + df_hist[df_hist['Visitante']==t][f'{f}_Visitante'].sum() for f in faixas] [cite: 1, 3, 5]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=faixas, y=get_marcados(df_m, t1), name=f"Gols {t1}", marker_color='blue'))
        fig.add_trace(go.Bar(x=faixas, y=get_marcados(df_v, t2), name=f"Gols {t2}", marker_color='red'))
        fig.update_layout(barmode='group', height=400)
        return fig
    st.plotly_chart(plot_momentum(df_m_last, df_v_last, m_sel, v_sel), use_container_width=True)

    # --- TABELAS TÉCNICAS ULTRA DETALHADAS  ---
    st.divider()
    st.markdown("### 📉 Estatísticas de Performance")

    def get_stats_combo(series):
        if series.empty: return [0.0]*5
        series = pd.to_numeric(series, errors='coerce').fillna(0)
        mean = series.mean(); median = series.median(); mode = series.mode().iloc[0] if not series.mode().empty else 0.0
        std = series.std(); cv = (std / mean) if mean != 0 else 0.0
        return [mean, median, mode, std, cv]

    def preparar_tabela_tecnica(df_hist, time):
        data = [
            ['Gols Marcados (FT)'] + get_stats_combo(extrair_metrica(df_hist, time, 'Gols_Mandante_FT', 'Gols_Visitante_FT')), [cite: 1, 2, 5]
            ['Gols Sofridos (FT)'] + get_stats_combo(extrair_metrica(df_hist, time, 'Gols_Visitante_FT', 'Gols_Mandante_FT')), [cite: 1, 2, 5]
            ['xG (Expectativa)'] + get_stats_combo(extrair_metrica(df_hist, time, 'xG_Mandante', 'xG_Visitante')), [cite: 1, 2, 5]
            ['Posse de Bola (%)'] + get_stats_combo(extrair_metrica(df_hist, time, 'Possession_H', 'Possession_A')), [cite: 1, 2, 5]
            ['Ataques Perigosos'] + get_stats_combo(extrair_metrica(df_hist, time, 'DangerousAttacks_H', 'DangerousAttacks_A')), [cite: 1, 2, 5]
            ['Finalizações (Total)'] + get_stats_combo(extrair_metrica(df_hist, time, 'Shots_H', 'Shots_A')), [cite: 1, 2, 5]
            ['Chutes no Gol'] + get_stats_combo(extrair_metrica(df_hist, time, 'ShotsOnTarget_H', 'ShotsOnTarget_A')), [cite: 1, 2, 5]
            ['Escanteios (Cantos)'] + get_stats_combo(extrair_metrica(df_hist, time, 'Corners_H', 'Corners_A')), [cite: 1, 2, 5]
            ['Faltas Cometidas'] + get_stats_combo(extrair_metrica(df_hist, time, 'Fouls_H', 'Fouls_A')), [cite: 1, 2, 5]
            ['Cartões Amarelos'] + get_stats_combo(extrair_metrica(df_hist, time, 'Yellow_Cards_H', 'Yellow_Cards_A')) [cite: 1, 2, 5]
        ]
        return pd.DataFrame(data, columns=['Métrica', 'Média', 'Mediana', 'Moda', 'DP', 'CV'])

    ct1, ct2 = st.columns(2)
    with ct1: st.table(preparar_tabela_tecnica(df_m_last, m_sel).style.format({c: "{:.2f}" for c in ['Média', 'Mediana', 'Moda', 'DP', 'CV']}))
    with ct2: st.table(preparar_tabela_tecnica(df_v_last, v_sel).style.format({c: "{:.2f}" for c in ['Média', 'Mediana', 'Moda', 'DP', 'CV']}))

    # --- HISTÓRICO DETALHADO COM ODDS  ---
    st.divider()
    st.markdown("### 📝 Histórico Detalhado (Últimos Jogos)")
    
    def preparar_h(df_h, time, apenas_mando=False, mando="Casa"):
        df_h = df_h.copy()
        if apenas_mando:
            df_f = df_h[df_h['Mandante' if mando=="Casa" else 'Visitante'] == time].sort_values('Data', ascending=False).head(10)
        else:
            df_f = df_h[(df_h['Mandante']==time)|(df_h['Visitante']==time)].sort_values('Data', ascending=False).head(10)
        
        res = []
        for _, r in df_f.iterrows():
            res.append({
                'Data': r['Data'], [cite: 1, 5]
                'Oponente': r['Visitante'] if r['Mandante']==time else r['Mandante'], [cite: 1, 5]
                'Placar HT': f"{int(r['Gols_Mandante_HT'])}x{int(r['Gols_Visitante_HT'])}", [cite: 1, 2, 5]
                'Placar FT': f"{int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])}", [cite: 1, 2, 5]
                'Odd 1 HT': r['Odd_H_HT'], 'Odd D HT': r['Odd_D_HT'], 'Odd 2 HT': r['Odd_A_HT'], [cite: 1, 2, 5]
                'Odd O25 FT': r['Odd_Over25_FT'], 'Odd BTTS': r['Odd_BTTS_Sim'], [cite: 1, 2, 5]
                'xG Jogo': f"{r['xG_Mandante']:.1f}-{r['xG_Visitante']:.1f}" [cite: 1, 2, 5]
            })
        return pd.DataFrame(res)
    
    st.write(f"**Jogos de {m_sel}**")
    st.table(preparar_h(df_l, m_sel, mando_only, "Casa"))
    st.write(f"**Jogos de {v_sel}**")
    st.table(preparar_h(df_l, v_sel, mando_only, "Fora"))

    # --- OUTROS DADOS E INCIDÊNCIA  ---
    st.divider()
    st.subheader("📊 Outras Estatísticas e Incidência")
    
    def calc_incidencia(df_hist):
        return pd.DataFrame([
            {'Mercado': 'Over 0.5 FT', 'Frequência': f"{(df_hist['Over05_Realizado']=='✅').mean()*100:.1f}%"}, [cite: 1, 2, 5]
            {'Mercado': 'Over 1.5 FT', 'Frequência': f"{(df_hist['Over15_Realizado']=='✅').mean()*100:.1f}%"}, [cite: 1, 2, 5]
            {'Mercado': 'Over 2.5 FT', 'Frequência': f"{(df_hist['Over25_Realizado']=='✅').mean()*100:.1f}%"}, [cite: 1, 2, 5]
            {'Mercado': 'BTTS Sim', 'Frequência': f"{(df_hist['BTTS_Realizado']=='✅').mean()*100:.1f}%"} [cite: 1, 2, 5]
        ])

    ci1, ci2 = st.columns(2)
    with ci1: st.write(f"Incidência {m_sel}"); st.table(calc_incidencia(df_m_last))
    with ci2: st.write(f"Incidência {v_sel}"); st.table(calc_incidencia(df_v_last))
