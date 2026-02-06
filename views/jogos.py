import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz

# Links dos arquivos
URL_AGENDA = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.csv"

def mostrar_jogos(df_hist): 
    st.title("📅 Agenda de Jogos")
    
    # --- AJUSTE DE FUSO HORÁRIO ---
    brasil_tz = pytz.timezone('America/Sao_Paulo')
    hoje_dt = datetime.now(brasil_tz).date()

    with st.expander("💡 Entenda os Sinais de Alerta (Radar de Valor)", expanded=True):
        st.markdown("""
        * 🔥⚽ **Fogo + Gol**: Tendência altíssima de **Over 2.5 Gols**.
        * 🔥🚩 **Fogo + Canto**: Tendência altíssima de **Over 9.5 Cantos**.
        * 🤝 **Ambas Sim**: Mais de 60% de incidência de **Ambas Marcam**.
        * ⭐ **Favorito**: Odd entre 1.40 e 1.80.
        * 🌟 **Super Favorito**: Odd abaixo de 1.40.
        * ⚖️ **Equilibrado**: Gap entre as odds menor ou igual a 1.0.
        """)
    
    @st.cache_data(ttl=60)
    def carregar_agenda(url):
        try:
            df = pd.read_csv(url, sep=None, engine='python', encoding='utf-8-sig')
            # Limpa espaços nos nomes das colunas da agenda
            df.columns = [c.strip() for c in df.columns]
            df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
            return df
        except: return pd.DataFrame()

    # --- FUNÇÃO PARA CALCULAR CLASSIFICAÇÃO (COM LIMPEZA DE COLUNAS) ---
    def obter_classificacao(df):
        if df is None or df.empty: return {}
        
        # Cria uma cópia para não afetar o DataFrame original
        df_c = df.copy()
        
        # LIMPEZA DOS NOMES DAS COLUNAS (Cura o AttributeError)
        df_c.columns = [str(c).strip() for c in df_c.columns]
        
        # Verifica se a coluna 'Liga' existe após a limpeza
        if 'Liga' not in df_c.columns:
            return {}

        stats = {}
        # Padronização de valores para busca
        df_c['Liga'] = df_c['Liga'].astype(str).str.strip().upper()
        df_c['Mandante'] = df_c['Mandante'].astype(str).str.strip().upper()
        df_c['Visitante'] = df_c['Visitante'].astype(str).str.strip().upper()

        for _, row in df_c.iterrows():
            liga = row['Liga']
            m, v = row['Mandante'], row['Visitante']
            try:
                gm, gv = float(row['Gols_Mandante_FT']), float(row['Gols_Visitante_FT'])
            except: continue
            
            if liga not in stats: stats[liga] = {}
            for t in [m, v]:
                if t not in stats[liga]: stats[liga][t] = {'pts': 0, 'sg': 0}
            
            # Cálculo de Pontos
            if gm > gv: stats[liga][m]['pts'] += 3
            elif gv > gm: stats[liga][v]['pts'] += 3
            else:
                stats[liga][m]['pts'] += 1
                stats[liga][v]['pts'] += 1
            
            # Saldo de Gols
            stats[liga][m]['sg'] += (gm - gv)
            stats[liga][v]['sg'] += (gv - gm)
        
        posicoes_finais = {}
        for liga in stats:
            ranking = sorted(stats[liga].items(), key=lambda x: (x[1]['pts'], x[1]['sg']), reverse=True)
            for i, (time, _) in enumerate(ranking):
                posicoes_finais[f"{liga}_{time}"] = i + 1
        return posicoes_finais

    df_agenda = carregar_agenda(URL_AGENDA)
    
    # Processa a classificação com o df_hist (dados_25_26.csv)
    dict_posicoes = obter_classificacao(df_hist)

    if df_agenda.empty or 'Data' not in df_agenda.columns:
        st.error("Erro ao carregar a agenda de jogos.")
        return

    def formatar_data_busca(dt):
        return [dt.strftime('%d/%m/%Y'), dt.strftime('%d/%m/%y')]

    if 'data_sel_formatos' not in st.session_state:
        st.session_state.data_sel_formatos = formatar_data_busca(hoje_dt)
        st.session_state.data_exibicao = hoje_dt.strftime('%d/%m/%Y')

    cols_btn = st.columns(3)
    datas_opcoes = [hoje_dt, hoje_dt + timedelta(days=1), hoje_dt + timedelta(days=2)]
    labels = ["📅 Hoje", "📅 Amanhã", "📅 Depois"]

    for i in range(3):
        if cols_btn[i].button(labels[i], key=f"nav_date_{i}", use_container_width=True):
            st.session_state.data_sel_formatos = formatar_data_busca(datas_opcoes[i])
            st.session_state.data_exibicao = datas_opcoes[i].strftime('%d/%m/%Y')
            st.rerun()

    st.info(f"Mostrando jogos de: **{st.session_state.data_exibicao}**")

    # --- FILTRO DO DIA ---
    df_dia = df_agenda[df_agenda['Data'].isin(st.session_state.data_sel_formatos)]
    times_no_dia = [] 

    # --- LISTAGEM DE JOGOS POR LIGA ---
    if df_dia.empty:
        st.warning(f"Nenhum jogo encontrado para {st.session_state.data_exibicao}.")
    else:
        for liga in df_dia['Liga'].unique():
            df_l = df_dia[df_dia['Liga'] == liga]
            liga_upper = str(liga).strip().upper()
            st.markdown(f"#### 🏆 {liga}")
            
            for idx, row in df_l.iterrows():
                mandante, visitante = row['Mandante'], row['Visitante']
                times_no_dia.extend([mandante, visitante])
                
                m_upper = str(mandante).strip().upper()
                v_upper = str(visitante).strip().upper()
                
                pos_m = dict_posicoes.get(f"{liga_upper}_{m_upper}", "?")
                pos_v = dict_posicoes.get(f"{liga_upper}_{v_upper}", "?")
                
                # --- Lógica de ícones simplificada ---
                tem_gol = False
                if not df_hist.empty:
                    df_m_h = df_hist[(df_hist['Mandante'].astype(str).str.upper() == m_upper) | (df_hist['Visitante'].astype(str).str.upper() == m_upper)]
                    df_v_h = df_hist[(df_hist['Mandante'].astype(str).str.upper() == v_upper) | (df_hist['Visitante'].astype(str).str.upper() == v_upper)]
                    
                    if not df_m_h.empty and not df_v_h.empty:
                        try:
                            m_gols = (df_m_h[df_m_h['Mandante'].astype(str).str.upper()==m_upper]['Total_Gols_FT'].mean() + df_v_h[df_v_h['Visitante'].astype(str).str.upper()==v_upper]['Total_Gols_FT'].mean()) / 2
                            if m_gols > 2.5: tem_gol = True
                        except: pass

                icones = ""
                if tem_gol: icones += " 🔥⚽"

                odd_m = row.get('Odd Mandante', 0)
                odd_v = row.get('Odd Visitante', 0)

                c1, c2, c3 = st.columns([4.2, 3.0, 1.3])
                with c1:
                    st.write(f"**{row['Hora']}** | ({pos_m}º) {mandante} vs {visitante} ({pos_v}º){icones}")
                with c2:
                    st.write(f"Odds: **{odd_m}** | **{row.get('Odd Empate',0)}** | **{odd_v}**")
                with c3:
                    if st.button("Analisar 🔍", key=f"btn_ag_{idx}_{m_upper[:3]}", use_container_width=True):
                        st.session_state.liga_scout = liga_upper
                        st.session_state.time_casa_scout = mandante
                        st.session_state.time_fora_scout = visitante
                        st.session_state.menu_ativo = "🔎 Scout"
                        st.rerun()

    # --- RANKINGS DE PERFORMANCE ---
    if not df_hist.empty and times_no_dia:
        st.divider()
        st.subheader(f"📊 Rankings de Performance")
        
        times_dia_unicos = list(set([str(t).strip().upper() for t in times_no_dia]))
        rank_data = []

        for t in times_dia_unicos:
            df_t = df_hist[(df_hist['Mandante'].astype(str).str.upper() == t) | (df_hist['Visitante'].astype(str).str.upper() == t)]
            if not df_t.empty:
                try:
                    # Cálculo simplificado para evitar novos AttributeErrors
                    gm_f = df_t[df_t['Mandante'].astype(str).str.upper()==t]['Gols_Mandante_FT'].mean()
                    gm_s = df_t[df_t['Visitante'].astype(str).str.upper()==t]['Gols_Visitante_FT'].mean()
                    rank_data.append({"Time": t, "Gols FT Marcados": gm_f, "Gols FT Sofridos": gm_s})
                except: continue
        
        if rank_data:
            st.dataframe(pd.DataFrame(rank_data).head(10), hide_index=True, use_container_width=True)
