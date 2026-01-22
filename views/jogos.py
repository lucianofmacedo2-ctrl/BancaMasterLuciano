import streamlit as st
import pandas as pd

# Link RAW para o seu CSV na raiz
URL_CSV = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.csv"

def mostrar_jogos():
    st.title("📅 Agenda de Jogos")

    # --- CSS SLIM REFINADO ---
    st.markdown("""
        <style>
        .header-liga {
            background-color: rgba(128, 128, 128, 0.05);
            padding: 5px 12px;
            border-radius: 4px;
            margin-top: 15px;
            border-left: 4px solid #28a745;
        }
        .header-liga h4 { margin: 0; font-size: 15px; font-weight: bold; color: #555; }
        .linha-jogo { display: flex; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(128, 128, 128, 0.05); }
        .hora-texto { color: #28a745; font-weight: bold; font-size: 14px; min-width: 50px; }
        .times-texto { font-size: 15px; font-weight: 500; flex-grow: 1; }
        .odd-container { display: flex; gap: 4px; justify-content: flex-end; }
        .odd-box {
            background-color: rgba(40, 167, 69, 0.1);
            color: #28a745;
            border: 1px solid rgba(40, 167, 69, 0.2);
            border-radius: 3px;
            width: 40px;
            text-align: center;
            font-size: 12px;
            font-weight: bold;
            padding: 2px 0;
        }
        </style>
    """, unsafe_allow_html=True)

    try:
        @st.cache_data(ttl=60)
        def carregar_dados_csv(url):
            # Tenta ler com os dois separadores mais comuns (vírgula e ponto-e-vírgula)
            try:
                # Tenta ponto e vírgula (Padrão Excel Brasil)
                df = pd.read_csv(url, sep=';', encoding='utf-8')
                if 'competicao' not in df.columns: raise Exception()
                return df
            except:
                try:
                    # Tenta vírgula (Padrão internacional)
                    df = pd.read_csv(url, sep=',', encoding='utf-8')
                    if 'competicao' not in df.columns: raise Exception()
                    return df
                except:
                    # Tenta com codificação Latin-1 (para acentos do Windows)
                    return pd.read_csv(url, sep=';', encoding='latin-1')

        df = carregar_dados_csv(URL_CSV)

        # Limpar nomes das colunas (remove espaços invisíveis)
        df.columns = df.columns.str.strip()

        if df.empty:
            st.warning("O arquivo de jogos está vazio.")
            return

        # Agrupar por liga
        ligas = df['competicao'].unique()

        for liga in ligas:
            st.markdown(f"<div class='header-liga'><h4>🏆 {liga}</h4></div>", unsafe_allow_html=True)
            df_liga = df[df['competicao'] == liga]
            
            for index, row in df_liga.iterrows():
                # Criando colunas para o layout
                col_dados, col_odds, col_btn = st.columns([4, 2, 1.2])
                
                with col_dados:
                    st.markdown(f"""
                        <div class='linha-jogo'>
                            <span class='hora-texto'>{row['hora']}</span>
                            <span class='times-texto'>{row['mandante']} vs {row['visitante']}</span>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col_odds:
                    # Exibe odds se as colunas existirem e não forem vazias
                    o1 = str(row.get('odd_1', '-'))
                    ox = str(row.get('odd_x', '-'))
                    o2 = str(row.get('odd_2', '-'))
                    
                    if o1 != 'nan' and o1 != '-':
                        st.markdown(f"""
                            <div class='odd-container' style='padding-top: 5px;'>
                                <div class='odd-box'>{o1}</div>
                                <div class='odd-box'>{ox}</div>
                                <div class='odd-box'>{o2}</div>
                            </div>
                        """, unsafe_allow_html=True)
                
                with col_btn:
                    if st.button("Analisar", key=f"btn_{index}", use_container_width=True):
                        st.session_state.time_casa_scout = row['mandante']
                        st.session_state.time_fora_scout = row['visitante']
                        st.toast(f"⚽ {row['mandante']} pronto para análise!")

    except Exception as e:
        st.error(f"Erro ao processar as colunas: {e}")
        st.info("Certifique-se que o CSV tem as colunas: data, hora, competicao, mandante, visitante")

if __name__ == "__main__":
    mostrar_jogos()
