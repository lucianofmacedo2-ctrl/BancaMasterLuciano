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
            df.columns = [c.strip() for c in df.columns]
            df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
            return df
        except: return pd.DataFrame()

    # --- FUNÇÃO PARA CALCULAR CLASSIFICAÇÃO (CORREÇÃO DO ATTRIBUTEERROR) ---
    def obter_classificacao(df):
        if df is None or df.empty: return {}
        
        # Copiamos para processar
        df_c = df.copy()
        
        # CORREÇÃO: Limpa espaços em branco de TODOS os nomes de colunas (Evita o erro 'Liga')
        df_c.columns = [str(c).strip() for c in df_c.columns]
        
        # Verifica se as colunas essenciais existem após a limpeza
        colunas_necessarias = ['Liga', 'Mandante', 'Visitante', 'Gols_Mandante_FT', 'Gols_Visitante_FT']
        if not all(col in df_c.columns for col in colunas_necessarias):
            return {}

        stats = {}
        # Padronização de nomes para comparação
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
            
            if gm > gv: stats[liga][m]['pts'] += 3
            elif gv > gm: stats[liga][v]['pts'] += 3
            else:
                stats[liga][m]['pts'] += 1
                stats[liga][v]['pts'] += 1
            
            stats[liga][m]['sg'] += (gm - gv)
            stats[liga][v]['sg'] += (gv - gm)
        
        posicoes_finais = {}
        for liga in stats:
            ranking = sorted(stats[liga].items(), key=lambda x: (x[1]['pts'], x[1]['sg']), reverse=True)
            for i, (time, _) in enumerate(ranking):
                posicoes_finais[f"{liga}_{time}"] = i + 1
        return posicoes_finais

    # Carregamento e Processamento
    df_agenda = carregar_agenda(URL_AGENDA)
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

    # --- LÓGICA DE SUGESTÕES (MANTIDA) ---
    if not df_dia.empty and not df_hist.empty:
        sugestoes_gols = []
        sugestoes_cantos = []
        
        # Garante colunas do histórico limpas para as sugestões
        df_hist_clean = df_hist.copy()
        df_hist_clean.columns = [str(c).strip() for c in df_hist_clean.columns]
        
        col_c_h = 'Corners_H' if 'Corners_H' in df_hist_clean.columns else 'Cantos_Mandante'
        col_c_a = 'Corners_A' if 'Corners_A' in df_hist_clean.columns else 'Cantos_Visitante'

        for _, row in df_dia.iterrows():
            m, v = str(row['Mandante']).strip().upper(), str(row['Visitante']).strip().upper()
            df_m = df_hist_clean[(df_hist_clean['Mandante'].astype(str).str.upper() == m) | (df_hist_clean['Visitante'].astype(str).str.upper() == m)]
            df_v = df_hist_clean[(df_hist_clean['Mandante'].astype(str).str.upper() == v) | (df_hist_clean['Visitante'].astype(str).str.upper() == v)]
            
            if not df_m.empty and not df_v.empty:
                try:
                    m_gols = (df_m[df_m['Mandante'].astype(str).str.upper()==m]['Total_Gols_FT'].mean() + df_v[df_v['Visitante'].astype(str).str.upper()==v]['Total_Gols_FT'].mean()) / 2
                    if m_gols > 2.0:
                        sugestoes_gols.append({'Jogo': f"{row['Mandante']} x {row['Visitante']}", 'Média': m_gols})
                    
                    if col_c_h in df_hist_clean.columns:
                        m_cantos = (df_m[df_m['Mandante'].astype(str).str.upper()==m][col_c_h].mean() + df_v[df_v['Visitante'].astype(str).str.upper()==v][col_c_a].mean())
                        if m_cantos > 8.5:
                            sugestoes_cantos.append({'Jogo': f"{row['Mandante']} x {row['Visitante']}", 'Média': m_cantos})
                except: pass

        if sugestoes_gols or sugestoes_cantos:
            with st.expander("🎯 Dicas de Ouro do Algoritmo (Top 5)", expanded=True):
                c_sug1, c_sug2 = st.columns(2)
                with c_sug1:
                    st.markdown("🔥 **Top Over 2.5 Gols**")
                    if sugestoes_gols:
                        df_sg = pd.DataFrame(sugestoes_gols).sort_values(by='Média', ascending=False).head(5)
                        st.dataframe(df_sg, hide_index=True, use_container_width=True)
                    else: st.write("Nenhuma dica forte para gols.")
                with c_sug2:
                    st.markdown("🚩 **Top Over 9.5 Cantos**")
                    if sugestoes_cantos:
                        df_sc = pd.DataFrame(sugestoes_cantos).sort_values(by='Média', ascending=False).head(5)
                        st.dataframe(df_sc, hide_index=True, use_container_width=True)
                    else: st.write("Nenhuma dica forte para cantos.")

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
                
                tem_gol = False; tem_canto = False; tem_ambas = False
                if not df_hist.empty:
                    # Busca no histórico usando nomes limpos
                    df_m_h = df_hist_clean[(df_hist_clean['Mandante'].astype(str).str.upper() == m_upper) | (df_hist_clean['Visitante'].astype(str).str.upper() == m_upper)]
                    df_v_h = df_hist_clean[(df_hist_clean['Mandante'].astype(str).str.upper() == v_upper) | (df_hist_clean['Visitante'].astype(str).str.upper() == v_upper)]
                    
                    if not df_m_h.empty and not df_v_h.empty:
                        try:
                            m_gols = (df_m_h[df_m_h['Mandante'].astype(str).str.upper()==m_upper]['Total_Gols_FT'].mean() + df_v_h[df_v_h['Visitante'].astype(str).str.upper()==v_upper]['Total_Gols_FT'].mean()) / 2
                            if m_gols > 2.5: tem_gol = True
                            
                            col_c_h = 'Corners_H' if 'Corners_H' in df_hist_clean.columns else 'Cantos_Mandante'
                            col_c_a = 'Corners_A' if 'Corners_A' in df_hist_clean.columns else 'Cantos_Visitante'
                            if col_c_h in df_hist_clean.columns:
                                m_cantos = (df_m_h[df_m_h['Mandante'].astype(str).str.upper()==m_upper][col_c_h].mean() + df_v_h[df_v_h['Visitante'].astype(str).str.upper()==v_upper][col_c_a].mean())
                                if m_cantos > 9.5: tem_canto = True

                            def calc_btts(df_equipe, t_ref):
                                if df_equipe.empty: return 0
                                btts_count = len(df_equipe[(df_equipe['Gols_Mandante_FT'] > 0) & (df_equipe['Gols_Visitante_FT'] > 0)])
                                return (btts_count / len(df_equipe)) * 100

                            btts_media = (calc_btts(df_m_h, m_upper) + calc_btts(df_v_h, v_upper)) / 2
                            if btts_media >= 60: tem_ambas = True
                        except: pass

                icones = ""
                if tem_gol: icones += " 🔥⚽"
                if tem_canto: icones += " 🔥🚩"
                if tem_ambas: icones += " 🤝"

                odd_m = row.get('Odd Mandante', 0)
                odd_v = row.get('Odd Visitante', 0)
                selo_favorito = ""
                
                try:
                    v_m = float(str(odd_m).replace(',', '.'))
                    v_v = float(str(odd_v).replace(',', '.'))
                    if v_m < 1.4: selo_favorito = " 🌟"
                    elif v_m <= 1.8: selo_favorito = " ⭐"
                    elif v_v < 1.4: selo_favorito = " 🌟"
                    elif v_v <= 1.8: selo_favorito = " ⭐"
                    elif abs(v_m - v_v) <= 1.0: selo_favorito = " ⚖️"
                except: pass

                c1, c2, c3 = st.columns([4.2, 3.0, 1.3])
                with c1:
                    st.write(f"**{row['Hora']}** | ({pos_m}º) {mandante} vs {visitante} ({pos_v}º){icones}{selo_favorito}")
                with c2:
                    st.write(f"Odds: **{odd_m}** | **{row.get('Odd Empate',0)}** | **{odd_v}**")
                with c3:
                    if st.button("Analisar 🔍", key=f"btn_ag_{idx}_{m_upper[:3]}", use_container_width=True):
                        st.session_state.liga_scout = liga_upper
                        st.session_state.time_casa_scout = mandante
                        st.session_state.time_fora_scout = visitante
                        st.session_state.menu_ativo = "🔎 Scout"
                        st.rerun()

    # --- RANKINGS DE PERFORMANCE (MANTIDO) ---
    if not df_hist.empty and times_no_dia:
        st.divider()
        st.subheader(f"📊 Rankings de Performance - {st.session_state.data_exibicao}")
        
        times_dia_unicos = list(set([str(t).strip().upper() for t in times_no_dia]))
        rank_data = []

        col_c_h = 'Corners_H' if 'Corners_H' in df_hist_clean.columns else 'Cantos_Mandante'
        col_c_a = 'Corners_A' if 'Corners_A' in df_hist_clean.columns else 'Cantos_Visitante'
        col_sh_h = 'Shots_H' if 'Shots_H' in df_hist_clean.columns else 'Finalizacoes_Mandante'
        col_sh_a = 'Shots_A' if 'Shots_A' in df_hist_clean.columns else 'Finalizacoes_Visitante'

        for t in times_dia_unicos:
            df_t = df_hist_clean[(df_hist_clean['Mandante'].astype(str).str.upper() == t) | (df_hist_clean['Visitante'].astype(str).str.upper() == t)]
            if not df_t.empty:
                def get_fs(df_local, time_ref, c_h, c_a):
                    if c_h not in df_local.columns: return 0.0, 0.0
                    f = np.where(df_local['Mandante'].astype(str).str.upper()==time_ref, df_local[c_h], df_local[c_a]).mean()
                    s = np.where(df_local['Mandante'].astype(str).str.upper()==time_ref, df_local[c_a], df_local[c_h]).mean()
                    return f, s

                gm_f, gm_s = get_fs(df_t, t, 'Gols_Mandante_FT', 'Gols_Visitante_FT')
                cn_f, cn_s = get_fs(df_t, t, col_c_h, col_c_a)
                sh_f, sh_s = get_fs(df_t, t, col_sh_h, col_sh_a)

                rank_data.append({
                    "Time": t, "Gols FT F": gm_f, "Gols FT S": gm_s,
                    "Cantos FT F": cn_f, "Cantos FT S": cn_s,
                    "Chutes F": sh_f, "Chutes S": sh_s
                })
        
        if rank_data:
            df_rank = pd.DataFrame(rank_data)
            def plot_rank_cols(titulo, col_f, col_s):
                st.markdown(f"#### {titulo}")
                c_a, c_b = st.columns(2)
                with c_a:
                    st.dataframe(df_rank.sort_values(col_f, ascending=False).head(5)[["Time", col_f]], hide_index=True, use_container_width=True)
                with c_b:
                    st.dataframe(df_rank.sort_values(col_s, ascending=False).head(5)[["Time", col_s]], hide_index=True, use_container_width=True)

            plot_rank_cols("⚽ Gols FT", "Gols FT F", "Gols FT S")
            plot_rank_cols("🚩 Cantos FT", "Cantos FT F", "Cantos FT S")
            plot_rank_cols("👟 Chutes", "Chutes F", "Chutes S")
