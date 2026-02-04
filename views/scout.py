import streamlit as st
import pandas as pd
import numpy as np

def mostrar_scout(df):
    st.markdown("## 🔎 Painel de Análise")
    
    # 1. Ajuste das colunas (Remoção de espaços extras)
    df.columns = [c.strip() for c in df.columns]

    # 2. SELEÇÃO DA LIGA
    lista_ligas = sorted(df['Liga'].unique())
    liga_sel = st.selectbox("🏆 Escolha a Liga", lista_ligas)
    df_l = df[df['Liga'] == liga_sel].copy()

    # 3. SELEÇÃO DOS TIMES
    lista_times = sorted(df_l['Mandante'].unique())
    m_sel = st.selectbox("🏠 Time da Casa", lista_times)
    
    # Filtra visitantes para não repetir o mandante
    visitantes_disponiveis = [t for t in lista_times if t != m_sel]
    v_sel = st.selectbox("🚌 Time de Fora", visitantes_disponiveis)

    # 4. CONFIGURAÇÃO (Sidebar)
    n_jogos = st.sidebar.slider("Amostragem (Últimos Jogos)", 5, 50, 10)
    
    st.divider()
    st.subheader(f"📊 {m_sel} vs {v_sel}")

    # --- FUNÇÃO INTERNA PARA CALCULAR CLASSIFICAÇÃO ---
    def calcular_posicoes(df_liga):
        stats = {}
        for _, r in df_liga.iterrows():
            m, v = r['Mandante'], r['Visitante']
            gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
            for t in [m, v]:
                if t not in stats: stats[t] = {'P': 0, 'V': 0, 'SG': 0}
            stats[m]['SG'] += (gm - gv)
            stats[v]['SG'] += (gv - gm)
            if gm > gv:
                stats[m]['P'] += 3; stats[m]['V'] += 1
            elif gm == gv:
                stats[m]['P'] += 1; stats[v]['P'] += 1
            else:
                stats[v]['P'] += 3; stats[v]['V'] += 1
        
        tab = pd.DataFrame.from_dict(stats, orient='index').reset_index().rename(columns={'index':'Time'})
        tab = tab.sort_values(by=['P', 'V', 'SG'], ascending=False).reset_index(drop=True)
        tab['Pos'] = tab.index + 1
        return tab

    # Execução do cálculo de posições
    tabela_liga = calcular_posicoes(df_l)
    
    try:
        pos_m = tabela_liga[tabela_liga['Time'] == m_sel]['Pos'].values[0]
        pos_v = tabela_liga[tabela_liga['Time'] == v_sel]['Pos'].values[0]
        dif = abs(pos_m - pos_v)

        # 5. ESTILO E EXIBIÇÃO DOS CARDS
        st.markdown("""
            <style>
            div[data-testid="stMetricValue"] > div {
                text-align: center !important;
                color: #000000 !important;
                font-weight: bold !important;
                justify-content: center !important;
            }
            div[data-testid="stMetricLabel"] > div {
                text-align: center !important;
                justify-content: center !important;
                color: #31333F !important;
            }
            [data-testid="stMetric"] {
                text-align: center;
                display: flex;
                flex-direction: column;
                align-items: center;
            }
            /* Centralização das tabelas */
            [data-testid="stTable"] td, [data-testid="stTable"] th { text-align: center !important; }
            </style>
            """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1: st.metric(label=f"Posição {m_sel}", value=f"{pos_m}º")
        with c2: st.metric(label=f"Posição {v_sel}", value=f"{pos_v}º")
        with c3: st.metric(label="Diferença de Tabela", value=f"{dif} pos.")
            
    except:
        st.info("Selecione os times para calcular posições.")

    # --- 6. BLOCO: ESTATÍSTICA TÉCNICA DETALHADA ---
    st.divider()
    st.markdown("### 📉 Estatísticas Técnicas (Últimos Jogos)")

    def get_stats_combo(series):
        if series.empty: return [0.0]*5
        mean = series.mean()
        median = series.median()
        mode = series.mode().iloc[0] if not series.mode().empty else 0.0
        std = series.std()
        cv = (std / mean) if mean != 0 else 0.0
        return [mean, median, mode, std, cv]

    # Filtrar amostragem para as tabelas
    df_m_last = df_l[(df_l['Mandante'] == m_sel) | (df_l['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(n_jogos)
    df_v_last = df_l[(df_l['Mandante'] == v_sel) | (df_l['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(n_jogos)

    def preparar_tabela_tecnica(df_hist, time):
        # Auxiliares para filtrar Marcados (Pro) e Sofridos (Contra)
        gols_pro_ft = pd.concat([df_hist[df_hist['Mandante'] == time]['Gols_Mandante_FT'], df_hist[df_hist['Visitante'] == time]['Gols_Visitante_FT']])
        gols_con_ft = pd.concat([df_hist[df_hist['Mandante'] == time]['Gols_Visitante_FT'], df_hist[df_hist['Visitante'] == time]['Gols_Mandante_FT']])
        
        gols_pro_ht = pd.concat([df_hist[df_hist['Mandante'] == time]['Gols_Mandante_HT'], df_hist[df_hist['Visitante'] == time]['Gols_Visitante_HT']])
        gols_con_ht = pd.concat([df_hist[df_hist['Mandante'] == time]['Gols_Visitante_HT'], df_hist[df_hist['Visitante'] == time]['Gols_Mandante_HT']])
        
        cant_pro_ft = pd.concat([df_hist[df_hist['Mandante'] == time]['Corners_H'], df_hist[df_hist['Visitante'] == time]['Corners_A']])
        cant_con_ft = pd.concat([df_hist[df_hist['Mandante'] == time]['Corners_A'], df_hist[df_hist['Visitante'] == time]['Corners_H']])
        
        if 'Corners_H_HT' in df_hist.columns:
            cant_pro_ht = pd.concat([df_hist[df_hist['Mandante'] == time]['Corners_H_HT'], df_hist[df_hist['Visitante'] == time]['Corners_A_HT']])
            cant_con_ht = pd.concat([df_hist[df_hist['Mandante'] == time]['Corners_A_HT'], df_hist[df_hist['Visitante'] == time]['Corners_H_HT']])
        else:
            cant_pro_ht = pd.Series(dtype=float)
            cant_con_ht = pd.Series(dtype=float)
            
        chutes_pro = pd.concat([df_hist[df_hist['Mandante'] == time]['ShotsOnTarget_H'], df_hist[df_hist['Visitante'] == time]['ShotsOnTarget_A']])
        chutes_con = pd.concat([df_hist[df_hist['Mandante'] == time]['ShotsOnTarget_A'], df_hist[df_hist['Visitante'] == time]['ShotsOnTarget_H']])
        
        data = [
            ['Gols Marcados (FT)'] + get_stats_combo(gols_pro_ft),
            ['Gols Sofridos (FT)'] + get_stats_combo(gols_con_ft),
            ['Gols Marcados (HT)'] + get_stats_combo(gols_pro_ht),
            ['Gols Sofridos (HT)'] + get_stats_combo(gols_con_ht),
            ['Cantos FT (Pro)'] + get_stats_combo(cant_pro_ft),
            ['Cantos FT (Contra)'] + get_stats_combo(cant_con_ft),
            ['Cantos HT (Pro)'] + get_stats_combo(cant_pro_ht),
            ['Cantos HT (Contra)'] + get_stats_combo(cant_con_ht),
            ['Chutes no Gol (Pro)'] + get_stats_combo(chutes_pro),
            ['Chutes no Gol (Contra)'] + get_stats_combo(chutes_con)
        ]
        return pd.DataFrame(data, columns=['Métrica', 'Média', 'Mediana', 'Moda', 'DP', 'CV'])

    col_t1, col_t2 = st.columns(2)
    with col_t1:
        st.markdown(f"**{m_sel}**")
        tab_m = preparar_tabela_tecnica(df_m_last, m_sel)
        st.table(tab_m.style.format({c: "{:.2f}" for c in tab_m.columns if c != 'Métrica'}))

    with col_t2:
        st.markdown(f"**{v_sel}**")
        tab_v = preparar_tabela_tecnica(df_v_last, v_sel)
        st.table(tab_v.style.format({c: "{:.2f}" for c in tab_v.columns if c != 'Métrica'}))
