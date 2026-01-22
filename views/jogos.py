import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

URL_AGENDA = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.csv"
ARQUIVO_HISTORICO = 'dados_25_26.csv'

def carregar_historico():
    try:
        df = pd.read_csv(ARQUIVO_HISTORICO, sep=None, engine='python')
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

    # 1. CARREGAR AGENDA (COM DETECÇÃO AUTOMÁTICA DE SEPARADOR)
    @st.cache_data(ttl=60)
    def carregar_agenda(url):
        try:
            # O sep=None faz o pandas descobrir se é vírgula ou ponto e vírgula sozinho
            df = pd.read_csv(url, sep=None, engine='python', encoding='utf-8')
            df.columns = [c.strip() for c in df.columns]
            return df
        except Exception as e:
            st.error(f"Erro ao baixar CSV: {e}")
            return pd.DataFrame()

    df_agenda = carregar_agenda(URL_AGENDA)

    if df_agenda.empty:
        return

    # Verificação de segurança: Se a coluna 'Data' não existe, tentamos limpar os nomes novamente
    if 'Data' not in df_agenda.columns:
        st.error(f"Erro Crítico: Coluna 'Data' não encontrada. Colunas detectadas: {list(df_agenda.columns)}")
        return

    # 2. CONFIGURAR DATAS
    hoje_dt = datetime.now().date()
    if 'data_sel' not in st.session_state:
        st.session_state.data_sel = hoje_dt.strftime('%d/%m/%Y')

    cols_btn = st.columns(3)
    datas = [hoje_dt, hoje_dt + timedelta(days=1), hoje_dt + timedelta(days=2)]
    labels = ["📅 Hoje", "📅 Amanhã", "📅 Depois"]

    for i in range(3):
        if cols_btn[i].button(labels[i], use_container_width=True):
            st.session_state.data_sel = datas[i].strftime('%d/%m/%Y')

    st.info(f"Mostrando jogos de: **{st.session_state.data_sel}**")

    # 3. FILTRAR JOGOS
    # Convertemos a coluna para string e limpamos espaços para garantir o match
    df_agenda['Data'] = df_agenda['Data'].astype(str).str.strip()
    df_dia = df_agenda[df_agenda['Data'] == st.session_state.data_sel]

    if df_dia.empty:
        st.warning(f"Nenhum jogo encontrado para {st.session_state.data_sel}.")
        with st.expander("Clique para ver as datas disponíveis no seu arquivo"):
            st.write(df_agenda['Data'].unique())
    else:
        # EXIBIÇÃO DOS JOGOS
        for liga in df_dia['Liga'].unique():
            df_l = df_dia[df_dia['Liga'] == liga]
            st.markdown(f"<div class='header-liga'>🏆 {liga}</div>", unsafe_allow_html=True)
            
            for idx, row in df_l.iterrows():
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
