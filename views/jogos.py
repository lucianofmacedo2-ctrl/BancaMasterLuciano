import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURAÇÃO DA API ---
API_KEY = "4059988260c0d57f4f27fed78f7aead1"
HEADERS = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}

@st.cache_data(ttl=3600)
def buscar_jogos_do_dia(data_str):
    url = "https://v3.football.api-sports.io/fixtures"
    params = {"date": data_str}
    try:
        response = requests.get(url, headers=HEADERS, params=params)
        return response.json().get('response', [])
    except Exception as e:
        st.error(f"Erro na API: {e}")
        return []

def mostrar_jogos():
    st.title("📅 Agenda de Jogos")
    
    # --- ATALHOS DE DATA ---
    st.markdown("### Selecione o Período")
    c_data1, c_data2, c_data3, c_data4 = st.columns(4)
    
    # Criamos botões que definem a data no session_state
    if "data_consulta" not in st.session_state:
        st.session_state.data_consulta = datetime.now()

    if c_data1.button("📅 Hoje"):
        st.session_state.data_consulta = datetime.now()
    if c_data2.button("⏩ Amanhã"):
        st.session_state.data_consulta = datetime.now() + timedelta(days=1)
    if c_data3.button("⏭️ Depois"):
        st.session_state.data_consulta = datetime.now() + timedelta(days=2)
    with c_data4:
        # Calendário manual para qualquer data
        st.session_state.data_consulta = st.date_input("Outra data", st.session_state.data_consulta)

    data_formatada = st.session_state.data_consulta.strftime('%Y-%m-%d')
    st.info(f"Exibindo jogos de: **{st.session_state.data_consulta.strftime('%d/%m/%Y')}**")

    # Botão para forçar atualização
    if st.sidebar.button("🔄 Limpar Cache API"):
        st.cache_data.clear()
        st.rerun()

    jogos_lista = buscar_jogos_do_dia(data_formatada)

    if not jogos_lista:
        st.warning("Nenhum jogo encontrado para esta data ou limite da API atingido.")
        return

    # Filtro de Ligas para facilitar a busca
    ligas_disponiveis = sorted(list(set([j['league']['name'] for j in jogos_lista])))
    ligas_finais = st.multiselect("Filtrar por Ligas específicas", ligas_disponiveis)

    # Listagem
    for j in jogos_lista:
        liga_nome = j['league']['name']
        if ligas_finais and liga_nome not in ligas_finais:
            continue
            
        home = j['teams']['home']['name']
        away = j['teams']['away']['name']
        hora = datetime.fromtimestamp(j['fixture']['timestamp']).strftime('%H:%M')
        
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 4, 1])
            with c1:
                st.write(f"**{hora}**")
                st.caption(j['fixture']['status']['short'])
            with c2:
                st.markdown(f"**{home} vs {away}**")
                st.caption(f"🏆 {liga_nome} ({j['league']['country']})")
            with c3:
                if st.button("📊 Scout", key=f"api_{j['fixture']['id']}"):
                    st.session_state.time_casa_scout = home
                    st.session_state.time_fora_scout = away
                    st.success("Times enviados!")
