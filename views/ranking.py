import streamlit as st
import pandas as pd

def mostrar_ranking(df):
    st.markdown("## 🏆 Ranking de Ligas")
    st.write("Compare o desempenho das ligas para encontrar as melhores oportunidades de mercado.")

    # 1. Limpeza de colunas
    df.columns = [c.strip() for c in df.columns]
    
    # 2. SELEÇÃO DO MERCADO
    opcoes_mercado = [
        "Over 0.5 FT", "Over 1.5 FT", "Over 2.5 FT", "Over 3.5 FT",
        "Over 0.5 HT", "BTTS FT", "Cantos +8.5", "Cantos +9.5", "Cantos +10.5"
    ]
    mercado_sel = st.selectbox("🎯 Selecione o Mercado para Rankear", opcoes_mercado)

    # --- PROCESSAMENTO DOS DADOS ---
    def calcular_stats_ligas(df_input):
        # Criar colunas de suporte
        df_input = df_input.copy()
        df_input['Total_FT'] = df_input['Gols_Mandante_FT'] + df_input['Gols_Visitante_FT']
        df_input['Total_HT'] = df_input['Gols_Mandante_HT'] + df_input['Gols_Visitante_HT']
        df_input['BTTS'] = (df_input['Gols_Mandante_FT'] > 0) & (df_input['Gols_Visitante_FT'] > 0)
        df_input['Total_Cantos'] = df_input['Corners_H'] + df_input['Corners_A']

        # Agrupar por Liga
        grupos = df_input.groupby('Liga')
        
        ranking_data = []
        for liga, dados in grupos:
            total_jogos = len(dados)
            if total_jogos < 5: continue # Ignora ligas com pouquíssimos jogos

            # Dicionário de cálculos
            stats = {
                "Over 0.5 FT": (dados['Total_FT'] > 0.5).mean(),
                "Over 1.5 FT": (dados['Total_FT'] > 1.5).mean(),
                "Over 2.5 FT": (dados['Total_FT'] > 2.5).mean(),
                "Over 3.5 FT": (dados['Total_FT'] > 3.5).mean(),
                "Over 0.5 HT": (dados['Total_HT'] > 0.5).mean(),
                "BTTS FT": dados['BTTS'].mean(),
                "Cantos +8.5": (dados['Total_Cantos'] > 8.5).mean(),
                "Cantos +9.5": (dados['Total_Cantos'] > 9.5).mean(),
                "Cantos +10.5": (dados['Total_Cantos'] > 10.5).mean(),
            }

            ranking_data.append({
                "🏆 Liga": liga,
                "📊 Jogos": total_jogos,
                "📈 Incidência": stats[mercado_sel] * 100
            })

        return pd.DataFrame(ranking_data)

    df_ranking = calcular_stats_ligas(df)

    if not df_ranking.empty:
        # Ordenar e formatar
        df_ranking = df_ranking.sort_values(by="📈 Incidência", ascending=False).reset_index(drop=True)
        df_ranking.index += 1 # Começar ranking do 1
        
        # Exibição
        st.divider()
        st.markdown(f"### Top Ligas - {mercado_sel}")
        
        # Estilização para destacar as melhores ligas (acima de 75% em verde, etc)
        def color_incidencia(val):
            color = 'red' if val < 40 else 'orange' if val < 70 else 'green'
            return f'color: {color}; font-weight: bold'

        st.table(df_ranking.style.format({"📈 Incidência": "{:.2f}%"}).applymap(color_incidencia, subset=['📈 Incidência']))
    else:
        st.warning("Não há dados suficientes para gerar o ranking.")
