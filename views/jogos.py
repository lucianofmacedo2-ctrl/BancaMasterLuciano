import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

URL_AGENDA = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.csv"
ARQUIVO_HISTORICO = 'dados_25_26.csv'

def carregar_historico():
    try:
        df = pd.read_csv(ARQUIVO_HISTORICO, sep=None, engine='python', encoding='utf-8-sig')
        df.columns = [c.strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

def mostrar_jogos():
    st.title("📅 Agenda de Jogos")
    
    # 1. CARREGAR AGENDA (UTF-8-SIG remove o \ufeff)
    @st.cache_data(ttl=60)
    def carregar_agenda(url):
        try:
            df = pd.read_csv(url, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = [c.strip() for c in df.columns]
            # Limpeza de espaços em branco
            df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
            return df
        except Exception as e:
            st.error(f"Erro ao carregar agenda: {e}")
            return pd.DataFrame()

    df_agenda = carregar_agenda(URL_AGENDA)

    if df_agenda.empty or 'Data' not in df_agenda.columns:
        if not df_agenda.empty:
            st.error(f"Coluna 'Data' não encontrada. Detectadas: {list(df_agenda.columns)}")
        return

    # 2. LÓGICA DE DATAS (Ano com 2 ou 4 dígitos)
    hoje_dt = datetime.now().date()
    
    # Criamos as duas opções de formato para busca
    def formatar_data_busca(dt):
        return [dt.strftime('%d/%m/%Y'), dt.strftime('%d/%m/%y')]

    if 'data_sel_formatos' not in st.session_state:
        st.session_state.data_sel_formatos = formatar_data_busca(hoje_dt)
        st.session_state.data_exibicao = hoje_dt.strftime('%d/%m/%Y')

    cols_btn = st.columns(3)
    datas_opcoes = [hoje_dt, hoje_dt + timedelta(days=1), hoje_dt + timedelta(days=2)]
    labels = ["📅 Hoje", "📅 Amanhã", "📅 Depois"]

    for i in range(3):
        if cols_btn[i].button(labels[i], use_container_width=True):
            st.session_state.data_sel_formatos = formatar_data_busca(datas_opcoes[i])
            st.session_state.data_exibicao = datas_opcoes[i].strftime('%d/%m/%Y')

    st.info(f"Mostrando jogos de: **{st.session_state.data_exibicao}**")

    # 3. FILTRAGEM FLEXÍVEL
    # O isin verifica se a data no CSV bate com 22/01/2026 OU 22/01/26
    df_dia = df_agenda[df_agenda['Data'].isin(st.session_state.data_sel_formatos)]

    if df_dia.empty:
        st.warning(f"Nenhum jogo encontrado para {st.session_state.data_exibicao}.")
        with st.expander("Dados técnicos do CSV (Debug)"):
            st.write("Datas encontradas no arquivo:", df_agenda['Data'].unique())
            st.write("Formatos que o app buscou:", st.session_state.data_sel_formatos)
    else:
        # EXIBIÇÃO DOS JOGOS
        for liga in df_dia['Liga'].unique():
            df_l = df_dia[df_dia['Liga'] == liga]
            st.markdown(f"### 🏆 {liga}")
            for idx, row in df_l.iterrows():
                c1, c2, c3 = st.columns([4, 2.5, 1.5])
                with c1:
                    st.write(f"**{row['Hora']}** | {row['Mandante']} vs {row['Visitante']}")
                with c2:
                    st.write(f"Odds: {row.get('Odd Mandante','-')} | {row.get('Odd Empate','-')}")
                with c3:
                    if st.button("Analisar 🔍", key=f"btn_{idx}", use_container_width=True):
                        st.session_state.time_casa_scout = row['Mandante']
                        st.session_state.time_fora_scout = row['Visitante']
                        st.session_state.menu_ativo = "🔎 Scout"
                        st.rerun()
