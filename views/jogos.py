import streamlit as st
import pandas as pd

# Link RAW para o seu CSV na raiz do repositório
URL_CSV = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.csv"

def mostrar_jogos():
    st.title("📅 Agenda de Jogos")

    # --- CONFIGURAÇÃO DE ESTILO (CSS) ---
    st.markdown("""
        <style>
        .header-liga {
            background-color: rgba(128, 128, 128, 0.08);
            padding: 6px 12px;
            border-radius: 5px;
            margin-top: 18px;
            margin-bottom: 8px;
            border-left: 5px solid #28a745;
        }
        .header-liga h4 { 
            margin: 0; 
            font-size: 15px; 
            font-weight: bold; 
            color: #888;
            text-transform: uppercase;
        }
        .linha-jogo { 
            display: flex; 
            align-items: center; 
            padding: 8px 0; 
            border-bottom: 1px solid rgba(128, 128, 128, 0.1); 
        }
        .hora-texto { 
            color: #28a745; 
            font-weight: bold; 
            font-size: 14px; 
            min-width: 55px; 
        }
        .times-texto { 
            font-size: 16px; 
            font-weight: 500; 
            margin-left: 10px;
        }
        .odd-box {
            background-color: rgba(40, 167, 69, 0.1);
            color: #28a745;
            border: 1px solid rgba(40, 167, 69, 0.3);
            border-radius: 4px;
            width: 42px;
            text-align: center;
            font-size: 13px;
            font-weight: bold;
            padding: 3px 0;
        }
        /* Ajuste para o botão ficar alinhado */
        .stButton button {
            margin-top: 2px;
        }
        </style>
    """, unsafe_allow_html=True)

    try:
        # Função para carregar dados tratando erros de separador e acentuação
        @st.cache_data(ttl=60)
        def carregar_dados_csv(url):
            try:
                # Tenta padrão internacional (vírgula e UTF-8)
                return pd.read_csv(url, sep=',', encoding='utf-8')
            except:
                try:
                    # Tenta padrão Excel Brasileiro (ponto-e-vírgula e Latin-1)
                    return pd.read_csv(url, sep=';', encoding='latin-1')
                except:
                    # Última tentativa (ponto-e-vírgula e UTF-8)
                    return pd.read_csv(url, sep=';', encoding='utf-8')

        df = carregar_dados_csv(URL_CSV)

        if df is None or df.empty:
            st.warning("O arquivo 'Lista_Jogos.csv' foi encontrado, mas está vazio.")
            return

        # Obter ligas únicas
        if 'competicao' in df.columns:
            ligas = df['competicao'].unique()
        else:
            st.error("Coluna 'competicao' não encontrada no CSV.")
            return

        for liga in ligas:
            # Cabeçalho da Liga
            st.markdown(f"<div class='header-liga'><h4>🏆 {liga}</h4></div>", unsafe_allow_html=True)
            
            df_liga = df[df['competicao'] == liga]
            
            for index, row in df_liga.iterrows():
                # Layout de 3 colunas: Jogo | Odds | Ação
                col_dados, col_odds, col_btn = st.columns([4, 2, 1.5])
                
                with col_dados:
                    st.markdown(f"""
                        <div class='linha-jogo'>
                            <span class='hora-texto'>{row['hora']}</span>
                            <span class='times-texto'>{row['mandante']} vs {row['visitante']}</span>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col_odds:
                    # Mostra as Odds se as colunas existirem e não forem vazias
                    if 'odd_1' in df.columns and str(row['odd_1']) != 'nan':
                        st.markdown(f"""
                            <div style='display: flex; gap: 5px; padding-top: 8px;'>
                                <div class='odd-box'>{row['odd_1']}</div>
                                <div class='odd-box'>{row['odd_x']}</div>
                                <div class='odd-box'>{row['odd_2']}</div>
                            </div>
                        """, unsafe_allow_html=True)
                
                with col_btn:
                    st.write("") # Espaçador para alinhar com o texto
                    if st.button("Analisar 🔍", key=f"btn_{index}", use_container_width=True):
                        # Salva os times no session_state para o módulo de estatísticas
                        st.session_state.time_casa_scout = row['mandante']
                        st.session_state.time_fora_scout = row['visitante']
                        st.toast(f"✅ Selecionado: {row['mandante']}")

    except Exception as e:
        st.error("Erro crítico ao carregar a agenda.")
        st.info("Verifique se o nome do arquivo no GitHub é exatamente 'Lista_Jogos.csv'.")
        # st.write(e) # Debug

if __name__ == "__main__":
    mostrar_jogos()
