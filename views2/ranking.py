import streamlit as st
import pandas as pd
import numpy as np
from scipy.stats import poisson

def mostrar_ranking(df):
    st.markdown("## 🏆 Ranking de Ligas & Times - Sistema 2")
    st.write("Compare o desempenho das ligas e clubes com probabilidades estimadas para o Sistema 2.")

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
        opcoes_temp = ["Histórico Completo", "Temporada Atual (25/26)"]
        temp_sel = st.selectbox("📅 Período de Análise", opcoes_temp, key="temp_rank_2")
    
    with col_f2:
        opcoes_mercado = [
            "Over 0.5 FT", "Over 1.5 FT", "Over 2.5 FT", "Over 3.5 FT",
            "Over 0.5 HT", "BTTS FT", "Cantos +8.5", "Cantos +9.5", "Cantos +10.5"
        ]
        mercado_sel = st.selectbox("🎯 Mercado para Rankear", opcoes_mercado, key="mercado_rank_2")

    # --- FUNÇÃO DE PROCESSAMENTO ---
    def processar_dados_base(df_input, periodo):
        df_proc = df_input.copy()
        col_cn_h = 'Corners_H' if 'Corners_H' in df_proc.columns else 'Cantos_Mandante'
        col_cn_a = 'Corners_A' if 'Corners_A' in df_proc.columns else 'Cantos_Visitante'
        
        if periodo == "Temporada Atual (25/26)":
            if 'Season' in df_proc.columns:
                df_proc = df_proc[df_proc['Season'].astype(str).str.contains('25|26')]
            elif 'Data' in df_proc.columns:
                df_proc['Data'] = pd.to_datetime(df_proc['Data'], errors='coerce')
                df_proc = df_proc[df_proc['Data'] >= '2025-07-01']

        df_proc['Total_FT'] = df_proc['Gols_Mandante_FT'] + df_proc['Gols_Visitante_FT']
        df_proc['Total_HT'] = df_proc['Gols_Mandante_HT'] + df_proc['Gols_Visitante_HT']
        df_proc['BTTS'] = (df_proc['Gols_Mandante_FT'] > 0) & (df_proc['Gols_Visitante_FT'] > 0)
        
        if col_cn_h in df_proc.columns and col_cn_a in df_proc.columns:
            df_proc['Total_Cantos'] = df_proc[col_cn_h] + df_proc[col_cn_a]
        else:
            df_proc['Total_Cantos'] = 0
            
        return df_proc, col_cn_h, col_cn_a

    df_base, c_h, c_a = processar_dados_base(df, temp_sel)

    # --- FUNÇÃO AUXILIAR POISSON ---
    def prob_poisson(media, linha):
        # Calcula 1 - Probabilidade acumulada até a linha (Ex: 1 - P(X<=8) = P(X>8.5))
        return (1 - poisson.cdf(linha, media)) * 100

    # --- 3. RANKING DE LIGAS ---
    def calcular_ranking_ligas(df_p):
        grupos = df_p.groupby('Liga')
        ranking_data = []
        for liga, dados in grupos:
            if len(dados) < 5: continue 
            
            media_cantos_liga = dados['Total_Cantos'].mean()
            
            stats = {
                "Over 0.5 FT": (dados['Total_FT'] > 0.5).mean() * 100,
                "Over 1.5 FT": (dados['Total_FT'] > 1.5).mean() * 100,
                "Over 2.5 FT": (dados['Total_FT'] > 2.5).mean() * 100,
                "Over 3.5 FT": (dados['Total_FT'] > 3.5).mean() * 100,
                "Over 0.5 HT": (dados['Total_HT'] > 0.5).mean() * 100,
                "BTTS FT": dados['BTTS'].mean() * 100,
                "Cantos +8.5": (dados['Total_Cantos'] > 8.5).mean() * 100,
                "Cantos +9.5": (dados['Total_Cantos'] > 9.5).mean() * 100,
                "Cantos +10.5": (dados['Total_Cantos'] > 10.5).mean() * 100,
            }
            
            ranking_data.append({
                "🏆 Liga": liga, 
                "📊 Jogos": len(dados), 
                "📈 Incidência": stats[mercado_sel],
                "Prob 8.5": prob_poisson(media_cantos_liga, 8),
                "Prob 9.5": prob_poisson(media_cantos_liga, 9),
                "Prob 10.5": prob_poisson(media_cantos_liga, 10)
            })
        return pd.DataFrame(ranking_data)

    df_rank_ligas = calcular_ranking_ligas(df_base)

    def color_incidencia(val):
        color = 'red' if val < 40 else 'orange' if val < 70 else 'green'
        return f'color: {color}; font-weight: bold; text-align: center;'

    if not df_rank_ligas.empty:
        df_rank_ligas = df_rank_ligas.sort_values(by="📈 Incidência", ascending=False).reset_index(drop=True)
        df_rank_ligas.index += 1 
        
        st.divider()
        st.markdown(f"### Top Ligas - {mercado_sel}")
        
        st.table(df_rank_ligas.style.format({
            "📈 Incidência": "{:.2f}%",
            "Prob 8.5": "{:.2f}%",
            "Prob 9.5": "{:.2f}%",
            "Prob 10.5": "{:.2f}%"
        }).applymap(color_incidencia, subset=['📈 Incidência']))
    
    # --- 4. RANKING DE TIMES POR LIGA ---
    st.divider()
    st.markdown("### ⚽ Ranking de Times por Liga")
    
    lista_ligas_filtro = sorted(df_base['Liga'].unique())
    liga_escolhida = st.selectbox("Escolha a Liga para detalhar", lista_ligas_filtro, key="liga_detalhe_2")
    
    if liga_escolhida:
        df_liga_v = df_base[df_base['Liga'] == liga_escolhida]
        times = sorted(pd.concat([df_liga_v['Mandante'], df_liga_v['Visitante']]).unique())
        ranking_times = []
        
        for t in times:
            df_t = df_liga_v[(df_liga_v['Mandante'] == t) | (df_liga_v['Visitante'] == t)]
            if len(df_t) < 3: continue
            
            media_cantos_time = df_t['Total_Cantos'].mean()
            
            stats_t = {
                "Over 0.5 FT": (df_t['Total_FT'] > 0.5).mean() * 100,
                "Over 1.5 FT": (df_t['Total_FT'] > 1.5).mean() * 100,
                "Over 2.5 FT": (df_t['Total_FT'] > 2.5).mean() * 100,
                "Over 3.5 FT": (df_t['Total_FT'] > 3.5).mean() * 100,
                "Over 0.5 HT": (df_t['Total_HT'] > 0.5).mean() * 100,
                "BTTS FT": df_t['BTTS'].mean() * 100,
                "Cantos +8.5": (df_t['Total_Cantos'] > 8.5).mean() * 100,
                "Cantos +9.5": (df_t['Total_Cantos'] > 9.5).mean() * 100,
                "Cantos +10.5": (df_t['Total_Cantos'] > 10.5).mean() * 100,
            }
            
            ranking_times.append({
                "Time": t,
                "Jogos": len(df_t),
                "Incidência": stats_t[mercado_sel],
                "Prob 8.5": prob_poisson(media_cantos_time, 8),
                "Prob 9.5": prob_poisson(media_cantos_time, 9),
                "Prob 10.5": prob_poisson(media_cantos_time, 10)
            })
        
        df_rank_times = pd.DataFrame(ranking_times)
        if not df_rank_times.empty:
            df_rank_times = df_rank_times.sort_values(by="Incidência", ascending=False).reset_index(drop=True)
            df_rank_times.index += 1
            st.table(df_rank_times.style.format({
                "Incidência": "{:.2f}%",
                "Prob 8.5": "{:.2f}%",
                "Prob 9.5": "{:.2f}%",
                "Prob 10.5": "{:.2f}%"
            }).applymap(color_incidencia, subset=['Incidência']))
        else:
            st.warning("Dados insuficientes para os times desta liga no Sistema 2.")
