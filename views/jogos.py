import streamlit as st
import pandas as pd

# Substitua o link abaixo pelo link RAW do seu arquivo no GitHub
# Para obter: Abra o csv no GitHub -> Clique em "Raw" -> Copie a URL do navegador
URL_RAW = "https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPOSITORIO/main/jogos_do_dia.csv"

def mostrar_jogos():
    st.header("📅 Agenda de Jogos")
    st.markdown("---")

    try:
        # 1. Carregar os dados (adicionamos cache para não sobrecarregar o GitHub)
        @st.cache_data(ttl=600)  # Atualiza a cada 10 minutos
        def carregar_dados_github(url):
            return pd.read_csv(url)

        df = carregar_dados_github(URL_RAW)

        if df.empty:
            st.warning("Nenhum jogo listado no arquivo para hoje.")
            return

        # 2. Exibir cada jogo em um card organizado
        for index, row in df.iterrows():
            with st.container(border=True):
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
                        st.write(row['fase'])

                with col_btn:
                    st.write("") # Espaçador
                    if st.button("Analisar 🔍", key=f"analisar_{index}", use_container_width=True):
                        # 3. Salva os times no session_state para o scout.py ler
                        st.session_state.time_casa_scout = row['mandante']
                        st.session_state.time_fora_scout = row['visitante']
                        
                        st.success("Enviado!")
                        # Se você quiser que ele mude de aba automaticamente, use:
                        # st.rerun() 

    except Exception as e:
        st.error("Erro ao carregar agenda do GitHub.")
        st.info("Verifique se o arquivo 'jogos_do_dia.csv' existe e se o link RAW está correto.")
        if st.checkbox("Mostrar erro técnico"):
            st.write(e)

# Chamada da função para testar o arquivo individualmente se necessário
if __name__ == "__main__":
    mostrar_jogos()
