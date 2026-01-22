import streamlit as st
import pandas as pd
import requests
import io

# Link direto para o arquivo na raiz
URL_EXCEL = "https://github.com/lucianofmacedo2-ctrl/BancaMasterLuciano/raw/main/Lista_Jogos.xlsx"

def mostrar_jogos():
    st.title("📅 Agenda de Jogos")

    # --- CSS SLIM ---
    st.markdown("""
        <style>
        .header-liga {
            background-color: rgba(128, 128, 128, 0.05);
            padding: 4px 10px;
            border-radius: 4px;
            margin-top: 15px;
            border-left: 3px solid #28a745;
        }
        .header-liga h4 { margin: 0; font-size: 14px; color: #888; text-transform: uppercase; }
        .odd-box {
            background-color: rgba(40, 167, 69, 0.1);
            color: #28a745;
            border: 1px solid rgba(40, 167, 69, 0.2);
            border-radius: 3px;
            width: 38px;
            text-align: center;
            font-size: 12px;
            font-weight: bold;
            padding: 2px 0;
        }
        </style>
    """, unsafe_allow_html=True)

    try:
        @st.cache_data(ttl=60)
        def carregar_dados_excel(url):
            # Baixa o arquivo binário do GitHub
            response = requests.get(url)
            response.raise_for_status() # Verifica se o download deu certo
            # Lê a aba 'JOGOS'
            return pd.read_excel(io.BytesIO(response.content), sheet_name="JOGOS")

        df = carregar_dados_excel(URL_EXCEL)

        if df.empty:
            st.warning("A aba 'JOGOS' está vazia.")
            return

        # Agrupar por liga
        ligas = df['competicao'].unique()

        for liga in ligas:
            st.markdown(f"<div class='header-liga'><h4>{liga}</h4></div>", unsafe_allow_html=True)
            df_liga = df[df['competicao'] == liga]
            
            for index, row in df_liga.iterrows():
                col_dados, col_odds, col_btn = st.columns([4, 2, 1.2])
                
                with col_dados:
                    st.markdown(f"""
                        <div style='padding: 5px 0; font-size: 15px;'>
                            <span style='color:#28a745; font-weight:bold;'>{row['hora']}</span>
                            <span style='margin-left:10px;'>{row['mandante']} vs {row['visitante']}</span>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col_odds:
                    # Exibe odds se as colunas existirem
                    if 'odd_1' in df.columns and str(row['odd_1']) != 'nan':
                        st.markdown(f"""
                            <div style='display: flex; gap: 4px; padding-top: 4px;'>
                                <div class='odd-box'>{row['odd_1']}</div>
                                <div class='odd-box'>{row['odd_x']}</div>
                                <div class='odd-box'>{row['odd_2']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                
                with col_btn:
                    if st.button("Analisar", key=f"btn_{index}", use_container_width=True):
                        st.session_state.time_casa_scout = row['mandante']
                        st.session_state.time_fora_scout = row['visitante']
                        st.toast(f"⚽ {row['mandante']} pronto!")

    except Exception as e:
        st.error(f"Erro ao carregar o Excel.")
        st.info("Dica: Verifique se a aba no Excel se chama exatamente JOGOS (em maiúsculas).")
        # st.write(e) # Debug

if __name__ == "__main__":
    mostrar_jogos()
