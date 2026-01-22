import streamlit as st
import pandas as pd

# Link oficial que você enviou
URL_RAW = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/refs/heads/main/jogos_do_dia.csv"

def mostrar_jogos():
    st.header("📅 Agenda de Jogos")
    st.markdown("---")

    try:
        # Carregar dados com cache para evitar lentidão
        @st.cache_data(ttl=60) # Atualiza a cada 1 minuto
        def carregar_dados_github(url):
            # Adicionamos header para garantir que o pandas leia corretamente do GitHub
            return pd.read_csv(url, encoding='utf-8')

        df = carregar_dados_github(URL_RAW)

        if df.empty:
            st.warning("O arquivo de jogos está vazio.")
            return

        # Exibir jogos
        for index, row in df.iterrows():
            with st.container(border=True):
                # Organização visual: Info | Times | Odds | Ação
                col_info, col_times, col_odds, col_btn = st.columns([1.5, 3, 2, 1.5])

                with col_info:
                    st.caption(f"🏆 {row['competicao']}")
                    st.write(f"🕒 **{row['hora']}**")
                    st.caption(f"📅 {row['data']}")

                with col_times:
                    st.markdown(f"**{row['mandante']}**")
                    st.markdown(f"**{row['visitante']}**")

                with col_odds:
                    if str(row['odd_1']) != "-":
                        st.caption("Probabilidades")
                        st.code(f"1: {row['odd_1']} | X: {row['odd_x']} | 2: {row['odd_2']}", language=None)
                    else:
                        st.caption("Fase")
                        st.write(row.get('fase', '-'))

                with col_btn:
                    st.write("") # Espaçador
                    if st.button("Analisar 🔍", key=f"analisar_{index}", use_container_width=True):
                        # Salva no session_state para o scout.py capturar
                        st.session_state.time_casa_scout = row['mandante']
                        st.session_state.time_fora_scout = row['visitante']
                        st.success("Times enviados!")

    except Exception as e:
        st.error("Erro ao carregar agenda do GitHub.")
        st.info("Verifique se o arquivo no GitHub está com o formato CSV correto.")
        if st.checkbox("Ver detalhes do erro"):
            st.write(e)

# Executa a função
if __name__ == "__main__":
    mostrar_jogos()
