import streamlit as st
import pandas as pd

# Link RAW para o arquivo Excel no GitHub
# Note que para Excel, o link termina com .xlsx
URL_EXCEL = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.xlsx"

def mostrar_jogos():
    st.title("📅 Agenda de Jogos (Base de Dados)")

    # --- CSS REFINADO ---
    st.markdown("""
        <style>
        .header-liga {
            background-color: rgba(128, 128, 128, 0.1);
            padding: 6px 15px;
            border-radius: 4px;
            margin-top: 20px;
            border-left: 5px solid #28a745;
        }
        .header-liga h4 { margin: 0; font-size: 16px; font-weight: bold; }
        .times-texto { font-size: 16px; font-weight: 500; }
        .hora-texto { color: #28a745; font-weight: bold; font-size: 15px; margin-right: 10px; }
        .odd-box {
            background-color: rgba(40, 167, 69, 0.1);
            color: #28a745;
            border: 1px solid rgba(40, 167, 69, 0.3);
            border-radius: 4px;
            padding: 2px 8px;
            font-weight: bold;
            font-size: 14px;
            text-align: center;
        }
        </style>
    """, unsafe_allow_html=True)

    try:
        # 1. Carregar o arquivo Excel da aba específica "JOGOS"
        @st.cache_data(ttl=60)
        def carregar_dados_excel(url):
            # É necessário ter a biblioteca 'openpyxl' instalada
            return pd.read_excel(url, sheet_name="JOGOS")

        df = carregar_dados_excel(URL_EXCEL)

        if df.empty:
            st.warning("Nenhum jogo encontrado na aba 'JOGOS'.")
            return

        # 2. Agrupar por Competição/Liga
        # Certifique-se que o nome da coluna na planilha é 'competicao'
        ligas = df['competicao'].unique()

        for liga in ligas:
            st.markdown(f"<div class='header-liga'><h4>🏆 {liga}</h4></div>", unsafe_allow_html=True)
            
            df_liga = df[df['competicao'] == liga]
            
            for index, row in df_liga.iterrows():
                # Layout: Info/Times | Odds | Botão
                col_jogo, col_odds, col_btn = st.columns([4, 2, 1.5])
                
                with col_jogo:
                    # Exibe Hora, Mandante e Visitante
                    st.markdown(f"""
                        <div style='padding: 5px 0;'>
                            <span class='hora-texto'>{row['hora']}</span>
                            <span class='times-texto'>{row['mandante']} vs {row['visitante']}</span>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col_odds:
                    # Verifica se existem odds na planilha (colunas odd_1, odd_x, odd_2)
                    if 'odd_1' in df.columns and str(row['odd_1']) != "nan":
                        st.markdown(f"""
                            <div style='display: flex; gap: 5px; padding-top: 5px;'>
                                <div class='odd-box'>{row['odd_1']}</div>
                                <div class='odd-box'>{row['odd_x']}</div>
                                <div class='odd-box'>{row['odd_2']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                
                with col_btn:
                    # Botão de análise que envia os dados para o scout
                    if st.button("Analisar 📊", key=f"btn_{index}", use_container_width=True):
                        st.session_state.time_casa_scout = row['mandante']
                        st.session_state.time_fora_scout = row['visitante']
                        st.toast(f"Times enviados para Scout!")

    except Exception as e:
        st.error("Erro ao carregar o arquivo Excel.")
        st.info("Certifique-se de que o arquivo 'Lista_Jogos.xlsx' está na raiz do GitHub e tem a aba 'JOGOS'.")
        # st.write(e) # Descomente para depurar erros

if __name__ == "__main__":
    mostrar_jogos()
