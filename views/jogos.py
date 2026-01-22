import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Links dos arquivos
URL_AGENDA = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.csv"
ARQUIVO_HISTORICO = 'dados_25_26.csv'

def carregar_historico():
    try:
        # Usamos utf-8-sig para ignorar automaticamente o caractere \ufeff
        df = pd.read_csv(ARQUIVO_HISTORICO, sep=None, engine='python', encoding='utf-8-sig')
        df.columns = [c.strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

def mostrar_jogos():
    st.title("📅 Agenda de Jogos")
    
    # 1. CARREGAR AGENDA COM TRATAMENTO DE CARACTERE INVISÍVEL
    @st.cache_data(ttl=60)
    def carregar_agenda(url):
        try:
            # O encoding 'utf-8-sig' é a chave para resolver o erro \ufeffData
            df = pd.read_csv(url, sep=None, engine='python', encoding='utf-8-sig')
            # Remove espaços extras de nomes de colunas
            df.columns = [c.strip() for c in df.columns]
            # Remove espaços de todas as células de texto
            df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
            return df
        except Exception as e:
            st.error(f"Erro ao carregar agenda: {e}")
            return pd.DataFrame()

    df_agenda = carregar_agenda(URL_AGENDA)

    if df_agenda.empty:
        return

    # Verificação amigável de colunas
    if 'Data' not in df_agenda.columns:
        st.error(f"Coluna 'Data' não encontrada. Colunas detectadas: {list(df_agenda.columns)}")
        return

    # 2. CONFIGURAÇÃO DE DATAS
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

    # 3. FILTRAR E EXIBIR
    df_dia = df_agenda[df_agenda['Data'] == st.session_state.data_sel]

    if df_dia.empty:
        st.warning(f"Nenhum jogo encontrado para {st.session_state.data_sel}.")
        with st.expander("Clique para ver as datas disponíveis no CSV"):
            st.write(df_agenda['Data'].unique())
    else:
        for liga in df_dia['Liga'].unique():
            df_l = df_dia[df_dia['Liga'] == liga]
            st.markdown(f"### 🏆 {liga}")
            
            for idx, row in df_l.iterrows():
                c1, c2, c3 = st.columns([4, 2.5, 1.5])
                with c1:
                    st.write(f"**{row['Hora']}** | {row['Mandante']} vs {row['Visitante']}")
                with c2:
                    st.write(f"Odds: {row.get('Odd Mandante','-')} | {row.get('Odd Empate','-')} | {row.get('Odd Visitante','-')}")
                with c3:
                    if st.button("Analisar 🔍", key=f"jog_{idx}"):
                        st.session_state.time_casa_scout = row['Mandante']
                        st.session_state.time_fora_scout = row['Visitante']
                        st.session_state.menu_ativo = "🔎 Scout"
                        st.rerun()
