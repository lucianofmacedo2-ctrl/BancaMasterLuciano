import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from difflib import get_close_matches

def mostrar_scout(df):
    st.markdown("## 🔎 Painel de Análise Profissional Ultra")
    
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
    
    # MELHORIA 3: Filtro de Mando (Split Home/Away)
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

    # --- FILTRAGEM DOS ÚLTIMOS JOGOS ---
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
        
        st.markdown("""
            <style>
            div[data-testid="stMetricValue"] > div { text-align: center !important; color: #1f77b4 !important; font-weight: bold !important; justify-content: center !important; }
            div[data-testid="stMetricLabel"] > div { text-align: center !important; justify-content: center !important; color: #31333F !important; }
            [data-testid="stMetric"] { text-align: center; display: flex; flex-direction: column; align-items: center; background: #f0f2f6; padding: 10px; border-radius: 10px; }
            </style>
            """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric(label=f"Posição {m_sel}", value=f"{pos_m}º")
        with c2: st.metric(label=f"Posição {v_sel}", value=f"{pos_v}º")
        with c3: st.metric(label="Forma Casa", value=get_forma(df_l, m_sel, True, 'Casa'))
        with c4: st.metric(label="Forma Fora", value=get_forma(df_l, v_sel, True, 'Fora'))
    except:
        st.info("Aguardando seleção...")

    # --- MELHORIA 5: RADAR DE ESTILO ---
    st.divider()
    st.subheader("🕸️ Radar Comparativo de Estilo de Jogo")
    
    def criar_radar(df_m, df_v, t1, t2):
        metrics = ['xG', 'Posse %', 'Atq. Perigosos', 'Finalizações', 'Cantos', 'Faltas']
        
        # Função interna para garantir que não dê erro se vazio
        def safe_mean(series): return series.mean() if not series.empty else 0

        val1 = [
            safe_mean(extrair_metrica(df_m, t1, 'xG_Mandante', 'xG_Visitante')),
            safe_mean(extrair_metrica(df_m, t1, 'Possession_H', 'Possession_A')),
            safe_mean(extrair_metrica(df_m, t1, 'DangerousAttacks_H', 'DangerousAttacks_A')) / 1.5, # Ajuste escala
            safe_mean(extrair_metrica(df_m, t1, 'Shots_H', 'Shots_A')),
            safe_mean(extrair_metrica(df_m, t1, 'Corners_H', 'Corners_A')),
            safe_mean(extrair_metrica(df_m, t1, 'Fouls_H', 'Fouls_A'))
        ]
        val2 = [
            safe_mean(extrair_metrica(df_v, t2, 'xG_Mandante', 'xG_Visitante')),
            safe_mean(extrair_metrica(df_v, t2, 'Possession_H', 'Possession_A')),
            safe_mean(extrair_metrica(df_v, t2, 'DangerousAttacks_H', 'DangerousAttacks_A')) / 1.5,
            safe_mean(extrair_metrica(df_v, t2, 'Shots_H', 'Shots_A')),
            safe_mean(extrair_metrica(df_v, t2, 'Corners_H', 'Corners_A')),
            safe_mean(extrair_metrica(df_v, t2, 'Fouls_H', 'Fouls_A'))
        ]

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=val1, theta=metrics, fill='toself', name=t1, line_color='blue'))
        fig.add_trace(go.Scatterpolar(r=val2, theta=metrics, fill='toself', name=t2, line_color='red'))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True)), showlegend=True, height=450)
        return fig

    st.plotly_chart(criar_radar(df_m_last, df_v_last, m_sel, v_sel), use_container_width=True)

    # --- MELHORIA 2: MOMENTUM DE GOLS ---
    st.divider()
    st.subheader("⏱️ Momentum de Gols (Distribuição Real)")
    faixas = ['0-15', '16-30', '31-45+', '46-60', '61-75', '76-90+']
    
    def plot_momentum(df_m, df_v, t1, t2):
        def get_marcados(df_hist, t):
            return [df_hist[df_hist['Mandante']==t][f'{f}_Mandante'].sum() + df_hist[df_hist['Visitante']==t][f'{f}_Visitante'].sum() for f in faixas]
        
        m_gols = get_marcados(df_m, t1)
        v_gols = get_marcados(df_v, t2)
        
        fig = go.Figure()
        fig.add_trace(go.Bar(x=faixas, y=m_gols, name=f"Gols {t1}", marker_color='blue', opacity=0.7))
        fig.add_trace(go.Bar(x=faixas, y=v_gols, name=f"Gols {t2}", marker_color='red', opacity=0.7))
        fig.update_layout(barmode='group', xaxis_title="Intervalo de Minutos", yaxis_title="Total de Gols Acumulados")
        return fig

    st.plotly_chart(plot_momentum(df_m_last, df_v_last, m_sel, v_sel), use_container_width=True)

    # --- MELHORIA 1: TENDÊNCIAS VS MÉDIA DA LIGA ---
    st.divider()
    st.subheader("🔥 Alerta de Tendências (Vs Média da Liga)")
    avg_liga_corners = df_l['Total_Corners'].mean()
    avg_liga_gols = df_l['Total_Gols_FT'].mean()
    
    col_al1, col_al2 = st.columns(2)
    with col_al1:
        my_avg_c = extrair_metrica(df_m_last, m_sel, 'Corners_H', 'Corners_A').mean()
        diff_c = (my_avg_c * 2) - avg_liga_corners
        st.metric(f"Cantos Esperados ({m_sel})", f"{my_avg_c:.2f}", delta=f"{diff_c:.2f} vs Liga", delta_color="normal")
    with col_al2:
        my_avg_g = extrair_metrica(df_v_last, v_sel, 'Gols_Mandante_FT', 'Gols_Visitante_FT').mean()
        diff_g = my_avg_g - (avg_liga_gols / 2)
        st.metric(f"Gols Marcados Média ({v_sel})", f"{my_avg_g:.2f}", delta=f"{diff_g:.2f} vs Liga", delta_color="normal")

    # --- TABELA TÉCNICA ULTRA DETALHADA ---
    st.divider()
    st.markdown("### 📉 Estatísticas de Performance")

    def get_stats_combo(series):
        if series.empty: return [0.0]*5
        series = pd.to_numeric(series, errors='coerce').fillna(0)
        mean = series.mean(); median = series.median()
        mode = series.mode().iloc[0] if not series.mode().empty else 0.0
        std = series.std(); cv = (std / mean) if mean != 0 else 0.0
        return [mean, median, mode, std, cv]

    def preparar_tabela_tecnica_v2(df_hist, time):
        data = [
            ['Gols Marcados (FT)'] + get_stats_combo(extrair_metrica(df_hist, time, 'Gols_Mandante_FT', 'Gols_Visitante_FT')),
            ['Gols Sofridos (FT)'] + get_stats_combo(extrair_metrica(df_hist, time, 'Gols_Visitante_FT', 'Gols_Mandante_FT')),
            ['xG (Expectativa)'] + get_stats_combo(extrair_metrica(df_hist, time, 'xG_Mandante', 'xG_Visitante')),
            ['Posse de Bola (%)'] + get_stats_combo(extrair_metrica(df_hist, time, 'Possession_H', 'Possession_A')),
            ['Ataques Perigosos'] + get_stats_combo(extrair_metrica(df_hist, time, 'DangerousAttacks_H', 'DangerousAttacks_A')),
            ['Finalizações'] + get_stats_combo(extrair_metrica(df_hist, time, 'Shots_H', 'Shots_A')),
            ['Chutes no Gol'] + get_stats_combo(extrair_metrica(df_hist, time, 'ShotsOnTarget_H', 'ShotsOnTarget_A')),
            ['Cantos (Escanteios)'] + get_stats_combo(extrair_metrica(df_hist, time, 'Corners_H', 'Corners_A')),
            ['Faltas Cometidas'] + get_stats_combo(extrair_metrica(df_hist, time, 'Fouls_H', 'Fouls_A')),
            ['Cartões Amarelos'] + get_stats_combo(extrair_metrica(df_hist, time, 'Yellow_Cards_H', 'Yellow_Cards_A')),
            ['Impedimentos'] + get_stats_combo(extrair_metrica(df_hist, time, 'Offsides_H', 'Offsides_A'))
        ]
        return pd.DataFrame(data, columns=['Métrica', 'Média', 'Mediana', 'Moda', 'DP', 'CV'])

    col_t1, col_t2 = st.columns(2)
    with col_t1: 
        st.write(f"📈 **Estatísticas: {m_sel}**")
        st.table(preparar_tabela_tecnica_v2(df_m_last, m_sel).style.format({c: "{:.2f}" for c in ['Média', 'Mediana', 'Moda', 'DP', 'CV']}))
    with col_t2: 
        st.write(f"📈 **Estatísticas: {v_sel}**")
        st.table(preparar_tabela_tecnica_v2(df_v_last, v_sel).style.format({c: "{:.2f}" for c in ['Média', 'Mediana', 'Moda', 'DP', 'CV']}))

    # --- INCIDÊNCIA DE MERCADOS ---
    st.divider()
    st.markdown("### 💰 Incidência de Mercados e Filtros de Odds")
    
    def calcular_incidencia_v2(df_hist):
        df_hist = df_hist.copy()
        df_hist['Total_HT'] = pd.to_numeric(df_hist['Total_Gols_HT'], errors='coerce').fillna(0)
        df_hist['Total_FT'] = pd.to_numeric(df_hist['Total_Gols_FT'], errors='coerce').fillna(0)
        df_hist['BTTS'] = (pd.to_numeric(df_hist['Gols_Mandante_FT']) > 0) & (pd.to_numeric(df_hist['Gols_Visitante_FT']) > 0)
        df_hist['C_HT'] = pd.to_numeric(df_hist['Total_Corners_HT'], errors='coerce').fillna(0)

        linhas = [
            {'Mercado': 'Over 0.5 HT', 'Freq (%)': f"{(df_hist['Total_HT'] > 0.5).mean()*100:.1f}%", 'Média Odds': f"{df_hist['Odd_Over05_HT'].mean():.2f}"},
            {'Mercado': 'Over 1.5 FT', 'Freq (%)': f"{(df_hist['Total_FT'] > 1.5).mean()*100:.1f}%", 'Média Odds': f"{df_hist['Odd_Over15_FT'].mean():.2f}"},
            {'Mercado': 'Over 2.5 FT', 'Freq (%)': f"{(df_hist['Total_FT'] > 2.5).mean()*100:.1f}%", 'Média Odds': f"{df_hist['Odd_Over25_FT'].mean():.2f}"},
            {'Mercado': 'Ambas Marcam', 'Freq (%)': f"{df_hist['BTTS'].mean()*100:.1f}%", 'Média Odds': f"{df_hist['Odd_BTTS_Sim'].mean():.2f}"},
            {'Mercado': 'Cantos Over 3.5 HT', 'Freq (%)': f"{(df_hist['C_HT'] > 3.5).mean()*100:.1f}%", 'Média Odds': '---'}
        ]
        return pd.DataFrame(linhas)

    cm1, cm2 = st.columns(2)
    with cm1: st.table(calcular_incidencia_v2(df_m_last))
    with cm2: st.table(calcular_incidencia_v2(df_v_last))

    # --- MELHORIA 4: CALCULADORA DE VALOR (ODDS JUSTAS) ---
    st.divider()
    st.subheader("💎 Calculadora de Valor (Odds Justas baseadas na Amostragem)")
    
    def calcular_valor(df_hist, mercado):
        if df_hist.empty: return "0.00", "N/A"
        if mercado == 'O25':
            freq = (pd.to_numeric(df_hist['Total_Gols_FT']) > 2.5).mean()
            odd_mercado = df_hist['Odd_Over25_FT'].mean()
        else:
            freq = ((pd.to_numeric(df_hist['Gols_Mandante_FT']) > 0) & (pd.to_numeric(df_hist['Gols_Visitante_FT']) > 0)).mean()
            odd_mercado = df_hist['Odd_BTTS_Sim'].mean()
        
        odd_justa = 1/freq if freq > 0 else 99.0
        status = "✅ VALOR" if odd_mercado > odd_justa else "❌ SEM VALOR"
        return f"{odd_justa:.2f}", status

    val_c1, val_c2 = st.columns(2)
    with val_c1:
        oj, stt = calcular_valor(df_m_last, 'O25')
        st.info(f"**Over 2.5 FT ({m_sel})**\n\nOdd Justa: {oj} | {stt}")
    with val_c2:
        oj, stt = calcular_valor(df_v_last, 'BTTS')
        st.info(f"**BTTS ({v_sel})**\n\nOdd Justa: {oj} | {stt}")

    # --- DISTRIBUIÇÃO POR MINUTOS COM DEGRADÊ ---
    st.divider()
    st.markdown("### ⏰ Gols por Faixa de Minutos (Mapa de Calor)")
    
    def preparar_minutos_v2(df_hist, time):
        marc, sofr = [], []
        for f in faixas:
            col_m = f'{f}_Mandante'; col_v = f'{f}_Visitante'
            m = df_hist[df_hist['Mandante'] == time][col_m].sum() + df_hist[df_hist['Visitante'] == time][col_v].sum()
            s = df_hist[df_hist['Mandante'] == time][col_v].sum() + df_hist[df_hist['Visitante'] == time][col_m].sum()
            marc.append(int(m)); sofr.append(int(s))
        return pd.DataFrame({'Intervalo': faixas, 'Marcados': marc, 'Sofridos': sofr}).set_index('Intervalo').T

    st.write(f"📊 **Distribuição {m_sel}**")
    st.dataframe(preparar_minutos_v2(df_m_last, m_sel).style.background_gradient(cmap='RdYlGn', axis=1), use_container_width=True)
    st.write(f"📊 **Distribuição {v_sel}**")
    st.dataframe(preparar_minutos_v2(df_v_last, v_sel).style.background_gradient(cmap='RdYlGn', axis=1), use_container_width=True)

    # --- HISTÓRICO DETALHADO ---
    st.divider()
    st.markdown("### 📝 Histórico Detalhado")
    tipo_hist = st.selectbox("🎯 Filtrar Histórico da Tabela Abaixo", ["Geral", "Casa/Casa e Fora/Fora"])

    def preparar_hist_final(df_hist, time, apenas_mando=False, mando="Casa"):
        df_hist = df_hist.copy()
        df_hist['Data'] = pd.to_datetime(df_hist['Data'], errors='coerce')
        if apenas_mando:
            df_f = df_hist[df_hist['Mandante' if mando=="Casa" else 'Visitante'] == time].sort_values('Data', ascending=False).head(10)
        else:
            df_f = df_hist[(df_hist['Mandante'] == time) | (df_hist['Visitante'] == time)].sort_values('Data', ascending=False).head(10)
        
        jogos = []
        for _, r in df_f.iterrows():
            oponente = r['Visitante'] if r['Mandante'] == time else r['Mandante']
            m_label = "Casa" if r['Mandante'] == time else "Fora"
            jogos.append({
                'Data': r['Data'].strftime('%d/%m/%Y') if pd.notnull(r['Data']) else "N/A",
                'Mando': m_label, 'Oponente': oponente,
                'Placar': f"{int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])}",
                'xG': f"{r['xG_Mandante']:.1f}-{r['xG_Visitante']:.1f}",
                'Odd H': r['Odd_Mandante_FT'], 'Odd D': r['Odd_Empate_FT'], 'Odd A': r['Odd_Visitante_FT']
            })
        return pd.DataFrame(jogos)

    is_mando = True if tipo_hist == "Casa/Casa e Fora/Fora" else False
    st.write(f"**Últimos 10: {m_sel}**")
    st.table(preparar_hist_final(df_l, m_sel, is_mando, "Casa"))
    st.write(f"**Últimos 10: {v_sel}**")
    st.table(preparar_hist_final(df_l, v_sel, is_mando, "Fora"))
