import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Links dos arquivos
URL_AGENDA = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.csv"

def mostrar_jogos(df_hist): 
    st.title("📅 Agenda de Jogos")

    with st.expander("💡 Entenda os Sinais de Alerta (Radar de Valor)", expanded=True):
        st.markdown("""
        No **Banca Master Luciano**, nosso algoritmo identifica automaticamente os melhores jogos para operar:
        * 🔥⚽ **Fogo + Gol**: Jogo com tendência altíssima de **Over 2.5 Gols**.
        * 🔥🚩 **Fogo + Canto**: Jogo com tendência altíssima de **Over 9.5 Cantos**.
        * 🔥⚽🚩 **Fogo Combo**: Jogo com ambas as tendências (Gols e Cantos).
        * ⚖️ **Equilibrado**: Jogo onde o gap entre as odds é menor ou igual a 1.0.
        * 🔍 **Analisar**: Clique para ver o scout detalhado de cada equipe.
        """)
    
    @st.cache_data(ttl=60)
    def carregar_agenda(url):
        try:
            df = pd.read_csv(url, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = [c.strip() for c in df.columns]
            df = df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
            return df
        except: return pd.DataFrame()

    df_agenda = carregar_agenda(URL_AGENDA)

    if df_agenda.empty or 'Data' not in df_agenda.columns:
        st.error("Erro ao carregar a agenda de jogos.")
        return

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
        if cols_btn[i].button(labels[i], key=f"nav_date_{i}", use_container_width=True):
            st.session_state.data_sel_formatos = formatar_data_busca(datas_opcoes[i])
            st.session_state.data_exibicao = datas_opcoes[i].strftime('%d/%m/%Y')
            st.rerun()

    st.info(f"Mostrando jogos de: **{st.session_state.data_exibicao}**")

    df_dia = df_agenda[df_agenda['Data'].isin(st.session_state.data_sel_formatos)]

    times_no_dia = [] 

    if df_dia.empty:
        st.warning(f"Nenhum jogo encontrado para {st.session_state.data_exibicao}.")
    else:
        for liga in df_dia['Liga'].unique():
            df_l = df_dia[df_dia['Liga'] == liga]
            st.markdown(f"#### 🏆 {liga}")
            
            for idx, row in df_l.iterrows():
                mandante, visitante = row['Mandante'], row['Visitante']
                times_no_dia.extend([mandante, visitante])
                
                tem_gol = False
                tem_canto = False
                
                if not df_hist.empty:
                    df_m = df_hist[df_hist['Mandante'] == mandante]
                    df_v = df_hist[df_hist['Visitante'] == visitante]
                    
                    if not df_m.empty and not df_v.empty:
                        m_gols = (df_m['Total_Gols_FT'].mean() + df_v['Total_Gols_FT'].mean()) / 2
                        col_c_h = 'Corners_H' if 'Corners_H' in df_hist.columns else 'Cantos_Mandante'
                        col_c_a = 'Corners_A' if 'Corners_A' in df_hist.columns else 'Cantos_Visitante'
                        
                        if col_c_h in df_hist.columns:
                            m_cantos = ( (df_m[col_c_h].mean() + df_m[col_c_a].mean()) + 
                                         (df_v[col_c_h].mean() + df_v[col_c_a].mean()) ) / 2
                            if m_cantos > 9.5: tem_canto = True
                        
                        if m_gols > 2.5: tem_gol = True

                icones = ""
                if tem_gol and tem_canto: icones = " 🔥⚽🚩"
                elif tem_gol: icones = " 🔥⚽"
                elif tem_canto: icones = " 🔥🚩"

                odd_m = row.get('Odd Mandante', 0)
                odd_e = row.get('Odd Empate', 0)
                odd_v = row.get('Odd Visitante', 0)
                
                alerta_equilibrio = ""
                try:
                    val_m = float(str(odd_m).replace(',', '.'))
                    val_v = float(str(odd_v).replace(',', '.'))
                    if abs(val_m - val_v) <= 1.0: alerta_equilibrio = " ⚖️"
                except: pass

                c1, c2, c3 = st.columns([4.2, 3.0, 1.3])
                with c1:
                    st.write(f"**{row['Hora']}** | {mandante} vs {visitante}{icones}{alerta_equilibrio}")
                with c2:
                    st.write(f"Odds: **{odd_m}** | **{odd_e}** | **{odd_v}**")
                with c3:
                    if st.button("Analisar 🔍", key=f"btn_ag_{idx}_{mandante[:3]}", use_container_width=True):
                        st.session_state.liga_scout = row['Liga']
                        st.session_state.time_casa_scout = mandante
                        st.session_state.time_fora_scout = visitante
                        st.session_state.menu_ativo = "🔎 Scout"
                        st.rerun()

    # --- RANKINGS DE PERFORMANCE EXPANDIDOS ---
    if not df_hist.empty and times_no_dia:
        st.divider()
        st.subheader(f"📊 Rankings de Performance - {st.session_state.data_exibicao}")
        
        times_dia_unicos = list(set(times_no_dia))
        rank_data = []

        # Mapeamento dinâmico de colunas
        c_cn_h = 'Corners_H' if 'Corners_H' in df_hist.columns else 'Cantos_Mandante'
        c_cn_a = 'Corners_A' if 'Corners_A' in df_hist.columns else 'Cantos_Visitante'
        c_cn_ht_h = 'Corners_HT_H' if 'Corners_HT_H' in df_hist.columns else None
        c_cn_ht_a = 'Corners_HT_A' if 'Corners_HT_A' in df_hist.columns else None
        c_sh_h = 'Shots_H' if 'Shots_H' in df_hist.columns else 'Finalizacoes_Mandante'
        c_sh_a = 'Shots_A' if 'Shots_A' in df_hist.columns else 'Finalizacoes_Visitante'
        c_cd_h = 'Cards_Total_H' if 'Cards_Total_H' in df_hist.columns else 'Cartoes_Mandante'
        c_cd_a = 'Cards_Total_A' if 'Cards_Total_A' in df_hist.columns else 'Cartoes_Visitante'

        for t in times_dia_unicos:
            df_t = df_hist[(df_hist['Mandante'] == t) | (df_hist['Visitante'] == t)]
            if not df_t.empty:
                # Função interna para calcular Feitos e Sofridos
                def get_fs(df_local, time_ref, col_h, col_a):
                    if col_h not in df_local.columns: return 0.0, 0.0
                    f = np.where(df_local['Mandante']==time_ref, df_local[col_h], df_local[col_a]).mean()
                    s = np.where(df_local['Mandante']==time_ref, df_local[col_a], df_local[col_h]).mean()
                    return f, s

                gm_f, gm_s = get_fs(df_t, t, 'Gols_Mandante_FT', 'Gols_Visitante_FT')
                ght_f, ght_s = get_fs(df_t, t, 'Gols_Mandante_HT', 'Gols_Visitante_HT')
                cn_f, cn_s = get_fs(df_t, t, c_cn_h, c_cn_a)
                sh_f, sh_s = get_fs(df_t, t, c_sh_h, c_sh_a)
                cd_f, cd_s = get_fs(df_t, t, c_cd_h, c_cd_a)
                
                # Cantos HT (Opcional)
                cnht_f, cnht_s = (0, 0)
                if c_cn_ht_h: cnht_f, cnht_s = get_fs(df_t, t, c_cn_ht_h, c_cn_ht_a)

                rank_data.append({
                    "Time": t,
                    "Gols FT F": gm_f, "Gols FT S": gm_s,
                    "Gols HT F": ght_f, "Gols HT S": ght_s,
                    "Cantos FT F": cn_f, "Cantos FT S": cn_s,
                    "Cantos HT F": cnht_f, "Cantos HT S": cnht_s,
                    "Chutes F": sh_f, "Chutes S": sh_s,
                    "Cartões F": cd_f, "Cartões S": cd_s
                })
        
        if rank_data:
            df_rank = pd.DataFrame(rank_data)
            
            def plot_rank_cols(titulo, col_f, col_s):
                st.markdown(f"#### {titulo}")
                c_a, c_b = st.columns(2)
                with c_a:
                    st.caption("🔝 Maiores Médias (Feitos)")
                    st.dataframe(df_rank.sort_values(col_f, ascending=False).head(5)[["Time", col_f]], hide_index=True, use_container_width=True)
                with c_b:
                    st.caption("⚠️ Maiores Médias (Sofridos)")
                    st.dataframe(df_rank.sort_values(col_s, ascending=False).head(5)[["Time", col_s]], hide_index=True, use_container_width=True)

            # Renderização das Categorias Pedidas
            plot_rank_cols("⚽ Gols FT (Jogo Todo)", "Gols FT F", "Gols FT S")
            plot_rank_cols("⏱️ Gols HT (1º Tempo)", "Gols HT F", "Gols HT S")
            plot_rank_cols("🚩 Cantos FT (Escanteios)", "Cantos FT F", "Cantos FT S")
            
            if c_cn_ht_h:
                plot_rank_cols("🚩 Cantos HT (1º Tempo)", "Cantos HT F", "Cantos HT S")
            
            plot_rank_cols("👟 Chutes (Finalizações)", "Chutes F", "Chutes S")
            plot_rank_cols("🟨 Cartões (Total)", "Cartões F", "Cartões S")
