import streamlit as st
import pandas as pd
import numpy as np

def mostrar_scout(df):
    st.markdown("## 🔎 Painel de Análise")
    
    # 1. Ajuste das colunas
    df.columns = [c.strip() for c in df.columns]

    # 2. SELEÇÃO DA LIGA
    lista_ligas = sorted(df['Liga'].unique())
    liga_sel = st.selectbox("🏆 Escolha a Liga", lista_ligas)
    df_l = df[df['Liga'] == liga_sel].copy()

    # 3. SELEÇÃO DOS TIMES
    lista_times = sorted(df_l['Mandante'].unique())
    m_sel = st.selectbox("🏠 Time da Casa", lista_times)
    v_sel = st.selectbox("🚌 Time de Fora", [t for t in lista_times if t != m_sel])

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

    def get_stats_combo(series):
        if series.empty: return [0.0]*5
        mean = series.mean()
        median = series.median()
        mode = series.mode().iloc[0] if not series.mode().empty else 0.0
        std = series.std()
        cv = (std / mean) if mean != 0 else 0.0
        return [mean, median, mode, std, cv]

    def highlight_max(s):
        is_max = s == s.max()
        return ['background-color: #1f77b4; color: white; font-weight: bold' if v and v > 0 else '' for v in is_max]

    # Execução do cálculo de posições
    tabela_liga = calcular_posicoes(df_l)
    
    try:
        pos_m = tabela_liga[tabela_liga['Time'] == m_sel]['Pos'].values[0]
        pos_v = tabela_liga[tabela_liga['Time'] == v_sel]['Pos'].values[0]
        dif = abs(pos_m - pos_v)

        # 5. ESTILO E EXIBIÇÃO DOS CARDS
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

    # --- 6. BLOCO: ESTATÍSTICA TÉCNICA ---
    st.divider()
    st.markdown("### 📉 Estatísticas Técnicas (Últimos Jogos)")
    df_m_last = df_l[(df_l['Mandante'] == m_sel) | (df_l['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(n_jogos)
    df_v_last = df_l[(df_l['Mandante'] == v_sel) | (df_l['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(n_jogos)

    def preparar_tabela_tecnica(df_hist, time):
        g_pro_ft = pd.concat([df_hist[df_hist['Mandante'] == time]['Gols_Mandante_FT'], df_hist[df_hist['Visitante'] == time]['Gols_Visitante_FT']])
        g_con_ft = pd.concat([df_hist[df_hist['Mandante'] == time]['Gols_Visitante_FT'], df_hist[df_hist['Visitante'] == time]['Gols_Mandante_FT']])
        g_pro_ht = pd.concat([df_hist[df_hist['Mandante'] == time]['Gols_Mandante_HT'], df_hist[df_hist['Visitante'] == time]['Gols_Visitante_HT']])
        g_con_ht = pd.concat([df_hist[df_hist['Mandante'] == time]['Gols_Visitante_HT'], df_hist[df_hist['Visitante'] == time]['Gols_Mandante_HT']])
        c_pro_ft = pd.concat([df_hist[df_hist['Mandante'] == time]['Corners_H'], df_hist[df_hist['Visitante'] == time]['Corners_A']])
        c_con_ft = pd.concat([df_hist[df_hist['Mandante'] == time]['Corners_A'], df_hist[df_hist['Visitante'] == time]['Corners_H']])
        ch_pro = pd.concat([df_hist[df_hist['Mandante'] == time]['ShotsOnTarget_H'], df_hist[df_hist['Visitante'] == time]['ShotsOnTarget_A']])
        ch_con = pd.concat([df_hist[df_hist['Mandante'] == time]['ShotsOnTarget_A'], df_hist[df_hist['Visitante'] == time]['ShotsOnTarget_H']])
        
        data = [
            ['Gols Marcados (FT)'] + get_stats_combo(g_pro_ft),
            ['Gols Sofridos (FT)'] + get_stats_combo(g_con_ft),
            ['Gols Marcados (HT)'] + get_stats_combo(g_pro_ht),
            ['Gols Sofridos (HT)'] + get_stats_combo(g_con_ht),
            ['Cantos FT (Pro)'] + get_stats_combo(c_pro_ft),
            ['Cantos FT (Contra)'] + get_stats_combo(c_con_ft),
            ['Chutes no Gol (Pro)'] + get_stats_combo(ch_pro),
            ['Chutes no Gol (Contra)'] + get_stats_combo(ch_con)
        ]
        return pd.DataFrame(data, columns=['Métrica', 'Média', 'Mediana', 'Moda', 'DP', 'CV'])

    col_t1, col_t2 = st.columns(2)
    with col_t1: st.table(preparar_tabela_tecnica(df_m_last, m_sel).style.format({c: "{:.2f}" for c in ['Média', 'Mediana', 'Moda', 'DP', 'CV']}))
    with col_t2: st.table(preparar_tabela_tecnica(df_v_last, v_sel).style.format({c: "{:.2f}" for c in ['Média', 'Mediana', 'Moda', 'DP', 'CV']}))

    # --- 7. BLOCO: INCIDÊNCIA DE MERCADOS ---
    st.divider()
    st.markdown("### 💰 Incidência de Mercados (%)")

    def calcular_incidencia(df_hist):
        df_hist = df_hist.copy()
        df_hist['Gols_M_ST'] = df_hist['Gols_Mandante_FT'] - df_hist['Gols_Mandante_HT']
        df_hist['Gols_V_ST'] = df_hist['Gols_Visitante_FT'] - df_hist['Gols_Visitante_HT']
        df_hist['Total_HT'] = df_hist['Gols_Mandante_HT'] + df_hist['Gols_Visitante_HT']
        df_hist['Total_FT'] = df_hist['Gols_Mandante_FT'] + df_hist['Gols_Visitante_FT']
        df_hist['Total_ST'] = df_hist['Gols_M_ST'] + df_hist['Gols_V_ST']
        df_hist['BTTS_HT'] = (df_hist['Gols_Mandante_HT'] > 0) & (df_hist['Gols_Visitante_HT'] > 0)
        df_hist['BTTS_FT'] = (df_hist['Gols_Mandante_FT'] > 0) & (df_hist['Gols_Visitante_FT'] > 0)
        df_hist['BTTS_ST'] = (df_hist['Gols_M_ST'] > 0) & (df_hist['Gols_V_ST'] > 0)

        mercados = [0.5, 1.5, 2.5, 3.5]
        linhas = []
        for m in mercados:
            linhas.append({
                'Mercado': f'Over {m} Gols',
                'HT': f"{(df_hist['Total_HT'] > m).mean()*100:.2f}%",
                'ST': f"{(df_hist['Total_ST'] > m).mean()*100:.2f}%",
                'FT': f"{(df_hist['Total_FT'] > m).mean()*100:.2f}%"
            })
        linhas.append({'Mercado': 'BTTS (Ambas)', 'HT': f"{df_hist['BTTS_HT'].mean()*100:.2f}%", 'ST': f"{df_hist['BTTS_ST'].mean()*100:.2f}%", 'FT': f"{df_hist['BTTS_FT'].mean()*100:.2f}%"})
        return pd.DataFrame(linhas)

    col_m1, col_m2 = st.columns(2)
    with col_m1: st.table(calcular_incidencia(df_m_last))
    with col_m2: st.table(calcular_incidencia(df_v_last))

    # --- 8. BLOCO: ANÁLISE DE MINUTOS (CALOR) ---
    st.divider()
    st.markdown("### ⏰ Distribuição de Gols por Minutos (Soma na Amostragem)")
    
    faixas = ['0-15', '16-30', '31-45+', '46-60', '61-75', '76-90+']
    
    def preparar_minutos(df_hist, time):
        marcados, sofridos = [], []
        for f in faixas:
            m = df_hist[df_hist['Mandante'] == time][f'{f}_Mandante'].sum() + df_hist[df_hist['Visitante'] == time][f'{f}_Visitante'].sum()
            s = df_hist[df_hist['Mandante'] == time][f'{f}_Visitante'].sum() + df_hist[df_hist['Visitante'] == time][f'{f}_Mandante'].sum()
            marcados.append(int(m)); sofridos.append(int(s))
        return pd.DataFrame({'Intervalo': faixas, 'Gols Marcados': marcados, 'Gols Sofridos': sofridos})

    c_min1, c_min2 = st.columns(2)
    with c_min1:
        st.markdown(f"**{m_sel}**")
        df_min_m = preparar_minutos(df_m_last, m_sel)
        st.table(df_min_m.style.apply(highlight_max, subset=['Gols Marcados', 'Gols Sofridos']))
    with c_min2:
        st.markdown(f"**{v_sel}**")
        df_min_v = preparar_minutos(df_v_last, v_sel)
        st.table(df_min_v.style.apply(highlight_max, subset=['Gols Marcados', 'Gols Sofridos']))
