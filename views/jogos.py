import streamlit as st
import pandas as pd

URL_RAW = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/refs/heads/main/jogos_do_dia.csv"

def mostrar_jogos():
    # --- ESTILO CSS PARA FONTES MAIORES E LAYOUT ---
    st.markdown("""
        <style>
        .titulo-jogo {
            font-size: 24px !important;
            font-weight: bold !important;
            color: #FFFFFF;
            margin-bottom: 0px;
        }
        .info-liga {
            font-size: 14px !important;
            color: #AAAAAA;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .hora-jogo {
            font-size: 20px !important;
            font-weight: bold;
            color: #00FF00; /* Verde para destacar o horário */
        }
        .odd-box {
            background-color: #262730;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            border: 1px solid #444;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("📅 Agenda de Jogos")
    st.markdown("---")

    try:
        @st.cache_data(ttl=60)
        def carregar_dados_github(url):
            return pd.read_csv(url, encoding='utf-8')

        df = carregar_dados_github(URL_RAW)

        for index, row in df.iterrows():
            with st.container(border=True):
                # Coluna 1: Horário e Data | Coluna 2: Times | Coluna 3: Odds e Botão
                col_tempo, col_confronto, col_acao = st.columns([1.2, 3, 2])

                with col_tempo:
                    st.markdown(f"<p class='hora-jogo'>{row['hora']}</p>", unsafe_allow_html=True)
                    st.caption(f"📅 {row['data']}")
                    st.markdown(f"<p class='info-liga'>{row['competicao']}</p>", unsafe_allow_html=True)

                with col_confronto:
                    st.markdown(f"<p class='titulo-jogo'>{row['mandante']}</p>", unsafe_allow_html=True)
                    st.markdown("<p style='margin: -5px 0; color: #666;'>vs</p>", unsafe_allow_html=True)
                    st.markdown(f"<p class='titulo-jogo'>{row['visitante']}</p>", unsafe_allow_html=True)

                with col_acao:
                    # Se houver odds, mostra em destaque
                    if str(row['odd_1']) != "-":
                        st.markdown(f"""
                            <div class='odd-box'>
                                <span style='color: #888; font-size: 12px;'>ODDS (1 X 2)</span><br>
                                <b style='font-size: 16px; color: #FFA500;'>{row['odd_1']} &nbsp; {row['odd_x']} &nbsp; {row['odd_2']}</b>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.write(f"📌 {row['fase']}")
                    
                    st.write("") # Espaço
                    if st.button("📊 Analisar Agora", key=f"analisar_{index}", use_container_width=True):
                        st.session_state.time_casa_scout = row['mandante']
                        st.session_state.time_fora_scout = row['visitante']
                        st.toast(f"Análise preparada: {row['mandante']}!", icon="✅")

    except Exception as e:
        st.error("Erro ao carregar a agenda.")
        st.info("Dica: Verifique se o arquivo CSV no GitHub está correto.")

if __name__ == "__main__":
    mostrar_jogos()
