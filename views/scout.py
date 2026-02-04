import streamlit as st
import pandas as pd
import numpy as np

def mostrar_scout(df):
    st.markdown("## 🔎 Painel de Análise")
    
    # 1. Ajuste das colunas
    df.columns = [c.strip() for c in df.columns]

    # 2. SELEÇÃO DA LIGA (Linha única para não ocupar espaço)
    lista_ligas = sorted(df['Liga'].unique())
    liga_sel = st.selectbox("🏆 Escolha a Liga", lista_ligas)
    
    # Filtro imediato da liga
    df_l = df[df['Liga'] == liga_sel].copy()

    # 3. SELEÇÃO DOS TIMES (Um abaixo do outro)
    lista_times = sorted(df_l['Mandante'].unique())
    m_sel = st.selectbox("🏠 Time da Casa", lista_times)
    
    # Filtra a lista de visitantes para não repetir o mandante
    visitantes_disponiveis = [t for t in lista_times if t != m_sel]
    v_sel = st.selectbox("🚌 Time de Fora", visitantes_disponiveis)

    # 4. CONFIGURAÇÃO (Na lateral para limpar o visual central)
    n_jogos = st.sidebar.slider("Amostragem (Últimos Jogos)", 5, 50, 10)
    
    st.divider()
    st.subheader(f"📊 {m_sel} vs {v_sel}")

# --- BLOCO: CLASSIFICAÇÃO E DIFERENÇA ---

def calcular_posicoes(df_liga, m_sel, v_sel):
    # Calcular pontos e vitórias para cada time na liga
    stats = {}
    for _, r in df_liga.iterrows():
        for t in [r['Mandante'], r['Visitante']]:
            if t not in stats: stats[t] = {'P': 0, 'V': 0, 'SG': 0}
        
        m, v = r['Mandante'], r['Visitante']
        gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
        
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

    # Criar DataFrame e Rankear
    tab = pd.DataFrame.from_dict(stats, orient='index').reset_index().rename(columns={'index':'Time'})
    tab = tab.sort_values(by=['P', 'V', 'SG'], ascending=False).reset_index(drop=True)
    tab['Pos'] = tab.index + 1
    
    # Extrair posições dos times selecionados
    pos_m = tab[tab['Time'] == m_sel]['Pos'].values[0] if m_sel in tab['Time'].values else 0
    pos_v = tab[tab['Time'] == v_sel]['Pos'].values[0] if v_sel in tab['Time'].values else 0
    
    return pos_m, pos_v

# Executar cálculo
pos_m, pos_v = calcular_posicoes(df_l, m_sel, v_sel)
dif = abs(pos_m - pos_v)

# Exibição dos Cards
c1, c2, c3 = st.columns(3)
c1.metric(f"Posição {m_sel}", f"{pos_m}º")
c2.metric(f"Posição {v_sel}", f"{pos_v}º")
c3.metric("Diferença de Tabela", f"{dif} pos.")
