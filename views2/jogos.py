import streamlit as st
import pandas as pd
from datetime import datetime

def mostrar_jogos(df):
    st.markdown("## 📅 Jogos do Dia - Sistema 2")
    
    # 1. Tratamento de Data
    df['Data'] = pd.to_datetime(df['Data'])
    
    # 2. Filtros
    col1, col2 = st.columns(2)
    with col1:
        # Chave única: sel_liga_jogos_2
        ligas = sorted(df['Liga'].unique())
        liga_sel = st.multiselect("Filtrar por Liga", ligas, key="sel_liga_jogos_2")
    
    with col2:
        # Chave única: data_jogos_2
        data_sel = st.date_input("Filtrar por Data", datetime.now(), key="data_jogos_2")

    # 3. Lógica de Filtro
    df_filtrado = df[df['Data'].dt.date == data_sel]
    if liga_sel:
        df_filtrado = df_filtrado[df_filtrado['Liga'].isin(liga_sel)]

    # 4. Exibição
    if df_filtrado.empty:
        st.warning(f"Nenhum jogo encontrado para {data_sel.strftime('%d/%m/%Y')}")
    else:
        # Selecionando colunas principais para visualização rápida
        colunas_ver = ['Liga', 'Mandante', 'Visitante', 'Odd_Mandante_FT', 'Odd_Empate_FT', 'Odd_Visitante_FT']
        st.dataframe(df_filtrado[colunas_ver], use_container_width=True, hide_index=True)

    st.info("💡 Dica: No Sistema 2, você pode cruzar estes dados com as Tabelas Dinâmicas.")
