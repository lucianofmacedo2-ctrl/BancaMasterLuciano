import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Links dos arquivos
URL_AGENDA = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.csv"

def mostrar_jogos(df_hist): # Agora aceita o df_hist vindo do app.py
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
                
                # --- LÓGICA DE ALERTAS (ATUALIZADA PARA AS NOVAS COLUNAS) ---
                if not df_hist.empty:
                    df_m = df_hist[df_hist['Mandante'] == mandante]
                    df_v = df_hist[df_hist['Visitante'] == visitante]
                    
                    if not df_m.empty and not df_v.empty:
                        # Média de Gols Total (Mandante e Visitante)
                        m_gols = (df_m['Total_Gols_FT'].mean() + df_v['Total_Gols_FT'].mean()) / 2
                        
                        # Média de Cantos (Usando Corners_H e Corners_A se existirem)
                        col_c_h = 'Corners_H' if 'Corners_H' in df_hist.columns else 'Cantos_Mandante'
                        col_c_a = 'Corners_A' if 'Corners_A' in df_hist.columns else 'Cantos_Visitante'
                        
                        if col_c_h in df_hist.columns:
                            m_cantos = ( (df_m[col_c_h].mean() + df_m[col_c_a].mean()) + 
                                         (df_v[col_c_h].mean() + df_v[col_c_a].mean()) ) / 2
                            if m_cantos > 9.5: tem_canto = True
                        
                        if m_gols > 2.5: tem_gol = True

                # Formatação dos Ícones
                icones = ""
                if tem_gol and tem_canto: icones = " 🔥⚽🚩"
                elif tem_gol: icones = " 🔥⚽"
                elif tem_canto: icones = " 🔥🚩"

                # --- LÓGICA DE ODDS E EQUILÍBRIO ---
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

    # --- RANKING TOP 5 (AJUSTADO PARA NOVAS COLUNAS) ---
    if not df_hist.empty and times_no_dia:
        st.divider()
        st.subheader(f"📊 Rankings de Performance - {st.session_state.data_exibicao}")
        
        times_dia_unicos = list(set(times_no_dia))
        rank_data = []

        # Identificar colunas corretas de Chutes e Cantos
        col_ch_h = 'ShotsOnTarget_H' if 'ShotsOnTarget_H' in df_hist.columns else 'Chutes_Gol_Mandante'
        col_ch_a = 'ShotsOnTarget_A' if 'ShotsOnTarget_A' in df_hist.columns else 'Chutes_Gol_Visitante'
        col_cn_h = 'Corners_H' if 'Corners_H' in df_hist.columns else 'Cantos_Mandante'
        col_cn_a = 'Corners_A' if 'Corners_A' in df_hist.columns else 'Cantos_Visitante'

        for t in times_dia_unicos:
            df_t = df_hist[(df_hist['Mandante'] == t) | (df_hist['Visitante'] == t)]
            if not df_t.empty:
                # Gols Marcados e Sofridos
                gm = np.where(df_t['Mandante']==t, df_t['Gols_Mandante_FT'], df_t['Gols_Visitante_FT']).mean()
                gs = np.where(df_t['Mandante']==t, df_t['Gols_Visitante_FT'], df_t['Gols_Mandante_FT']).mean()
                # Gols HT
                gm_ht = np.where(df_t['Mandante']==t, df_t['Gols_Mandante_HT'], df_t['Gols_Visitante_HT']).mean()
                gs_ht = np.where(df_t['Mandante']==t, df_t['Gols_Visitante_HT'], df_t['Gols_Mandante_HT']).mean()
                
                # Cantos e Chutes (se colunas existirem)
                cm = 0; chm = 0
                if col_cn_h in df_hist.columns:
                    cm = np.where(df_t['Mandante']==t, df_t[col_cn_h], df_t[col_cn_a]).mean()
                if col_ch_h in df_hist.columns:
                    chm = np.where(df_t['Mandante']==t, df_t[col_ch_h], df_t[col_ch_a]).mean()

                rank_data.append({
                    "Time": t,
                    "Gols FT M": gm, "Gols FT S": gs,
                    "Gols HT M": gm_ht, "Gols HT S": gs_ht,
                    "Cantos M": cm, "Chutes M": chm
                })
        
        if rank_data:
            df_rank = pd.DataFrame(rank_data)
            c_rank1, c_rank2 = st.columns(2)
            with c_rank1:
                st.markdown("#### ⚽ Top Gols FT (Marcados)")
                st.dataframe(df_rank.sort_values("Gols FT M", ascending=False).head(5)[["Time", "Gols FT M"]], hide_index=True)
            with c_rank2:
                st.markdown("#### 🚩 Top Cantos (Médias)")
                st.dataframe(df_rank.sort_values("Cantos M", ascending=False).head(5)[["Time", "Cantos M"]], hide_index=True)
