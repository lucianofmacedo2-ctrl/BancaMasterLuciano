import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from difflib import get_close_matches

def mostrar_scout(df):
    st.markdown("## 🔎 Painel de Análise Profissional Ultra")
    
    # 1. Ajuste e Limpeza de Colunas
    df.columns = [c.strip() for c in df.columns]

    # --- LÓGICA DE INDEXAÇÃO AUTOMÁTICA (Persistência de Estado) ---
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
            df_f = df_hist[df_hist['Mandante' if mando=="Casa" else 'Visitante'] == time].sort_values('Data', ascending=False).head(5)
        else:
            df_f = df_hist[(df_hist['Mandante'] == time) | (df_hist['Visitante'] == time)].sort_values('Data', ascending=False).head(5)
        
        resultados = []
        for _, r in df_f.iterrows():
            gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
            if gm == gv: resultados.append("🟡")
            elif (r['Mandante'] == time and gm > gv) or (r['Visitante'] == time and gv > gm): resultados.append("🟢")
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

    # --- RADAR DE ESTILO (NORMALIZADO) ---
    st.divider()
    st.subheader("🕸️ Radar de Estilo de Jogo (Normalizado 0-100)")
    def criar_radar_normalizado(df_m, df_v, t1, t2):
        metrics = ['xG', 'Posse %', 'Atq. Perigosos', 'Finalizações', 'Cantos', 'Faltas']
        def get_means(df_h, t):
            return [
                extrair_metrica(df_h, t, 'xG_Mandante', 'xG_Visitante').mean(),
                extrair_metrica(df_h, t, 'Possession_H', 'Possession_A').mean(),
                extrair_metrica(df_h, t, 'DangerousAttacks_H', 'DangerousAttacks_A').mean(),
                extrair_metrica(df_h, t, 'Shots_H', 'Shots_A').mean(),
                extrair_metrica(df_h, t, 'Corners_H', 'Corners_A').mean(),
                extrair_metrica(df_h, t, 'Fouls_H', 'Fouls_A').mean()
            ]
        m1, m2 = get_means(df_m, t1), get_means(df_v, t2)
        max_values = [3.0, 100.0, 120.0, 25.0, 12.0, 25.0]
        norm1 = [(v / m) * 100 if m > 0 else 0 for v, m in zip(m1, max_values)]
        norm2 = [(v / m) * 100 if m > 0 else 0 for v, m in zip(m2, max_values)]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(r=norm1, theta=metrics, fill='toself', name=t1, line_color='blue', text=[f"{v:.2f}" for v in m1], hoverinfo="name+text+theta"))
        fig.add_trace(go.Scatterpolar(r=norm2, theta=metrics, fill='toself', name=t2, line_color='red', text=[f"{v:.2f}" for v in m2], hoverinfo="name+text+theta"))
        fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True, height=450)
        return fig
    st.plotly_chart(criar_radar_normalizado(df_m_last, df_v_last, m_sel, v_sel), use_container_width=True)

    # --- MOMENTUM E ALERTAS DE LIGA ---
    st.divider()
    st.subheader("⏱️ Momentum e Alerta de Tendências (Vs Liga)")
    faixas = ['0-15', '16-30', '31-45+', '46-60', '61-75', '76-90+']
    
    col_al1, col_al2 = st.columns(2)
    with col_al1:
        avg_liga_corners = df_l['Total_Corners'].mean()
        my_avg_c = extrair_metrica(df_m_last, m_sel, 'Corners_H', 'Corners_A').mean()
        st.metric(f"Cantos/Jogo ({m_sel})", f"{my_avg_c:.2f}", delta=f"{(my_avg_c*2)-avg_liga_corners:.2f} vs Liga")
    with col_al2:
        avg_liga_gols = df_l['Total_Gols_FT'].mean()
        my_avg_g = extrair_metrica(df_v_last, v_sel, 'Gols_Mandante_FT', 'Gols_Visitante_FT').mean()
        st.metric(f"Gols Marcados ({v_sel})", f"{my_avg_g:.2f}", delta=f"{my_avg_g-(avg_liga_gols/2):.2f} vs Liga")

    def plot_momentum(df_m, df_v, t1, t2):
        def get_g(df_h, t): return [df_h[df_h['Mandante']==t][f'{f}_Mandante'].sum() + df_h[df_h['Visitante']==t][f'{f}_Visitante'].sum() for f in faixas]
        fig = go.Figure()
        fig.add_trace(go.Bar(x=faixas, y=get_g(df_m, t1), name=t1, marker_color='blue'))
        fig.add_trace(go.Bar(x=faixas, y=get_g(df_v, t2), name=t2, marker_color='red'))
        fig.update_layout(barmode='group', height=350, title="Distribuição de Gols Marcados por Tempo")
        return fig
    st.plotly_chart(plot_momentum(df_m_last, df_v_last, m_sel, v_sel), use_container_width=True)

    # --- TABELAS TÉCNICAS (ESTATÍSTICAS COMPLETAS) ---
    st.divider()
    st.markdown("### 📉 Estatísticas de Performance")
    def get_stats_combo(series):
        if series.empty: return [0.0]*5
        series = pd.to_numeric(series, errors='coerce').fillna(0)
        mean = series.mean()
        std = series.std()
        return [mean, series.median(), series.mode().iloc[0] if not series.mode().empty else 0.0, std, (std/mean) if mean!=0 else 0.0]

    def preparar_tabela_tecnica(df_hist, time):
        data = [
            ['Gols Marcados'] + get_stats_combo(extrair_metrica(df_hist, time, 'Gols_Mandante_FT', 'Gols_Visitante_FT')),
            ['Gols Sofridos'] + get_stats_combo(extrair_metrica(df_hist, time, 'Gols_Visitante_FT', 'Gols_Mandante_FT')),
            ['xG'] + get_stats_combo(extrair_metrica(df_hist, time, 'xG_Mandante', 'xG_Visitante')),
            ['Posse %'] + get_stats_combo(extrair_metrica(df_hist, time, 'Possession_H', 'Possession_A')),
            ['Finalizações'] + get_stats_combo(extrair_metrica(df_hist, time, 'Shots_H', 'Shots_A')),
            ['Cantos'] + get_stats_combo(extrair_metrica(df_hist, time, 'Corners_H', 'Corners_A')),
            ['Faltas'] + get_stats_combo(extrair_metrica(df_hist, time, 'Fouls_H', 'Fouls_A'))
        ]
        return pd.DataFrame(data, columns=['Métrica', 'Média', 'Mediana', 'Moda', 'DP', 'CV'])

    ct1, ct2 = st.columns(2)
    with ct1: st.write(f"**Estatísticas {m_sel}**"); st.table(preparar_tabela_tecnica(df_m_last, m_sel).style.format({c: "{:.2f}" for c in ['Média', 'Mediana', 'Moda', 'DP', 'CV']}))
    with ct2: st.write(f"**Estatísticas {v_sel}**"); st.table(preparar_tabela_tecnica(df_v_last, v_sel).style.format({c: "{:.2f}" for c in ['Média', 'Mediana', 'Moda', 'DP', 'CV']}))

    # --- CALCULADORA DE VALOR E INCIDÊNCIA ---
    st.divider()
    st.subheader("💎 Calculadora de Valor e Incidência")
    def calc_inc(df_h):
        df_h['BTTS'] = (df_h['Gols_Mandante_FT']>0) & (df_h['Gols_Visitante_FT']>0)
        df_h['Total_HT'] = df_h['Total_Gols_HT']
        df_h['Total_FT'] = df_h['Total_Gols_FT']
        linhas = []
        for merc, cond in zip(['Over 0.5 HT', 'Over 2.5 FT', 'BTTS Sim'], [df_h['Total_HT']>0, df_h['Total_FT']>2.5, df_h['BTTS']]):
            freq = cond.mean()
            odd_j = 1/freq if freq > 0 else 0
            linhas.append({'Mercado': merc, 'Freq': f"{freq*100:.1f}%", 'Odd Justa': f"{odd_j:.2f}" if odd_j > 0 else "N/A"})
        return pd.DataFrame(linhas)
    
    ci1, ci2 = st.columns(2)
    with ci1: st.write(f"Valor {m_sel}"); st.table(calc_inc(df_m_last))
    with ci2: st.write(f"Valor {v_sel}"); st.table(calc_inc(df_v_last))

    # --- MAPA DE CALOR DE GOLS POR MINUTO ---
    st.divider()
    st.markdown("### ⏰ Mapa de Gols por Faixa de Minutos")
    def preparar_minutos_mapa(df_hist, time):
        marc, sofr = [], []
        for f in faixas:
            m = df_hist[df_hist['Mandante'] == time][f'{f}_Mandante'].sum() + df_hist[df_hist['Visitante'] == time][f'{f}_Visitante'].sum()
            s = df_hist[df_hist['Mandante'] == time][f'{f}_Visitante'].sum() + df_hist[df_hist['Visitante'] == time][f'{f}_Mandante'].sum()
            marc.append(int(m)); sofr.append(int(s))
        return pd.DataFrame({'Intervalo': faixas, 'Marcados': marc, 'Sofridos': sofr}).set_index('Intervalo').T

    st.write(f"📊 **Mapa {m_sel}**")
    st.dataframe(preparar_minutos_mapa(df_m_last, m_sel).style.background_gradient(cmap='RdYlGn', axis=1), use_container_width=True)
    st.write(f"📊 **Mapa {v_sel}**")
    st.dataframe(preparar_minutos_mapa(df_v_last, v_sel).style.background_gradient(cmap='RdYlGn', axis=1), use_container_width=True)

    # --- HISTÓRICO DETALHADO ---
    st.divider()
    st.markdown("### 📝 Histórico Detalhado (Últimos 10 Jogos)")
    def preparar_h(df_h, time, apenas_mando=False, mando="Casa"):
        df_f = df_h[df_h['Mandante' if mando=="Casa" else 'Visitante'] == time] if apenas_mando else df_h[(df_h['Mandante']==time)|(df_h['Visitante']==time)]
        df_f = df_f.sort_values('Data', ascending=False).head(10)
        res = []
        for _, r in df_f.iterrows():
            res.append({
                'Data': r['Data'], 
                'Mando': "Casa" if r['Mandante']==time else "Fora",
                'Oponente': r['Visitante'] if r['Mandante']==time else r['Mandante'], 
                'FT': f"{int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])}", 
                'xG': f"{r['xG_Mandante']:.1f}-{r['xG_Visitante']:.1f}", 
                'Odd H': r['Odd_Mandante_FT'], 'Odd D': r['Odd_Empate_FT'], 'Odd A': r['Odd_Visitante_FT']
            })
        return pd.DataFrame(res)
    
    st.write(f"**Jogos de {m_sel}**"); st.table(preparar_h(df_l, m_sel, mando_only, "Casa"))
    st.write(f"**Jogos de {v_sel}**"); st.table(preparar_h(df_l, v_sel, mando_only, "Fora"))
