import streamlit as st
import pandas as pd

URL_RAW = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/refs/heads/main/jogos_do_dia.csv"

def mostrar_jogos():
    st.title("📅 Agenda de Jogos")

    # --- CSS REFINADO E FINO ---
    st.markdown("""
        <style>
        /* Cabeçalho da Liga mais fino */
        .header-liga {
            background-color: rgba(128, 128, 128, 0.1);
            padding: 5px 12px;
            border-radius: 4px;
            margin-top: 15px;
            margin-bottom: 5px;
            border-left: 4px solid #28a745;
        }
        .header-liga h4 {
            margin: 0;
            font-size: 16px !important;
            font-weight: bold;
            text-transform: uppercase;
        }
        /* Linha do jogo mais compacta */
        .linha-jogo {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 4px 0px;
            border-bottom: 1px solid rgba(128, 128, 128, 0.1);
        }
        .hora-texto {
            font-size: 14px;
            font-weight: bold;
            color: #28a745;
            margin-right: 15px;
        }
        .times-texto {
            font-size: 15px;
            font-weight: 500;
        }
        .vs-sep {
            color: #888;
            font-size: 12px;
            margin: 0 8px;
        }
        .odd-container {
            display: flex;
            gap: 4px;
        }
        .odd-box {
            background-color: rgba(40, 167, 69, 0.1);
            color: #28a745;
            border: 1px solid rgba(40, 167, 69, 0.3);
            border-radius: 3px;
            width: 42px;
            text-align: center;
            font-size: 13px;
            font-weight: bold;
            padding: 2px 0;
        }
        </style>
    """, unsafe_allow_html=True)

    try:
        @st.cache_data(ttl=60)
        def carregar_dados(url):
            return pd.read_csv(url, encoding='utf-8')

        df = carregar_dados(URL_RAW)

        if df.empty:
            st.info("Nenhum jogo disponível.")
            return

        # Agrupar por liga
        ligas = df['competicao'].unique()

        for liga in ligas:
            # Cabeçalho Fino
            st.markdown(f"<div class='header-liga'><h4>🏆 {liga}</h4></div>", unsafe_allow_html=True)
            
            df_liga = df[df['competicao'] == liga]
            
            for _, row in df_liga.iterrows():
                # Criando as colunas para o layout horizontal
                col_dados, col_odds = st.columns([4, 1.5])
                
                with col_dados:
                    # Hora + Confronto na mesma linha
                    st.markdown(f"""
                        <div class='linha-jogo'>
                            <div>
                                <span class='hora-texto'>{row['hora']}</span>
                                <span class='times-texto'>{row['mandante']}</span>
                                <span class='vs-sep'>vs</span>
                                <span class='times-texto'>{row['visitante']}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col_odds:
                    # Quadrinhos de Odds alinhados à direita
                    if str(row['odd_1']) != "-":
                        st.markdown(f"""
                            <div class='odd-container'>
                                <div class='odd-box'>{row['odd_1']}</div>
                                <div class='odd-box'>{row['odd_x']}</div>
                                <div class='odd-box'>{row['odd_2']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='text-align:right; font-size:12px; color:#888;'>{row['fase']}</div>", unsafe_allow_html=True)

    except Exception as e:
        st.error("Erro ao carregar agenda.")

if __name__ == "__main__":
    mostrar_jogos()
