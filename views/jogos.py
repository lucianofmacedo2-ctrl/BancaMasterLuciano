import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Links dos arquivos
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

    # --- LEGENDA PARA VENDA ---
    with st.expander("💡 Radar de Valor Profissional (Média Cruzada)", expanded=False):
        st.markdown("""
        Nosso algoritmo cruza o **Ataque** de um time com a **Defesa** do outro:
        * 🔥⚽ **Fogo + Gol**: Alta tendência de **Over 2.5**. (Expectativa cruzada > 2.5 gols).
        * 🔥🚩 **Fogo + Canto**: Alta tendência de **Over 9.5**. (Expectativa cruzada > 10.5 cantos).
        """)
    
    df_hist = carregar_historico()
    
    @st.cache_data(ttl=60)
    def carregar_agenda(url):
        try:
            df = pd.read_csv(url, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = [c.strip() for c in df.columns]
            df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
            return df
        except: return pd.DataFrame()

    df_agenda = carregar_agenda(URL_AGENDA)
    if df_agenda.empty or 'Data' not in df_agenda.columns: return

    # DATA LOGIC
    hoje_dt = datetime.now().date()
    def formatar_data_busca(dt): return [dt.strftime('%d/%m/%Y'), dt.strftime('%d/%m/%y')]
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

    df_dia = df_agenda[df_agenda['Data'].isin(st.session_state.data_sel_formatos)]

    if df_dia.empty:
        st.warning("Nenhum jogo encontrado.")
    else:
        times_no_dia = []
        for liga in df_dia['Liga'].unique():
            df_l = df_dia[df_dia['Liga'] == liga]
            st.markdown(f"#### 🏆 {liga}")
            
            for idx, row in df_l.iterrows():
                m, v = row['Mandante'], row['Visitante']
                times_no_dia.extend([m, v])
                
                alerta_gol, alerta_canto = "", ""
                
                if not df_hist.empty:
                    # DADOS HISTÓRICOS
                    # Mandante em Casa
                    hist_m = df_hist[df_hist['Mandante'] == m]
                    # Visitante Fora
                    hist_v = df_hist[df_hist['Visitante'] == v]
                    
                    if len(hist_m) >= 3 and len(hist_v) >= 3:
                        # --- LÓGICA CRUZADA DE GOLS ---
                        # Quanto o Mandante faz vs Quanto o Visitante sofre
                        exp_gols_m = (hist_m['Gols_Mandante_FT'].mean() + hist_v['Gols_Mandante_FT'].mean()) / 2
                        # Quanto o Visitante faz vs Quanto o Mandante sofre
                        exp_gols_v = (hist_v['Gols_Visitante_FT'].mean() + hist_m['Gols_Visitante_FT'].mean()) / 2
                        
                        if (exp_gols_m + exp_gols_v) >= 2.6: alerta_gol = " 🔥⚽"

                        # --- LÓGICA CRUZADA DE CANTOS ---
                        # Média de cantos que o Mandante faz vs que o Visitante sofre
                        exp_cantos_m = (hist_m['Cantos_Mandante'].mean() + hist_v['Cantos_Mandante'].mean()) / 2
                        # Média de cantos que o Visitante faz vs que o Mandante sofre
                        exp_cantos_v = (hist_v['Cantos_Visitante'].mean() + hist_m['Cantos_Visitante'].mean()) / 2
                        
                        if (exp_cantos_m + exp_cantos_v) >= 10.5: alerta_canto = " 🔥🚩"

                c1, c2, c3 = st.columns([4, 2.5, 1.5])
                with c1:
                    st.write(f"**{row['Hora']}** | {m} vs {v}{alerta_gol}{alerta_canto}")
                with c2:
                    st.write(f"Odds: {row.get('Odd Mandante','-')} | {row.get('Odd Empate','-')}")
                with c3:
                    if st.button("Analisar 🔍", key=f"btn_ag_{idx}", use_container_width=True):
                        st.session_state.time_casa_scout, st.session_state.time_fora_scout = m, v
                        st.session_state.menu_ativo = "🔎 Scout"
                        st.rerun()

        # O Ranking Top 5 continua igual (abaixo da lista)
