import streamlit as st
import pandas as pd

def mostrar_termometro(df):
    st.title("🔥 Termômetro de Ligas")
    
    if df.empty:
        st.error("Base de dados vazia.")
        return

    # Garantir que as colunas numéricas estão prontas
    cols_analise = ['Total_Gols_FT', 'Total_Corners', 'Total_Corners_HT', 'Total_Gols_HT']
    for col in cols_analise:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

    # Criar coluna Ambas Marcam
    df['BTTS'] = ((df['Gols_Mandante_FT'] > 0) & (df['Gols_Visitante_FT'] > 0)).astype(int)

    # Agrupamento por Liga
    stats_liga = df.groupby('Liga').agg({
        'Total_Gols_FT': 'mean',
        'Total_Corners': 'mean',
        'Total_Gols_HT': 'mean',
        'BTTS': 'mean',
        'Mandante': 'count' # Representa o total de jogos
    }).rename(columns={'Mandante': 'Jogos'})

    # Filtro de ligas com amostragem mínima (ex: 10 jogos)
    stats_liga = stats_liga[stats_liga['Jogos'] >= 10]

    st.markdown("### 🏆 Top 10 Ligas por Mercado")
    
    t1, t2 = st.columns(2)
    
    with t1:
        st.subheader("🚩 Ligas com mais Cantos (FT)")
        top_cantos = stats_liga.sort_values('Total_Corners', ascending=False).head(10)
        st.dataframe(top_cantos[['Total_Corners', 'Jogos']], column_config={
            "Total_Corners": st.column_config.NumberColumn("Média Cantos", format="%.2f")
        })

        st.subheader("🤝 Ligas com mais Ambas Marcam")
        top_btts = stats_liga.sort_values('BTTS', ascending=False).head(10)
        st.dataframe(top_btts[['BTTS', 'Jogos']], column_config={
            "BTTS": st.column_config.ProgressColumn("BTTS %", format="%.2f", min_value=0, max_value=1)
        })

    with t2:
        st.subheader("⚽ Ligas com mais Gols (FT)")
        top_gols = stats_liga.sort_values('Total_Gols_FT', ascending=False).head(10)
        st.dataframe(top_gols[['Total_Gols_FT', 'Jogos']], column_config={
            "Total_Gols_FT": st.column_config.NumberColumn("Média Gols", format="%.2f")
        })

        st.subheader("⏱️ Ligas com mais Gols no HT")
        top_ht = stats_liga.sort_values('Total_Gols_HT', ascending=False).head(10)
        st.dataframe(top_ht[['Total_Gols_HT', 'Jogos']], column_config={
            "Total_Gols_HT": st.column_config.NumberColumn("Média Gols HT", format="%.2f")
        })

    st.info("💡 Apenas ligas com no mínimo 10 jogos registrados aparecem neste ranking para garantir a qualidade dos dados.")
