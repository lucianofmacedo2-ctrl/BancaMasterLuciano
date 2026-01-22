import streamlit as st
import pandas as pd

URL_RAW = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/refs/heads/main/jogos_do_dia.csv"

def mostrar_jogos():
    # --- CSS PARA LAYOUT IGUAL À IMAGEM ---
    st.markdown("""
        <style>
        .jogo-container {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 15px;
            border-bottom: 1px solid rgba(128, 128, 128, 0.2);
            background-color: transparent;
        }
        .time-texto {
            font-size: 18px !important;
            font-weight: 500;
            margin: 0 10px;
        }
        .hora-texto {
            font-size: 16px;
            color: #28a745;
            font-weight: bold;
            min-width: 60px;
        }
        .data-texto {
            font-size: 12px;
            color: #888;
            min-width: 50px;
        }
        .odd-item {
            display: inline-block;
            width: 45px;
            background-color: rgba(40, 167, 69, 0.1);
            color: #28a745;
            border: 1px solid #28a745;
            border-radius: 4px;
            text-align: center;
            padding: 5px 0;
            font-weight: bold;
            font-size: 14px;
            margin-left: 5px;
        }
        .vs-texto {
            color: #888;
            font-size: 14px;
        }
        /* Ajuste para o botão sumir e parecer apenas um clique na linha */
        .stButton button {
            background-color: transparent !important;
            border: 1px solid rgba(128, 128, 128, 0.3) !important;
            height: 35px;
        }
        </style>
    """, unsafe_allow_html=True)

    st.title("📅 Agenda de Jogos")

    try:
        @st.cache_data(ttl=60)
        def carregar_dados(url):
            return pd.read_csv(url, encoding='utf-8')

        df = carregar_dados(URL_RAW)

        # Agrupar por competição para criar cabeçalhos como na imagem
        competicoes = df['competicao'].unique()

        for comp in competicoes:
            st.markdown(f"### 🏆 {comp}")
            df_comp = df[df['competicao'] == comp]
            
            for index, row in df_comp.iterrows():
                # Criamos o layout de linha única
                col1, col2, col3, col4 = st.columns([1, 4, 2, 1.5])
                
                with col1:
                    st.markdown(f"<span class='data-texto'>{row['data']}</span> <span class='hora-texto'>{row['hora']}</span>", unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"<span class='time-texto'>{row['mandante']}</span> <span class='vs-texto'>vs</span> <span class='time-texto'>{row['visitante']}</span>", unsafe_allow_html=True)
                
                with col3:
                    if str(row['odd_1']) != "-":
                        st.markdown(f"""
                            <div style='display: flex;'>
                                <div class='odd-item'>{row['odd_1']}</div>
                                <div class='odd-item'>{row['odd_x']}</div>
                                <div class='odd-item'>{row['odd_2']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.caption(row['fase'])
                
                with col4:
                    if st.button("Analisar", key=f"btn_{index}", use_container_width=True):
                        st.session_state.time_casa_scout = row['mandante']
                        st.session_state.time_fora_scout = row['visitante']
                        st.toast(f"Carregando {row['mandante']}...")

    except Exception as e:
        st.error("Erro ao carregar layout.")

if __name__ == "__main__":
    mostrar_jogos()
