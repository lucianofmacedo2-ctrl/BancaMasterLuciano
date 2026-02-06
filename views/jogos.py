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
        * ⚖️ **Equilibrado**: Diferença entre as odds menor ou igual a 1.0.
        """)
    
    @st.cache_data(ttl=60)
    def carregar_agenda(url):
        try:
            df = pd.read_csv(url, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = [str(c).strip() for c in df.columns]
            df = df.loc[:, ~df.columns.duplicated()] # Remove duplicatas de colunas
            return df
        except: return pd.DataFrame()

    # --- FUNÇÃO AUXILIAR PARA LIMPEZA DE COLUNAS (EVITA ATTRIBUTEERROR) ---
    def limpar_coluna_texto(df, nome_col):
        """Garante que a coluna seja uma Series de texto limpo, sem erros de duplicidade."""
        if nome_col not in df.columns:
            # Busca aproximada se não achar o nome exato
            cols_encontradas = [c for c in df.columns if nome_col.upper() in str(c).upper()]
            if not cols_encontradas: return pd.Series(dtype='object')
            nome_col = cols_encontradas[0]
        
        col_data = df[nome_col]
        # Se retornar um DataFrame (colunas duplicadas), pegamos a primeira
        if isinstance(col_data, pd.DataFrame):
            col_data = col_data.iloc[:, 0]
        
        return col_data.astype(str).str.strip().str.upper()

    # --- FUNÇÃO PARA CALCULAR CLASSIFICAÇÃO ---
    def obter_classificacao(df_input):
        if df_input is None or not isinstance(df_input, pd.DataFrame) or df_input.empty:
            return {}
        
        df_c = df_input.copy()
        df_c.columns = [str(c).strip() for c in df_c.columns]
        df_c = df_c.loc[:, ~df_c.columns.duplicated()]

        # Filtragem de Temporada (2025/2026 e 2026)
        if 'Temporada' in df_c.columns:
            # Tratamento seguro da coluna Temporada
            s_temp = df_c['Temporada']
            if isinstance(s_temp, pd.DataFrame): s_temp = s_temp.iloc[:, 0]
            df_c = df_c[s_temp.astype(str).str.strip().isin(['2025/2026', '2026'])]

        # Limpeza Segura de Colunas Cruciais
        df_c['LIGA_OK'] = limpar_coluna_texto(df_c, 'Liga')
        df_c['M_OK'] = limpar_coluna_texto(df_c, 'Mandante')
        df_c['V_OK'] = limpar_coluna_texto(df_c, 'Visitante')

        if df_c['LIGA_OK'].empty: return {}

        stats = {}
        for _, row in df_c.iterrows():
            liga = row['LIGA_OK']
            m, v = row['M_OK'], row['V_OK']
            try:
                gm = float(row['Gols_Mandante_FT'])
                gv = float(row['Gols_Visitante_FT'])
            except: continue
            
            if liga not in stats: stats[liga] = {}
            for t in [m, v]:
                if t not in stats[liga]: stats[liga][t] = {'pts': 0, 'sg': 0}
            
            if gm > gv: stats[liga][m]['pts'] += 3
            elif gv > gm: stats[liga][v]['pts'] += 3
            else:
                stats[liga][m]['pts'] += 1
                stats[liga][v]['pts'] += 1
            stats[liga][m]['sg'] += (gm - gv)
            stats[liga][v]['sg'] += (gv - gm)
        
        posicoes = {}
        for liga in stats:
            ranking = sorted(stats[liga].items(), key=lambda x: (x[1]['pts'], x[1]['sg']), reverse=True)
            for i, (time, _) in enumerate(ranking):
                posicoes[f"{liga}_{time}"] = i + 1
        return posicoes

    df_agenda = carregar_agenda(URL_AGENDA)
    dict_posicoes = obter_classificacao(df_hist)

    # Preparação para estatísticas e alertas
    if not df_hist.empty:
        df_h_clean = df_hist.copy()
        df_h_clean.columns = [str(c).strip() for c in df_h_clean.columns]
        df_h_clean = df_h_clean.loc[:, ~df_h_clean.columns.duplicated()]
        
        # Filtro temporada nas médias
        if 'Temporada' in df_h_clean.columns:
            s_t = df_h_clean['Temporada']
            if isinstance(s_t, pd.DataFrame): s_t = s_t.iloc[:, 0]
            df_h_clean = df_h_clean[s_t.astype(str).str.strip().isin(['2025/2026', '2026'])]
        
        df_h_clean['M_UP'] = limpar_coluna_texto(df_h_clean, 'Mandante')
        df_h_clean['V_UP'] = limpar_coluna_texto(df_h_clean, 'Visitante')
    else:
        df_h_clean = pd.DataFrame()

    if df_agenda.empty or 'Data' not in df_agenda.columns:
        st.error("Erro ao carregar a agenda de jogos.")
        return

    # Navegação de Datas
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

    # Filtro do dia
    df_dia = df_agenda[df_agenda['Data'].isin(st.session_state.data_sel_formatos)]
    times_no_dia = []

    if df_dia.empty:
        st.warning(f"Nenhum jogo encontrado para {st.session_state.data_exibicao}.")
    else:
        for liga in df_dia['Liga'].unique():
            df_l = df_dia[df_dia['Liga'] == liga]
            liga_up = str(liga).strip().upper()
            st.markdown(f"#### 🏆 {liga}")
            
            for idx, row in df_l.iterrows():
                mandante = str(row['Mandante']).strip()
                visitante = str(row['Visitante']).strip()
                times_no_dia.extend([mandante, visitante])
                
                m_up, v_up = mandante.upper(), visitante.upper()
                pos_m = dict_posicoes.get(f"{liga_up}_{m_up}", "?")
                pos_v = dict_posicoes.get(f"{liga_up}_{v_up}", "?")
                
                # --- Lógica de Alertas ---
                icones = ""
                if not df_h_clean.empty:
                    df_m_h = df_h_clean[(df_h_clean['M_UP'] == m_up) | (df_h_clean['V_UP'] == m_up)]
                    df_v_h = df_h_clean[(df_h_clean['M_UP'] == v_up) | (df_h_clean['V_UP'] == v_up)]
                    
                    if not df_m_h.empty and not df_v_h.empty:
                        try:
                            m_g = (df_m_h['Total_Gols_FT'].mean() + df_v_h['Total_Gols_FT'].mean()) / 2
                            if m_g > 2.5: icones += " 🔥⚽"
                            
                            b_m = (len(df_m_h[(df_m_h['Gols_Mandante_FT']>0) & (df_m_h['Gols_Visitante_FT']>0)]) / len(df_m_h))
                            b_v = (len(df_v_h[(df_v_h['Gols_Mandante_FT']>0) & (df_v_h['Gols_Visitante_FT']>0)]) / len(df_v_h))
                            if (b_m + b_v) / 2 >= 0.60: icones += " 🤝"
                        except: pass

                # Selo de Favorito
                odd_m = row.get('Odd Mandante', 0)
                odd_v = row.get('Odd Visitante', 0)
                selo = ""
                try:
                    vm, vv = float(str(odd_m).replace(',','.')), float(str(odd_v).replace(',','.'))
                    if vm < 1.4 or vv < 1.4: selo = " 🌟"
                    elif vm <= 1.8 or vv <= 1.8: selo = " ⭐"
                except: pass

                c1, c2, c3 = st.columns([4.2, 3.0, 1.3])
                with c1:
                    st.write(f"**{row['Hora']}** | ({pos_m}º) {mandante} vs {visitante} ({pos_v}º){icones}{selo}")
                with c2:
                    st.write(f"Odds: **{odd_m}** | **{row.get('Odd Empate',0)}** | **{odd_v}**")
                with c3:
                    if st.button("Analisar 🔍", key=f"ag_{idx}_{m_up[:3]}", use_container_width=True):
                        st.session_state.liga_scout = liga_up
                        st.session_state.time_casa_scout = mandante
                        st.session_state.time_fora_scout = visitante
                        st.session_state.menu_ativo = "🔎 Scout"
                        st.rerun()

    # --- RANKINGS ---
    if not df_h_clean.empty and times_no_dia:
        st.divider()
        st.subheader("📊 Destaques da Rodada (Temporada Atual)")
        times_u = list(set([t.upper() for t in times_no_dia]))
        r_list = []
        for t in times_u:
            df_t = df_h_clean[(df_h_clean['M_UP'] == t) | (df_h_clean['V_UP'] == t)]
            if not df_t.empty:
                r_list.append({"Time": t, "Média Gols": df_t['Total_Gols_FT'].mean()})
        
        if r_list:
            df_rank = pd.DataFrame(r_list).sort_values('Média Gols', ascending=False).head(5)
            st.write("🔥 **Ataques mais produtivos (2025-2026):**")
            st.dataframe(df_rank, hide_index=True, use_container_width=True)
