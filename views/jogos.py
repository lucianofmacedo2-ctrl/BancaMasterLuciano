import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DA API ---
API_KEY = "4059988260c0d57f4f27fed78f7aead1"
HEADERS = {
    'x-rapidapi-host': "v3.football.api-sports.io",
    'x-rapidapi-key': API_KEY
}

@st.cache_data(ttl=3600) # Guarda os dados por 1 hora para economizar sua cota de 100/dia
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
    st.title("📅 Próximos Jogos")
    st.markdown("Consulte os jogos do dia e envie direto para análise no Scout.")

    # 1. Escolha da Data
    data_sel = st.date_input("Selecione a data para análise", datetime.now())
    data_formatada = data_sel.strftime('%Y-%m-%d')

    if st.button("🔄 Buscar/Atualizar Jogos"):
        st.cache_data.clear() # Limpa o cache se o usuário clicar no botão manualmente
        st.rerun()

    jogos = buscar_jogos_do_dia(data_formatada)

    if not jogos:
        st.info("Nenhum jogo encontrado para esta data ou limite da API atingido.")
        return

    # 2. Filtro de Ligas (Opcional - para não mostrar 500 jogos)
    ligas_disponiveis = sorted(list(set([j['league']['name'] for j in jogos])))
    ligas_finais = st.multiselect("Filtrar Ligas", ligas_disponiveis)

    # 3. Listagem dos Jogos
    for j in jogos:
        liga_nome = j['league']['name']
        
        # Se houver filtro de liga, pula os que não estão nela
        if ligas_finais and liga_nome not in ligas_finais:
            continue
            
        home = j['teams']['home']['name']
        away = j['teams']['away']['name']
        hora = datetime.fromtimestamp(j['fixture']['timestamp']).strftime('%H:%M')
        status = j['fixture']['status']['long']
        
        with st.container(border=True):
            c1, c2, c3 = st.columns([1, 4, 1])
            
            with c1:
                st.write(f"**{hora}**")
                st.caption(status)
            
            with c2:
                st.markdown(f"**{home} vs {away}**")
                st.caption(f"🏆 {liga_nome} ({j['league']['country']})")
            
            with c3:
                # Botão para integrar com o seu Scout futuro
                if st.button("📊 Scout", key=f"api_{j['fixture']['id']}"):
                    st.session_state.time_casa_scout = home
                    st.session_state.time_fora_scout = away
                    st.success("Enviado!")
