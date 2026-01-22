import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Links dos arquivos
URL_AGENDA = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.csv"
ARQUIVO_HISTORICO = 'dados_25_26.csv'

def carregar_historico():
    try:
        df = pd.read_csv(ARQUIVO_HISTORICO)
        df.columns = [c.strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

def mostrar_jogos():
    st.title("📅 Agenda de Jogos")
    
    # --- CSS ---
    st.markdown("""
        <style>
        .header-liga { background-color: rgba(128,128,128,0.08); padding: 10px; border-radius: 8px; margin-top: 15px; border-left: 5px solid #28a745; }
        .sub-rodada { font-size: 13px; color: #28a745; font-weight: bold; margin-left: 5px; }
        .linha-jogo { display: flex; align-items: center; padding: 10px 0; border-bottom: 1px solid rgba(128,128,128,0.05); }
        .hora-texto { color: #28a745; font-weight: bold; font-size: 14px; min-width: 60px; }
        .times-texto { font-size: 16px; font-weight: 500; }
        .odd-box { background-color: rgba(40, 167, 69, 0.08); color: #28a745; border: 1px solid rgba(40,167,69,0.2); border-radius: 4px; width: 50px; text-align: center; font-size: 13px; font-weight: bold; padding: 4px 0; }
        </style>
    """, unsafe_allow_html=True)

    # 1. CARREGAR DADOS
    df_hist = carregar_historico()
    
    @st.cache_data(ttl=60)
    def carregar_agenda(url):
        try:
            # Forçamos a leitura da coluna Data como texto para evitar erros de conversão automática
            df = pd.read_csv(url, sep=None, engine='python', dtype={'Data': str})
            df.columns = [c.strip() for c in df.columns]
            # Remove espaços de todas as colunas de texto
            df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
            return df
        except:
            return pd.DataFrame()

    df_agenda = carregar_agenda(URL_AGENDA)

    if df_agenda.empty:
        st.error("Não foi possível carregar a Lista_Jogos.csv. Verifique o arquivo no GitHub.")
        return

    # 2. CONFIGURAR DATAS DOS BOTÕES
    # Garantimos o formato 01/01/2026 (com zeros à esquerda)
    hoje_dt = datetime.now().date()
    amanha_dt = hoje_dt + timedelta(days=1)
    depois_dt = hoje_dt + timedelta(days=2)

    if 'data_sel' not in st.session_state:
        st.session_state.data_sel = hoje_dt.strftime('%d/%m/%Y')

    cols_btn = st.columns(3)
    if cols_btn[0].button("📅 Hoje", use_container_width=True): 
        st.session_state.data_sel = hoje_dt.strftime('%d/%m/%Y')
    if cols_btn[1].button("📅 Amanhã", use_container_width=True): 
        st.session_state.data_sel = amanha_dt.strftime('%d/%m/%Y')
    if cols_btn[2].button("📅 Depois", use_container_width=True): 
        st.session_state.data_sel = depois_dt.strftime('%d/%m/%Y')

    st.info(f"Mostrando jogos de: **{st.session_state.data_sel}**")

    # 3. FILTRAR E EXIBIR
    # Filtro rigoroso: removemos qualquer espaço extra antes de comparar
    df_dia = df_agenda[df_agenda['Data'] == st.session_state.data_sel]

    if df_dia.empty:
        st.warning(f"Nenhum jogo encontrado para {st.session_state.data_sel}.")
        # Ajuda para debug: mostra quais datas existem no seu CSV
        with st.expander("Ver datas disponíveis no CSV"):
            st.write(df_agenda['Data'].unique())
    else:
        times_no_dia = []
        for liga in df_dia['Liga'].unique():
            df_l = df_dia[df_dia['Liga'] == liga]
            rodada = df_l['Rodada'].iloc[0] if 'Rodada' in df_l.columns else "-"
            
            st.markdown(f"<div class='header-liga'>🏆 {liga} <span class='sub-rodada'>— Rodada {rodada}</span></div>", unsafe_allow_html=True)
            
            for idx, row in df_l.iterrows():
                times_no_dia.extend([row['Mandante'], row['Visitante']])
                c1, c2, c3 = st.columns([4, 2.5, 1.5])
                with c1:
                    st.markdown(f"<div class='linha-jogo'><span class='hora-texto'>{row['Hora']}</span><span class='times-texto'>{row['Mandante']} vs {row['Visitante']}</span></div>", unsafe_allow_html=True)
                with c2:
                    st.markdown(f"<div style='display: flex; gap: 8px; padding-top: 10px;'><div class='odd-box'>{row.get('Odd Mandante','-')}</div><div class='odd-box'>{row.get('Odd Empate','-')}</div><div class='odd-box'>{row.get('Odd Visitante','-')}</div></div>", unsafe_allow_html=True)
                with c3:
                    st.write("")
                    if st.button("Analisar 🔍", key=f"jog_{idx}", use_container_width=True):
                        st.session_state.time_casa_scout = row['Mandante']
                        st.session_state.time_fora_scout = row['Visitante']
                        st.session_state.menu_ativo = "🔎 Scout"
                        st.rerun()

        # 4. RANKING (MANTIDO)
        if not df_hist.empty and times_no_dia:
            st.divider()
            st.subheader(f"📊 Top Performance - Jogos de {st.session_state.data_sel}")
            # ... (resto do código do ranking permanece igual)
