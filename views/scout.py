import streamlit as st
import pandas as pd
import numpy as np

def mostrar_scout(df):
    st.title("🔎 Scout Profissional - Master Luciano")
    
    # Limpeza de nomes de colunas
    df.columns = [c.strip() for c in df.columns]

    # --- FILTROS INICIAIS ---
    col_f1, col_f2 = st.columns(2)
    
    # 1. Seleção da Liga
    lista_ligas = sorted(df['Liga'].unique())
    liga_sel = col_f1.selectbox("1º Selecione a Liga", lista_ligas)
    
    # Filtrar o dataframe pela liga para carregar os times dela
    df_l = df[df['Liga'] == liga_sel].copy()

    # 2. Seleção dos Clubes
    lista_times = sorted(df_l['Mandante'].unique())
    m_sel = col_f1.selectbox("2º Time Mandante", lista_times)
    v_sel = col_f2.selectbox("3º Time Visitante", [t for t in lista_times if t != m_sel])

    # 3. Amostragem (Sidebar)
    n_jogos = st.sidebar.slider("Amostragem de Jogos", 5, 50, 10)
    
    st.write(f"### Analisando: {m_sel} vs {v_sel}")
    st.write(f"Liga: {liga_sel} | Últimos {n_jogos} jogos")
