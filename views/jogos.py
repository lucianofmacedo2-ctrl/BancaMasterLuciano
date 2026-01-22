import streamlit as st
import pandas as pd

URL_CSV = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.csv"

def mostrar_jogos():
    st.title("📅 Agenda de Jogos")

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
        .header-liga h4 { margin: 0; font-size: 15px; font-weight: bold; color: #555; text-transform: uppercase; }
        .linha-jogo { display: flex; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(128, 128, 128, 0.1); }
        .hora-texto { color: #28a745; font-weight: bold; font-size: 14px; min-width: 55px; }
        .times-texto { font-size: 16px; font-weight: 500; margin-left: 10px; }
        .odd-box {
            background-color: rgba(40, 167, 69, 0.1);
            color: #28a745;
            border: 1px solid rgba(40, 167, 69, 0.3);
            border-radius: 4px;
            width: 45px;
            text-align: center;
            font-size: 13px;
            font-weight: bold;
            padding: 3px 0;
        }
        </style>
    """, unsafe_allow_html=True)

    try:
        @st.cache_data(ttl=60)
        def carregar_dados_csv(url):
            for sep in [';', ',']:
                try:
                    df = pd.read_csv(url, sep=sep, encoding='utf-8')
                    if 'Liga' in df.columns: return df
                except: continue
            return pd.read_csv(url, sep=';', encoding='latin-1')

        df = carregar_dados_csv(URL_CSV)
        df.columns = df.columns.str.strip()

        if df.empty:
            st.warning("O arquivo 'Lista_Jogos.csv' está vazio.")
            return

        ligas = df['Liga'].unique()

        for liga in ligas:
            st.markdown(f"<div class='header-liga'><h4>🏆 {liga}</h4></div>", unsafe_allow_html=True)
            df_liga = df[df['Liga'] == liga]
            
            for index, row in df_liga.iterrows():
                col_dados, col_odds, col_btn = st.columns([4, 2.5, 1.5])
                
                with col_dados:
                    st.markdown(f"""
                        <div class='linha-jogo'>
                            <span class='hora-texto'>{row['Hora']}</span>
                            <span class='times-texto'>{row['Mandante']} vs {row['Visitante']}</span>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col_odds:
                    o1 = row.get('Odd Mandante', '-')
                    ox = row.get('Odd Empate', '-')
                    o2 = row.get('Odd Visitante', '-')
                    st.markdown(f"""
                        <div style='display: flex; gap: 5px; padding-top: 8px;'>
                            <div class='odd-box'>{o1}</div>
                            <div class='odd-box'>{ox}</div>
                            <div class='odd-box'>{o2}</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col_btn:
                    st.write("") 
                    if st.button("Analisar 🔍", key=f"btn_{index}", use_container_width=True):
                        # SALVA OS TIMES PARA O SCOUT
                        st.session_state.time_casa_scout = row['Mandante']
                        st.session_state.time_fora_scout = row['Visitante']
                        
                        # MUDA A PÁGINA NO MENU LATERAL
                        st.session_state.menu_ativo = "🔎 Scout"
                        
                        # RECARREGA O APP JÁ NA PÁGINA NOVA
                        st.rerun()

    except Exception as e:
        st.error("Erro ao carregar a agenda.")

if __name__ == "__main__":
    mostrar_jogos()
