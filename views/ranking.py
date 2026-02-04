import streamlit as st
import pandas as pd
import numpy as np

def mostrar_ranking(df):
    st.markdown("## 🏆 Ranking de Ligas & Times")
    st.write("Compare o desempenho das ligas e clubes para encontrar as melhores oportunidades.")

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
        temp_sel = st.selectbox("📅 Período de Análise", opcoes_temp)
    
    with col_f2:
        opcoes_mercado = [
            "Over 0.5 FT", "Over 1.5 FT", "Over 2.5 FT", "Over 3.5 FT",
            "Over 0.5 HT", "BTTS FT", "Cantos +8.5", "Cantos +9.5", "Cantos +10.5"
        ]
        mercado_sel = st.selectbox("🎯 Mercado para Rankear", opcoes_mercado)

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

    # --- 3. RANKING DE LIGAS (LÓGICA EXISTENTE) ---
    def calcular_ranking_ligas(df_p):
        grupos = df_p.groupby('Liga')
        ranking_data = []
        for liga, dados in grupos:
            if len(dados) < 5: continue 
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
            ranking_data.append({"🏆 Liga": liga, "📊 Jogos": len(dados), "📈 Incidência": stats[mercado_sel] * 100})
        return pd.DataFrame(ranking_data)

    df_rank_ligas = calcular_ranking_ligas(df_base)

    if not df_rank_ligas.empty:
        df_rank_ligas = df_rank_ligas.sort_values(by="📈 Incidência", ascending=False).reset_index(drop=True)
        df_rank_ligas.index += 1 
        
        st.divider()
        st.markdown(f"### Top Ligas - {mercado_sel}")
        
        def color_incidencia(val):
            color = 'red' if val < 40 else 'orange' if val < 70 else 'green'
            return f'color: {color}; font-weight: bold; text-align: center;'

        st.table(df_rank_ligas.style.format({"📈 Incidência": "{:.2f}%"}).applymap(color_incidencia, subset=['📈 Incidência']))
    
    # --- 4. NOVO: RANKING DE TIMES POR LIGA ---
    st.divider()
    st.markdown("### ⚽ Ranking de Times por Liga")
    st.write("Selecione uma liga para ver o desempenho individual dos clubes.")
    
    lista_ligas_filtro = sorted(df_base['Liga'].unique())
    liga_escolhida = st.selectbox("Escolha a Liga para detalhar", lista_ligas_filtro)
    
    if liga_escolhida:
        df_liga_v = df_base[df_base['Liga'] == liga_escolhida]
        times = sorted(pd.concat([df_liga_v['Mandante'], df_liga_v['Visitante']]).unique())
        ranking_times = []
        
        for t in times:
            df_t = df_liga_v[(df_liga_v['Mandante'] == t) | (df_liga_v['Visitante'] == t)]
            if len(df_t) < 3: continue
            
            stats_t = {
                "Over 0.5 FT": (df_t['Total_FT'] > 0.5).mean(),
                "Over 1.5 FT": (df_t['Total_FT'] > 1.5).mean(),
                "Over 2.5 FT": (df_t['Total_FT'] > 2.5).mean(),
                "Over 3.5 FT": (df_t['Total_FT'] > 3.5).mean(),
                "Over 0.5 HT": (df_t['Total_HT'] > 0.5).mean(),
                "BTTS FT": df_t['BTTS'].mean(),
                "Cantos +8.5": (df_t['Total_Cantos'] > 8.5).mean(),
                "Cantos +9.5": (df_t['Total_Cantos'] > 9.5).mean(),
                "Cantos +10.5": (df_t['Total_Cantos'] > 10.5).mean(),
            }
            
            ranking_times.append({
                "Time": t,
                "Jogos": len(df_t),
                "Incidência": stats_t[mercado_sel] * 100
            })
        
        df_rank_times = pd.DataFrame(ranking_times)
        if not df_rank_times.empty:
            df_rank_times = df_rank_times.sort_values(by="Incidência", ascending=False).reset_index(drop=True)
            df_rank_times.index += 1
            st.table(df_rank_times.style.format({"Incidência": "{:.2f}%"}).applymap(color_incidencia, subset=['Incidência']))
        else:
            st.warning("Dados insuficientes para os times desta liga.")
