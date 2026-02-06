import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import unicodedata
from difflib import get_close_matches

# Links dos arquivos
URL_AGENDA = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.csv"

def mostrar_jogos(df_hist): 
    st.title("📅 Agenda de Jogos")
    
    brasil_tz = pytz.timezone('America/Sao_Paulo')
    hoje_dt = datetime.now(brasil_tz).date()

    # --- LEGENDA COMPLETA ---
    with st.expander("💡 Entenda os Sinais de Alerta (Radar de Valor)", expanded=True):
        st.markdown("""
        * 🔥⚽ **Fogo + Gol**: Tendência altíssima de **Over 2.5 Gols**.
        * 🔥🚩 **Fogo + Canto**: Tendência altíssima de **Over 9.5 Escanteios**.
        * 🤝 **Ambas Sim**: Mais de 60% de incidência de **Ambas Marcam**.
        * ⭐ **Favorito**: Odd entre 1.40 e 1.80.
        * 🌟 **Super Favorito**: Odd abaixo de 1.40.
        * ⚖️ **Equilibrado**: Diferença entre as odds de Mandante e Visitante menor ou igual a 1.0.
        """)

    def tratar_string(texto):
        if not texto or pd.isna(texto): return ""
        texto = str(texto).replace("Ã³", "o").replace("Ã©", "e").replace("Ã¡", "a").replace("Ã", "a")
        nksf = unicodedata.normalize('NFKD', texto)
        texto = "".join([c for c in nksf if not unicodedata.combining(c)])
        texto = texto.upper().replace(".", "").replace("-", " ").strip()
        return " ".join(texto.split())

    @st.cache_data(ttl=60)
    def carregar_agenda(url):
        try:
            df = pd.read_csv(url, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = [c.strip() for c in df.columns]
            return df
        except: return pd.DataFrame()

    def obter_classificacao(df_input):
        if df_input is None or df_input.empty: return {}, []
        df_c = df_input.copy()
        df_c['M_TRATADO'] = df_c['Mandante'].apply(tratar_string)
        df_c['V_TRATADO'] = df_c['Visitante'].apply(tratar_string)
        df_c['LIGA_TRATADA'] = df_c['Liga'].apply(tratar_string)
        stats = {}
        todos_os_times = set()
        for _, row in df_c.iterrows():
            liga = row['LIGA_TRATADA']
            m, v = row['M_TRATADO'], row['V_TRATADO']
            todos_os_times.update([m, v])
            try:
                gm, gv = float(row['Gols_Mandante_FT']), float(row['Gols_Visitante_FT'])
            except: continue
            if liga not in stats: stats[liga] = {}
            for t in [m, v]:
                if t not in stats[liga]: stats[liga][t] = {'pts': 0, 'sg': 0}
            if gm > gv: stats[liga][m]['pts'] += 3
            elif gv > gm: stats[liga][v]['pts'] += 3
            else:
                stats[liga][m]['pts'] += 1; stats[liga][v]['pts'] += 1
            stats[liga][m]['sg'] += (gm - gv)
            stats[liga][v]['sg'] += (gv - gm)
        posicoes = {}
        for liga in stats:
            ranking = sorted(stats[liga].items(), key=lambda x: (x[1]['pts'], x[1]['sg']), reverse=True)
            for i, (time, _) in enumerate(ranking):
                posicoes[f"{liga}_{time}"] = i + 1
        return posicoes, list(todos_os_times)

    df_agenda = carregar_agenda(URL_AGENDA)
    dict_posicoes, lista_times_banco = obter_classificacao(df_hist)

    def encontrar_time_similar(nome_agenda, lista_referencia):
        nome_agenda = tratar_string(nome_agenda)
        if nome_agenda in lista_referencia: return nome_agenda
        matches = get_close_matches(nome_agenda, lista_referencia, n=1, cutoff=0.6)
        return matches[0] if matches else None

    if 'data_exibicao' not in st.session_state:
        st.session_state.data_exibicao = hoje_dt.strftime('%d/%m/%Y')

    cols_btn = st.columns(3)
    datas_ops = [hoje_dt, hoje_dt + timedelta(days=1), hoje_dt + timedelta(days=2)]
    labels = ["📅 Hoje", "📅 Amanhã", "📅 Depois"]
    for i in range(3):
        if cols_btn[i].button(labels[i], key=f"btn_nav_{i}", use_container_width=True):
            st.session_state.data_exibicao = datas_ops[i].strftime('%d/%m/%Y')
            st.rerun()

    st.info(f"Mostrando jogos de: **{st.session_state.data_exibicao}**")

    data_alvo = st.session_state.data_exibicao[0:5] 
    df_dia = df_agenda[df_agenda['Data'].str.contains(data_alvo, na=False)]

    if df_dia.empty:
        st.warning(f"Nenhum jogo encontrado para {st.session_state.data_exibicao}.")
    else:
        for liga_orig in df_dia['Liga'].unique():
            st.markdown(f"#### 🏆 {liga_orig}")
            df_l = df_dia[df_dia['Liga'] == liga_orig]
            liga_tratada = tratar_string(liga_orig)

            for idx, row in df_l.iterrows():
                m_orig, v_orig = str(row['Mandante']), str(row['Visitante'])
                m_match = encontrar_time_similar(m_orig, lista_times_banco)
                v_match = encontrar_time_similar(v_orig, lista_times_banco)

                pos_m = dict_posicoes.get(f"{liga_tratada}_{m_match}", "?")
                if pos_m == "?" and m_match:
                    for k, p in dict_posicoes.items():
                        if k.endswith(f"_{m_match}"): pos_m = p; break
                pos_v = dict_posicoes.get(f"{liga_tratada}_{v_match}", "?")
                if pos_v == "?" and v_match:
                    for k, p in dict_posicoes.items():
                        if k.endswith(f"_{v_match}"): pos_v = p; break

                # --- LÓGICA DE ICONES (RADAR) ---
                icones = ""
                try:
                    odd_m = float(str(row.get('Odd Mandante', 0)).replace(',','.'))
                    odd_v = float(str(row.get('Odd Visitante', 0)).replace(',','.'))
                    # Favoritos
                    if odd_m < 1.4 or odd_v < 1.4: icones += " 🌟"
                    elif odd_m <= 1.8 or odd_v <= 1.8: icones += " ⭐"
                    # Equilibrado (Diferença entre odds <= 1.0)
                    if abs(odd_m - odd_v) <= 1.0: icones += " ⚖️"
                except: pass

                if not df_hist.empty and m_match and v_match:
                    h_m = df_hist[(df_hist['Mandante'].apply(tratar_string) == m_match) | (df_hist['Visitante'].apply(tratar_string) == m_match)]
                    h_v = df_hist[(df_hist['Mandante'].apply(tratar_string) == v_match) | (df_hist['Visitante'].apply(tratar_string) == v_match)]
                    if not h_m.empty and not h_v.empty:
                        try:
                            avg_g = (h_m['Total_Gols_FT'].mean() + h_v['Total_Gols_FT'].mean()) / 2
                            if avg_g > 3.0: icones += " 🔥⚽"
                            if 'Total_Cantos_FT' in df_hist.columns:
                                avg_c = (h_m['Total_Cantos_FT'].mean() + h_v['Total_Cantos_FT'].mean()) / 2
                                if avg_c > 11.0: icones += " 🔥🚩"
                            b_m = (len(h_m[(h_m['Gols_Mandante_FT']>0) & (h_m['Gols_Visitante_FT']>0)]) / len(h_m))
                            b_v = (len(h_v[(h_v['Gols_Mandante_FT']>0) & (h_v['Gols_Visitante_FT']>0)]) / len(h_v))
                            if (b_m + b_v) / 2 >= 0.60: icones += " 🤝"
                        except: pass

                c1, c2, c3 = st.columns([4.2, 3.0, 1.3])
                with c1:
                    st.write(f"**{row['Hora']}** | ({pos_m}º) {m_orig} vs {v_orig} ({pos_v}º){icones}")
                with c2:
                    st.write(f"Odds: **{row.get('Odd Mandante','-')}** | **{row.get('Odd Empate','-')}** | **{row.get('Odd Visitante','-')}**")
                with c3:
                    if st.button("Analisar 🔍", key=f"btn_an_{idx}", use_container_width=True):
                        st.session_state.time_casa_scout = m_orig
                        st.session_state.time_fora_scout = v_orig
                        st.session_state.menu_ativo = "🔎 Scout"
                        st.rerun()
