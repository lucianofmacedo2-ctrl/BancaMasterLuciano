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
    
    # 1. CARREGAR DADOS
    df_hist = carregar_historico()
    
    @st.cache_data(ttl=60)
    def carregar_agenda(url):
        try:
            df = pd.read_csv(url, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = [c.strip() for c in df.columns]
            df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
            return df
        except: 
            return pd.DataFrame()

    df_agenda = carregar_agenda(URL_AGENDA)

    if df_agenda.empty or 'Data' not in df_agenda.columns:
        return

    # 2. LÓGICA DE DATAS
    hoje_dt = datetime.now().date()
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

    # 3. FILTRAGEM E EXIBIÇÃO COM ALERTA DE VALOR
    df_dia = df_agenda[df_agenda['Data'].isin(st.session_state.data_sel_formatos)]

    if df_dia.empty:
        st.warning(f"Nenhum jogo encontrado para {st.session_state.data_exibicao}.")
    else:
        times_no_dia = []
        for liga in df_dia['Liga'].unique():
            df_l = df_dia[df_dia['Liga'] == liga]
            st.markdown(f"#### 🏆 {liga}")
            
            for idx, row in df_l.iterrows():
                mandante = row['Mandante']
                visitante = row['Visitante']
                times_no_dia.extend([mandante, visitante])
                
                # --- Lógica do Alerta de Valor (Over 2.5) ---
                alerta_emoji = ""
                if not df_hist.empty:
                    # Média do Mandante (em casa)
                    jogos_m = df_hist[df_hist['Mandante'] == mandante]
                    media_m = (jogos_m['Gols_Mandante_FT'].mean() + jogos_m['Gols_Visitante_FT'].mean()) if not jogos_m.empty else 0
                    
                    # Média do Visitante (fora)
                    jogos_v = df_hist[df_hist['Visitante'] == visitante]
                    media_v = (jogos_v['Gols_Mandante_FT'].mean() + jogos_v['Gols_Visitante_FT'].mean()) if not jogos_v.empty else 0
                    
                    # Se a soma das médias for > 2.7 (ajustado para ser mais criterioso)
                    if (media_m + media_v) > 2.7:
                        alerta_emoji = " 🔥"

                c1, c2, c3 = st.columns([4, 2.5, 1.5])
                with c1:
                    # Exibe o emoji de fogo se o jogo tiver valor
                    st.write(f"**{row['Hora']}** | {mandante} vs {visitante}{alerta_emoji}")
                with c2:
                    st.write(f"Odds: {row.get('Odd Mandante','-')} | {row.get('Odd Empate','-')}")
                with c3:
                    if st.button("Analisar 🔍", key=f"btn_ag_{idx}", use_container_width=True):
                        st.session_state.time_casa_scout = mandante
                        st.session_state.time_fora_scout = visitante
                        st.session_state.menu_ativo = "🔎 Scout"
                        st.rerun()

        # 4. RANKINGS (MANTIDOS)
        if not df_hist.empty and times_no_dia:
            st.divider()
            st.subheader(f"📊 Top Performance - {st.session_state.data_exibicao}")
            
            times_dia_unicos = list(set(times_no_dia))
            rank_data = []

            for t in times_dia_unicos:
                jogos_t = df_hist[(df_hist['Mandante'] == t) | (df_hist['Visitante'] == t)]
                if not jogos_t.empty:
                    gm = df_hist[df_hist['Mandante'] == t]['Gols_Mandante_FT'].sum() + df_hist[df_hist['Visitante'] == t]['Gols_Visitante_FT'].sum()
                    gs = df_hist[df_hist['Mandante'] == t]['Gols_Visitante_FT'].sum() + df_hist[df_hist['Visitante'] == t]['Gols_Mandante_FT'].sum()
                    cm = df_hist[df_hist['Mandante'] == t]['Cantos_Mandante'].sum() + df_hist[df_hist['Visitante'] == t]['Cantos_Visitante'].sum()
                    cs = df_hist[df_hist['Mandante'] == t]['Cantos_Visitante'].sum() + df_hist[df_hist['Visitante'] == t]['Cantos_Mandante'].sum()
                    chm = df_hist[df_hist['Mandante'] == t]['Chutes_Gol_Mandante'].sum() + df_hist[df_hist['Visitante'] == t]['Chutes_Gol_Visitante'].sum()
                    chs = df_hist[df_hist['Mandante'] == t]['Chutes_Gol_Visitante'].sum() + df_hist[df_hist['Visitante'] == t]['Chutes_Gol_Mandante'].sum()
                    
                    total_j = len(jogos_t)
                    rank_data.append({
                        "Time": t,
                        "Gols Marcados": gm / total_j, "Gols Sofridos": gs / total_j,
                        "Cantos Marcados": cm / total_j, "Cantos Sofridos": cs / total_j,
                        "Chutes Marcados": chm / total_j, "Chutes Sofridos": chs / total_j
                    })
            
            if rank_data:
                df_rank = pd.DataFrame(rank_data)
                
                # --- LAYOUT SIMÉTRICO ---
                categorias = [
                    ("⚽ Gols", "Gols Marcados", "Gols Sofridos"),
                    ("🚩 Escanteios", "Cantos Marcados", "Cantos Sofridos"),
                    ("🎯 Chutes ao Gol", "Chutes Marcados", "Chutes Sofridos")
                ]
                
                for titulo, col_m, col_s in categorias:
                    st.markdown(f"#### {titulo}")
                    ca, cb = st.columns(2)
                    with ca:
                        st.write("**Marcados (Top 5)**")
                        st.dataframe(df_rank.sort_values(col_m, ascending=False).head(5)[["Time", col_m]], hide_index=True, use_container_width=True)
                    with cb:
                        st.write("**Sofridos (Top 5)**")
                        st.dataframe(df_rank.sort_values(col_s, ascending=False).head(5)[["Time", col_s]], hide_index=True, use_container_width=True)
