import streamlit as st
import pandas as pd

URL_RAW = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/refs/heads/main/jogos_do_dia.csv"

def mostrar_jogos():
    # --- ESTILO CSS CORRIGIDO (ADAPTÁVEL) ---
    st.markdown("""
        <style>
        /* Removido a cor fixa branca para os nomes se adaptarem ao tema */
        .titulo-jogo {
            font-size: 22px !important;
            font-weight: bold !important;
            line-height: 1.2;
            margin: 5px 0px;
        }
        .info-liga {
            font-size: 13px !important;
            color: #888888;
            text-transform: uppercase;
            font-weight: 500;
        }
        .hora-jogo {
            font-size: 20px !important;
            font-weight: bold;
            color: #28a745; /* Verde padrão que funciona em ambos os fundos */
        }
        .odd-box {
            background-color: rgba(128, 128, 128, 0.1); /* Fundo levemente cinza transparente */
            padding: 8px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid rgba(128, 128, 128, 0.2);
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
                col_tempo, col_confronto, col_acao = st.columns([1.2, 3, 2])

                with col_tempo:
                    st.markdown(f"<p class='hora-jogo'>{row['hora']}</p>", unsafe_allow_html=True)
                    st.caption(f"📅 {row['data']}")
                    st.markdown(f"<p class='info-liga'>{row['competicao']}</p>", unsafe_allow_html=True)

                with col_confronto:
                    # Usando divs simples para o texto respeitar a cor padrão do Streamlit
                    st.markdown(f"<div class='titulo-jogo'>{row['mandante']}</div>", unsafe_allow_html=True)
                    st.markdown("<div style='font-size: 14px; opacity: 0.6;'>vs</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='titulo-jogo'>{row['visitante']}</div>", unsafe_allow_html=True)

                with col_acao:
                    if str(row['odd_1']) != "-":
                        st.markdown(f"""
                            <div class='odd-box'>
                                <span style='font-size: 11px; opacity: 0.8;'>ODDS</span><br>
                                <b style='color: #e67e22;'>{row['odd_1']} &nbsp; {row['odd_x']} &nbsp; {row['odd_2']}</b>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.write(f"📌 {row['fase']}")
                    
                    st.write("") # Espaço
                    if st.button("📊 Analisar", key=f"analisar_{index}", use_container_width=True):
                        st.session_state.time_casa_scout = row['mandante']
                        st.session_state.time_fora_scout = row['visitante']
                        st.toast(f"Times enviados: {row['mandante']}!", icon="⚽")

    except Exception as e:
        st.error("Erro ao carregar a agenda.")

if __name__ == "__main__":
    mostrar_jogos()
