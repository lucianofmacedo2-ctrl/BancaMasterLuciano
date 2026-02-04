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
                stats[m]['P'] += 3
                stats[m]['V'] += 1
            elif gm == gv:
                stats[m]['P'] += 1
                stats[v]['P'] += 1
            else:
                stats[v]['P'] += 3
                stats[v]['V'] += 1
        
        tab = pd.DataFrame.from_dict(stats, orient='index').reset_index().rename(columns={'index':'Time'})
        tab = tab.sort_values(by=['P', 'V', 'SG'], ascending=False).reset_index(drop=True)
        tab['Pos'] = tab.index + 1
        return tab

    # Execução do cálculo
    tabela_liga = calcular_posicoes(df_l)
    
    try:
        # Busca a posição exata de cada time
        pos_m = tabela_liga[tabela_liga['Time'] == m_sel]['Pos'].values[0]
        pos_v = tabela_liga[tabela_liga['Time'] == v_sel]['Pos'].values[0]
        dif = abs(pos_m - pos_v)

        # 5. ESTILO E EXIBIÇÃO DOS CARDS (Centralizados e Escuros)
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
            /* Garante que o container da métrica também centralize */
            [data-testid="stMetric"] {
                text-align: center;
                display: flex;
                flex-direction: column;
                align-items: center;
            }
            </style>
            """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric(label=f"Posição {m_sel}", value=f"{pos_m}º")
        with c2:
            st.metric(label=f"Posição {v_sel}", value=f"{pos_v}º")
        with c3:
            st.metric(label="Diferença de Tabela", value=f"{dif} pos.")
            
    except Exception as e:
        st.info("Aguardando seleção de times para calcular posições.")
