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
