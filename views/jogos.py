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
    with st.expander("💡 Radar de Valor Profissional (Média Cruzada)", expanded=True):
        st.markdown("""
        Nosso algoritmo utiliza **Média Cruzada** (Ataque vs Defesa) para identificar super tendências:
        * 🔥⚽ **Fogo + Gol**: Expectativa superior a **4.0 Gols** no confronto.
        * 🔥🚩 **Fogo + Canto**: Expectativa superior a **13.0 Escanteios** no confronto.
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

    # LÓGICA DE DATAS
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
        st.warning("Nenhum jogo encontrado para esta data.")
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
                    # Filtra histórico específico do mando
                    hist_m_casa = df_hist[df_hist['Mandante'] == m]
                    hist_v_fora = df_hist[df_hist['Visitante'] == v]
                    
                    if len(hist_m_casa) >= 2 and len(hist_v_fora) >= 2:
                        # --- CÁLCULO CRUZADO DE GOLS ---
                        # (O que m faz em casa + o que v sofre fora) / 2
                        exp_m_faz = (hist_m_casa['Gols_Mandante_FT'].mean() + hist_v_fora['Gols_Mandante_FT'].mean()) / 2
                        # (O que v faz fora + o que m sofre em casa) / 2
                        exp_v_faz = (hist_v_fora['Gols_Visitante_FT'].mean() + hist_m_casa['Gols_Visitante_FT'].mean()) / 2
                        
                        if (exp_m_faz + exp_v_faz) > 3.1: 
                            alerta_gol = " 🔥⚽"

                        # --- CÁLCULO CRUZADO DE CANTOS ---
                        # (Cantos que m faz em casa + Cantos que v cede fora) / 2
                        exp_c_m = (hist_m_casa['Cantos_Mandante'].mean() + hist_v_fora['Cantos_Mandante'].mean()) / 2
                        # (Cantos que v faz fora + Cantos que m cede em casa) / 2
                        exp_c_v = (hist_v_fora['Cantos_Visitante'].mean() + hist_m_casa['Cantos_Visitante'].mean()) / 2
                        
                        if (exp_c_m + exp_c_v) > 11.2: 
                            alerta_canto = " 🔥🚩"

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

        # --- RANKINGS TOP 5 ABAIXO DA LISTA ---
        if not df_hist.empty and times_no_dia:
            st.divider()
            st.subheader(f"📊 Top Performance - {st.session_state.data_exibicao}")
            
            times_dia_unicos = list(set(times_no_dia))
            rank_data = []
            for t in times_dia_unicos:
                jogos_t = df_hist[(df_hist['Mandante'] == t) | (df_hist['Visitante'] == t)]
                if not jogos_t.empty:
                    total_j = len(jogos_t)
                    rank_data.append({
                        "Time": t,
                        "Gols Marcados": (df_hist[df_hist['Mandante'] == t]['Gols_Mandante_FT'].sum() + df_hist[df_hist['Visitante'] == t]['Gols_Visitante_FT'].sum()) / total_j,
                        "Gols Sofridos": (df_hist[df_hist['Mandante'] == t]['Gols_Visitante_FT'].sum() + df_hist[df_hist['Mandante'] == t]['Gols_Visitante_FT'].sum()) / total_j,
                        "Cantos Marcados": (df_hist[df_hist['Mandante'] == t]['Cantos_Mandante'].sum() + df_hist[df_hist['Visitante'] == t]['Cantos_Visitante'].sum()) / total_j,
                        "Cantos Sofridos": (df_hist[df_hist['Mandante'] == t]['Cantos_Visitante'].sum() + df_hist[df_hist['Mandante'] == t]['Cantos_Mandante'].sum()) / total_j,
                        "Chutes Marcados": (df_hist[df_hist['Mandante'] == t]['Chutes_Gol_Mandante'].sum() + df_hist[df_hist['Visitante'] == t]['Chutes_Gol_Visitante'].sum()) / total_j,
                        "Chutes Sofridos": (df_hist[df_hist['Mandante'] == t]['Chutes_Gol_Visitante'].sum() + df_hist[df_hist['Mandante'] == t]['Chutes_Gol_Mandante'].sum()) / total_j
                    })
            
            if rank_data:
                df_rank = pd.DataFrame(rank_data)
                categorias = [("⚽ Gols", "Gols Marcados", "Gols Sofridos"), 
                              ("🚩 Escanteios", "Cantos Marcados", "Cantos Sofridos"),
                              ("🎯 Chutes ao Gol", "Chutes Marcados", "Chutes Sofridos")]
                for tit, cm, cs in categorias:
                    st.markdown(f"#### {tit}")
                    ca, cb = st.columns(2)
                    with ca: st.dataframe(df_rank.sort_values(cm, ascending=False).head(5)[["Time", cm]], hide_index=True, use_container_width=True)
                    with cb: st.dataframe(df_rank.sort_values(cs, ascending=False).head(5)[["Time", cs]], hide_index=True, use_container_width=True)
