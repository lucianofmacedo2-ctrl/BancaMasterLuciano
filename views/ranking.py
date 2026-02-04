import streamlit as st
import pandas as pd
import numpy as np

def mostrar_ranking(df):
    st.markdown("## 🏆 Ranking de Ligas")
    st.write("Compare o desempenho das ligas para encontrar as melhores oportunidades.")

    # 1. Limpeza e Preparação
    df.columns = [c.strip() for c in df.columns]
    
    # Injeção de CSS para centralizar tudo
    st.markdown("""
        <style>
        [data-testid="stTable"] td, [data-testid="stTable"] th {
            text-align: center !important;
            vertical-align: middle !important;
        }
        </style>
        """, unsafe_allow_html=True)

    # 2. SELEÇÃO DE TEMPORADA E MERCADO
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        # Filtro de Temporada
        opcoes_temp = ["Histórico Completo", "Temporada Atual (25/26)"]
        temp_sel = st.selectbox("📅 Período de Análise", opcoes_temp)
    
    with col_f2:
        # Filtro de Mercado
        opcoes_mercado = [
            "Over 0.5 FT", "Over 1.5 FT", "Over 2.5 FT", "Over 3.5 FT",
            "Over 0.5 HT", "BTTS FT", "Cantos +8.5", "Cantos +9.5", "Cantos +10.5"
        ]
        mercado_sel = st.selectbox("🎯 Mercado para Rankear", opcoes_mercado)

    # --- PROCESSAMENTO DOS DADOS ---
    def calcular_stats_ligas(df_input, periodo):
        df_proc = df_input.copy()
        
        # Mapeamento Dinâmico de Colunas (Evita o KeyError)
        col_cn_h = 'Corners_H' if 'Corners_H' in df_proc.columns else 'Cantos_Mandante'
        col_cn_a = 'Corners_A' if 'Corners_A' in df_proc.columns else 'Cantos_Visitante'
        
        # Filtro de Temporada
        if periodo == "Temporada Atual (25/26)":
            if 'Season' in df_proc.columns:
                df_proc = df_proc[df_proc['Season'].astype(str).str.contains('25|26')]
            else:
                # Caso não tenha a coluna Season, tenta pela Data
                if 'Data' in df_proc.columns:
                    df_proc['Data'] = pd.to_datetime(df_proc['Data'], errors='coerce')
                    df_proc = df_proc[df_proc['Data'] >= '2025-07-01']

        # Cálculos de base com proteção contra colunas ausentes
        df_proc['Total_FT'] = df_proc['Gols_Mandante_FT'] + df_proc['Gols_Visitante_FT']
        df_proc['Total_HT'] = df_proc['Gols_Mandante_HT'] + df_proc['Gols_Visitante_HT']
        df_proc['BTTS'] = (df_proc['Gols_Mandante_FT'] > 0) & (df_proc['Gols_Visitante_FT'] > 0)
        
        # Cálculo de Cantos usando o mapeamento dinâmico
        if col_cn_h in df_proc.columns and col_cn_a in df_proc.columns:
            df_proc['Total_Cantos'] = df_proc[col_cn_h] + df_proc[col_cn_a]
        else:
            df_proc['Total_Cantos'] = 0 # Valor padrão caso não existam colunas de cantos

        grupos = df_proc.groupby('Liga')
        ranking_data = []
        
        for liga, dados in grupos:
            total_jogos = len(dados)
            if total_jogos < 5: continue 

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

    df_ranking = calcular_stats_ligas(df, temp_sel)

    if not df_ranking.empty:
        df_ranking = df_ranking.sort_values(by="📈 Incidência", ascending=False).reset_index(drop=True)
        df_ranking.index += 1 
        
        st.divider()
        st.markdown(f"### Top Ligas - {mercado_sel} ({temp_sel})")
        
        def color_incidencia(val):
            color = 'red' if val < 40 else 'orange' if val < 70 else 'green'
            return f'color: {color}; font-weight: bold; text-align: center;'

        st.table(
            df_ranking.style.format({"📈 Incidência": "{:.2f}%"})
            .applymap(color_incidencia, subset=['📈 Incidência'])
            .set_properties(**{'text-align': 'center'})
        )
    else:
        st.warning(f"Sem dados suficientes para {temp_sel}.")
