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
    
    # 1. CARREGAR DADOS
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

    # 2. LÓGICA DE DATAS (Ano 2026 ou 26)
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

    # 3. FILTRAGEM E EXIBIÇÃO
    df_dia = df_agenda[df_agenda['Data'].isin(st.session_state.data_sel_formatos)]

    if df_dia.empty:
        st.warning(f"Nenhum jogo encontrado para {st.session_state.data_exibicao}.")
    else:
        times_no_dia = []
        for liga in df_dia['Liga'].unique():
            df_l = df_dia[df_dia['Liga'] == liga]
            rodada = df_l['Rodada'].iloc[0] if 'Rodada' in df_l.columns else "-"
            st.markdown(f"#### 🏆 {liga} (Rodada: {rodada})")
            
            for idx, row in df_l.iterrows():
                times_no_dia.extend([row['Mandante'], row['Visitante']])
                c1, c2, c3 = st.columns([4, 2.5, 1.5])
                with c1:
                    st.write(f"**{row['Hora']}** | {row['Mandante']} vs {row['Visitante']}")
                with c2:
                    st.write(f"Odds: {row.get('Odd Mandante','-')} | {row.get('Odd Empate','-')} | {row.get('Odd Visitante','-')}")
                with c3:
                    if st.button("Analisar 🔍", key=f"btn_ag_{idx}", use_container_width=True):
                        st.session_state.time_casa_scout = row['Mandante']
                        st.session_state.time_fora_scout = row['Visitante']
                        st.session_state.menu_ativo = "🔎 Scout"
                        st.rerun()

        # 4. RANKING TOP 5 (INTELIGÊNCIA)
        if not df_hist.empty and times_no_dia:
            st.divider()
            st.subheader(f"🔝 Top 5 Performance - Times que jogam em {st.session_state.data_exibicao}")
            st.caption("Baseado na média histórica desta temporada (Dados de 2025/26)")

            times_dia_unicos = list(set(times_no_dia))
            rank_data = []

            for t in times_dia_unicos:
                # Filtrar jogos do time no histórico (como mandante ou visitante)
                jogos_t = df_hist[(df_hist['Mandante'] == t) | (df_hist['Visitante'] == t)]
                
                if not jogos_t.empty:
                    # Gols Marcados e Sofridos
                    gm = df_hist[df_hist['Mandante'] == t]['Gols_Mandante_FT'].sum() + df_hist[df_hist['Visitante'] == t]['Gols_Visitante_FT'].sum()
                    gs = df_hist[df_hist['Mandante'] == t]['Gols_Visitante_FT'].sum() + df_hist[df_hist['Visitante'] == t]['Gols_Mandante_FT'].sum()
                    
                    # Cantos Marcados e Sofridos
                    cm = df_hist[df_hist['Mandante'] == t]['Cantos_Mandante'].sum() + df_hist[df_hist['Visitante'] == t]['Cantos_Visitante'].sum()
                    cs = df_hist[df_hist['Mandante'] == t]['Cantos_Visitante'].sum() + df_hist[df_hist['Visitante'] == t]['Cantos_Mandante'].sum()
                    
                    # Chutes Marcados
                    chm = df_hist[df_hist['Mandante'] == t]['Chutes_Gol_Mandante'].sum() + df_hist[df_hist['Visitante'] == t]['Chutes_Gol_Visitante'].sum()
                    
                    total_j = len(jogos_t)
                    rank_data.append({
                        "Time": t,
                        "Gols Feitos": gm / total_j,
                        "Gols Sofridos": gs / total_j,
                        "Cantos Marcados": cm / total_j,
                        "Cantos Sofridos": cs / total_j,
                        "Chutes": chm / total_j
                    })
            
            if rank_data:
                df_rank = pd.DataFrame(rank_data)
                
                # Exibição em Colunas
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    st.write("⚽ **Gols Marcados (Top 5)**")
                    st.dataframe(df_rank.sort_values("Gols Feitos", ascending=False).head(5)[["Time", "Gols Feitos"]], hide_index=True, use_container_width=True)
                    
                    st.write("🚩 **Cantos Marcados (Top 5)**")
                    st.dataframe(df_rank.sort_values("Cantos Marcados", ascending=False).head(5)[["Time", "Cantos Marcados"]], hide_index=True, use_container_width=True)

                with col_r2:
                    st.write("🥅 **Gols Sofridos (Top 5)**")
                    st.dataframe(df_rank.sort_values("Gols Sofridos", ascending=False).head(5)[["Time", "Gols Sofridos"]], hide_index=True, use_container_width=True)
                    
                    st.write("🎯 **Chutes ao Gol (Top 5)**")
                    st.dataframe(df_rank.sort_values("Chutes", ascending=False).head(5)[["Time", "Chutes"]], hide_index=True, use_container_width=True)
                
                st.write("🚩 **Cantos Sofridos (Top 5)**")
                st.dataframe(df_rank.sort_values("Cantos Sofridos", ascending=False).head(5)[["Time", "Cantos Sofridos"]], hide_index=True, use_container_width=True)
