import streamlit as st
import pandas as pd

def mostrar_tabelas(df):
    st.markdown("## 📈 Tabelas Dinâmicas e Estatísticas")
    st.write("Análise profunda por Liga e por Time para identificar padrões de Over/Under.")

    # 1. Filtros de Topo
    lista_ligas = sorted(df['Liga'].unique())
    liga_sel = st.selectbox("🏆 Selecionar Liga para Análise", lista_ligas, key="tabelas_liga_sel")

    df_liga = df[df['Liga'] == liga_sel].copy()

    # --- ABA 1: CLASSIFICAÇÃO DE MÉDIAS ---
    tab1, tab2 = st.tabs(["📊 Médias por Time", "🌍 Comparativo de Ligas"])

    with tab1:
        st.subheader(f"Desempenho dos Times: {liga_sel}")
        
        # Agrupando estatísticas
        times = sorted(df_liga['Mandante'].unique())
        stats_list = []

        for time in times:
            jogos_time = df_liga[(df_liga['Mandante'] == time) | (df_liga['Visitante'] == time)]
            total_jogos = len(jogos_time)
            
            if total_jogos > 0:
                # Gols
                gols_feitos = jogos_time.apply(lambda row: row['Gols_Mandante_FT'] if row['Mandante'] == time else row['Gols_Visitante_FT'], axis=1).sum()
                gols_sofridos = jogos_time.apply(lambda row: row['Gols_Visitante_FT'] if row['Mandante'] == time else row['Gols_Mandante_FT'], axis=1).sum()
                
                # Cantos (Corners) - Verificação de colunas existentes
                col_h = 'Corners_H' if 'Corners_H' in df.columns else 'Cantos_Mandante'
                col_a = 'Corners_A' if 'Corners_A' in df.columns else 'Cantos_Visitante'
                
                cantos_pro = jogos_time.apply(lambda row: row[col_h] if row['Mandante'] == time else row[col_a], axis=1).sum()
                
                stats_list.append({
                    'Time': time,
                    'Jogos': total_jogos,
                    'Média Gols Pro': round(gols_feitos / total_jogos, 2),
                    'Média Gols Sofridos': round(gols_sofridos / total_jogos, 2),
                    'Média Gols Total': round((gols_feitos + gols_sofridos) / total_jogos, 2),
                    'Média Cantos Pro': round(cantos_pro / total_jogos, 2)
                })

        df_stats = pd.DataFrame(stats_list).sort_values(by='Média Gols Total', ascending=False)
        st.dataframe(df_stats, use_container_width=True, hide_index=True)

    with tab2:
        st.subheader("Comparativo Geral entre Ligas")
        
        # Comparando todas as ligas do CSV
        df_comp = df.groupby('Liga').agg({
            'Total_Gols_FT': 'mean',
            'Total_Gols_HT': 'mean'
        }).reset_index()
        
        # Identificando colunas de cantos para a média global
        col_cn_total = 'Total_Corners' if 'Total_Corners' in df.columns else None
        if not col_cn_total and 'Corners_H' in df.columns:
            df['Total_Corners_Calc'] = df['Corners_H'] + df['Corners_A']
            col_cn_total = 'Total_Corners_Calc'

        if col_cn_total:
            df_cn = df.groupby('Liga')[col_cn_total].mean().reset_index()
            df_comp = pd.merge(df_comp, df_cn, on='Liga')

        df_comp.columns = ['Liga', 'Média Gols FT', 'Média Gols HT', 'Média Cantos']
        st.dataframe(df_comp.sort_values(by='Média Gols FT', ascending=False), use_container_width=True, hide_index=True)

    st.divider()
    st.info("💡 Use esta tela para encontrar ligas 'Over' para seus robôs ou estratégias de backtest.")
