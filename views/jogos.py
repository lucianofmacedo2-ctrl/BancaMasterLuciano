import streamlit as st
import pandas as pd

URL_RAW = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/refs/heads/main/jogos_do_dia.csv"

def mostrar_jogos():
    st.title("📅 Agenda de Jogos por Liga")
    st.markdown("---")

    # Estilo CSS para melhorar a aparência das tabelas e botões
    st.markdown("""
        <style>
        .stTable {
            font-size: 16px !important;
        }
        .header-liga {
            background-color: #1E1E1E;
            padding: 10px;
            border-radius: 5px;
            margin-top: 20px;
            border-left: 5px solid #28a745;
            color: white;
        }
        .odd-verde {
            color: #28a745;
            font-weight: bold;
            background-color: rgba(40, 167, 69, 0.1);
            padding: 2px 6px;
            border-radius: 4px;
        }
        </style>
    """, unsafe_allow_html=True)

    try:
        @st.cache_data(ttl=60)
        def carregar_dados(url):
            return pd.read_csv(url, encoding='utf-8')

        df = carregar_dados(URL_RAW)

        if df.empty:
            st.info("Nenhum jogo disponível no momento.")
            return

        # 1. Obter lista de ligas únicas e ordenar
        ligas = sorted(df['competicao'].unique())

        for liga in ligas:
            # Criar um container visual para a Liga
            st.markdown(f"<div class='header-liga'><h3>🏆 {liga}</h3></div>", unsafe_allow_html=True)
            
            # Filtrar jogos apenas desta liga
            df_liga = df[df['competicao'] == liga].copy()
            
            # Preparar as colunas para exibição na tabela
            for index, row in df_liga.iterrows():
                # Criar uma linha com colunas para simular a tabela
                col_data, col_confronto, col_odds, col_acao = st.columns([1.5, 4, 2, 1.5])
                
                with col_data:
                    st.write(f"🕒 **{row['hora']}**")
                    st.caption(f"{row['data']}")
                
                with col_confronto:
                    # Exibe Mandante vs Visitante em uma linha
                    st.markdown(f"**{row['mandante']}** <span style='color:gray'>vs</span> **{row['visitante']}**", unsafe_allow_html=True)
                    st.caption(f"Fase: {row['fase']}")
                
                with col_odds:
                    if str(row['odd_1']) != "-":
                        # Exibe as odds formatadas
                        st.markdown(f"<span class='odd-verde'>{row['odd_1']}</span> | <span class='odd-verde'>{row['odd_x']}</span> | <span class='odd-verde'>{row['odd_2']}</span>", unsafe_allow_html=True)
                    else:
                        st.write("-")
                
                with col_acao:
                    # Botão de ação
                    if st.button("Analisar", key=f"btn_{index}", use_container_width=True):
                        st.session_state.time_casa_scout = row['mandante']
                        st.session_state.time_fora_scout = row['visitante']
                        st.toast(f"Análise de {row['mandante']} enviada!", icon="⚽")
            
            st.markdown("---") # Linha divisória entre ligas

    except Exception as e:
        st.error("Erro ao carregar e organizar as tabelas.")
        st.exception(e)

if __name__ == "__main__":
    mostrar_jogos()
