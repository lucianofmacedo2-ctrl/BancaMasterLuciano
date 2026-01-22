import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Links dos arquivos no GitHub
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
    
    # --- CSS PARA ESTILIZAÇÃO ---
    st.markdown("""
        <style>
        .header-liga { background-color: rgba(128,128,128,0.08); padding: 8px; border-radius: 5px; margin-top: 15px; border-left: 5px solid #28a745; }
        .sub-rodada { font-size: 12px; color: #888; margin-top: -5px; margin-left: 5px; }
        .linha-jogo { display: flex; align-items: center; padding: 8px 0; border-bottom: 1px solid rgba(128,128,128,0.1); }
        .hora-texto { color: #28a745; font-weight: bold; font-size: 14px; min-width: 55px; }
        .times-texto { font-size: 16px; font-weight: 500; margin-left: 10px; }
        .odd-box { background-color: rgba(40, 167, 69, 0.1); color: #28a745; border: 1px solid rgba(40,167,69,0.3); border-radius: 4px; width: 45px; text-align: center; font-size: 13px; font-weight: bold; padding: 3px 0; }
        .stButton>button { border-radius: 20px; }
        </style>
    """, unsafe_allow_html=True)

    # 1. CARREGAR DADOS
    df_historico = carregar_historico()
    
    @st.cache_data(ttl=60)
    def carregar_agenda(url):
        for sep in [';', ',']:
            try:
                df = pd.read_csv(url, sep=sep, encoding='utf-8')
                if 'Liga' in df.columns: return df
            except: continue
        return pd.read_csv(url, sep=';', encoding='latin-1')

    df_agenda = carregar_agenda(URL_AGENDA)
    df_agenda.columns = [c.strip() for c in df_agenda.columns]
    
    # 2. FILTROS DE DATA (BOTÕES)
    hoje = datetime.now().date()
    amanha = hoje + timedelta(days=1)
    depois = hoje + timedelta(days=2)

    col_f1, col_f2, col_f3 = st.columns(3)
    if 'data_filtro' not in st.session_state:
        st.session_state.data_filtro = hoje.strftime('%d/%m/%Y')

    if col_f1.button("📅 Hoje", use_container_width=True): st.session_state.data_filtro = hoje.strftime('%d/%m/%Y')
    if col_f2.button("📅 Amanhã", use_container_width=True): st.session_state.data_filtro = amanha.strftime('%d/%m/%Y')
    if col_f3.button("📅 Depois", use_container_width=True): st.session_state.data_filtro = depois.strftime('%d/%m/%Y')

    st.info(f"Mostrando jogos de: **{st.session_state.data_filtro}**")

    # Filtrar agenda pela data selecionada
    df_filtrado = df_agenda[df_agenda['Data'] == st.session_state.data_filtro]

    if df_filtrado.empty:
        st.warning(f"Nenhum jogo encontrado para {st.session_state.data_filtro}.")
    else:
        # 3. LISTAGEM DE JOGOS
        ligas = df_filtrado['Liga'].unique()
        times_do_dia = []

        for liga in ligas:
            df_liga = df_filtrado[df_filtrado['Liga'] == liga]
            rodada = df_liga['Rodada'].iloc[0] if 'Rodada' in df_liga.columns else "-"
            
            st.markdown(f"<div class='header-liga'><h4>🏆 {liga}</h4><div class='sub-rodada'>Rodada: {rodada}</div></div>", unsafe_allow_html=True)
            
            for index, row in df_liga.iterrows():
                times_do_dia.extend([row['Mandante'], row['Visitante']])
                c_dados, c_odds, c_btn = st.columns([4, 2.5, 1.5])
                
                with c_dados:
                    st.markdown(f"<div class='linha-jogo'><span class='hora-texto'>{row['Hora']}</span><span class='times-texto'>{row['Mandante']} vs {row['Visitante']}</span></div>", unsafe_allow_html=True)
                
                with c_odds:
                    st.markdown(f"<div style='display: flex; gap: 5px; padding-top: 8px;'><div class='odd-box'>{row.get('Odd Mandante','-')}</div><div class='odd-box'>{row.get('Odd Empate','-')}</div><div class='odd-box'>{row.get('Odd Visitante','-')}</div></div>", unsafe_allow_html=True)
                
                with c_btn:
                    st.write("")
                    if st.button("Analisar 🔍", key=f"btn_{index}", use_container_width=True):
                        st.session_state.time_casa_scout = row['Mandante']
                        st.session_state.time_fora_scout = row['Visitante']
                        st.session_state.menu_ativo = "🔎 Scout"
                        st.rerun()

        # 4. RANKING TOP 5 (INTELIGÊNCIA)
        if not df_historico.empty:
            st.divider()
            st.subheader(f"🔝 Top 5 Performance - Jogos de {st.session_state.data_filtro}")
            st.caption("Baseado na média histórica desta temporada")

            # Filtrar histórico apenas dos times que jogam no dia
            times_unicos = list(set(times_do_dia))
            
            # Cálculo de Médias
            rank_data = []
            for time in times_unicos:
                # Jogos como mandante e visitante no histórico
                jogos_m = df_historico[df_historico['Mandande'] == time]
                jogos_v = df_historico[df_historico['Visitante'] == time]
                
                if len(jogos_m) + len(jogos_v) > 0:
                    gols_feitos = (jogos_m['Gols_Mandante_FT'].sum() + jogos_v['Gols_Visitante_FT'].sum()) / (len(jogos_m) + len(jogos_v))
                    gols_sofridos = (jogos_m['Gols_Visitante_FT'].sum() + jogos_v['Gols_Mandante_FT'].sum()) / (len(jogos_m) + len(jogos_v))
                    cantos_feitos = (jogos_m['Cantos_Mandante'].sum() + jogos_v['Cantos_Visitante'].sum()) / (len(jogos_m) + len(jogos_v))
                    chutes_feitos = (jogos_m['Chutes_Gol_Mandante'].sum() + jogos_v['Chutes_Gol_Visitante'].sum()) / (len(jogos_m) + len(jogos_v))
                    
                    rank_data.append({
                        "Time": time,
                        "Gols Feitos": gols_feitos,
                        "Gols Sofridos": gols_sofridos,
                        "Cantos": cantos_feitos,
                        "Chutes ao Gol": chutes_feitos
                    })
            
            df_ranking = pd.DataFrame(rank_data)

            if not df_ranking.empty:
                r1, r2, r3 = st.columns(3)
                with r1:
                    st.write("⚽ **Gols Feitos**")
                    st.dataframe(df_ranking.sort_values("Gols Feitos", ascending=False)[["Time", "Gols Feitos"]].head(5), hide_index=True)
                with r2:
                    st.write("🥅 **Gols Sofridos**")
                    st.dataframe(df_ranking.sort_values("Gols Sofridos", ascending=False)[["Time", "Gols Sofridos"]].head(5), hide_index=True)
                with r3:
                    st.write("🚩 **Cantos (Média)**")
                    st.dataframe(df_ranking.sort_values("Cantos", ascending=False)[["Time", "Cantos"]].head(5), hide_index=True)

if __name__ == "__main__":
    mostrar_jogos()
