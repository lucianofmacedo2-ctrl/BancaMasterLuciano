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
    st.title("📅 Agenda & Inteligência de Dados")
    
    brasil_tz = pytz.timezone('America/Sao_Paulo')
    hoje_dt = datetime.now(brasil_tz).date()

    # --- LEGENDA ---
    with st.expander("💡 Legenda do Radar de Valor", expanded=False):
        st.markdown("""
        * 🔥⚽ **Fogo + Gol**: Média combinada > 2.5 gols.
        * 🔥🚩 **Fogo + Canto**: Média combinada > 9.5 escanteios.
        * 🤝 **Ambas Sim**: Incidência de BTTS > 60%.
        * ⭐ **Favorito**: Odd 1.40 - 1.80 | 🌟 **Super Fav**: Odd < 1.40.
        * ⚖️ **Equilibrado**: Diferença de Odds ≤ 1.0.
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

    # --- PRÉ-PROCESSAMENTO DO HISTÓRICO (IMPORTANTE) ---
    if not df_hist.empty:
        # Garantir que colunas de cantos sejam numéricas
        cols_cantos = ['Corners_H', 'Corners_A', 'Total_Corners', 'Corners_H_HT', 'Corners_A_HT', 'Total_Corners_HT']
        for col in cols_cantos:
            if col in df_hist.columns:
                df_hist[col] = pd.to_numeric(df_hist[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)

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
                gm, gv = float(str(row['Gols_Mandante_FT']).replace(',','.')), float(str(row['Gols_Visitante_FT']).replace(',','.'))
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

    if 'data_exibicao' not in st.session_state: st.session_state.data_exibicao = hoje_dt.strftime('%d/%m/%Y')
    cols_btn = st.columns(3)
    datas_ops = [hoje_dt, hoje_dt + timedelta(days=1), hoje_dt + timedelta(days=2)]
    for i, label in enumerate(["📅 Hoje", "📅 Amanhã", "📅 Depois"]):
        if cols_btn[i].button(label, key=f"btn_n_{i}", use_container_width=True):
            st.session_state.data_exibicao = datas_ops[i].strftime('%d/%m/%Y')
            st.rerun()

    data_alvo = st.session_state.data_exibicao[0:5] 
    df_dia = df_agenda[df_agenda['Data'].str.contains(data_alvo, na=False)] if not df_agenda.empty else pd.DataFrame()

    sugestoes_gols = []
    sugestoes_cantos = []
    times_do_dia_tratados = []

    if df_dia.empty:
        st.warning(f"Sem jogos para {st.session_state.data_exibicao}.")
    else:
        for liga_orig in df_dia['Liga'].unique():
            st.markdown(f"#### 🏆 {liga_orig}")
            df_l = df_dia[df_dia['Liga'] == liga_orig]
            liga_tratada = tratar_string(liga_orig)

            for idx, row in df_l.iterrows():
                m_orig, v_orig = str(row['Mandante']), str(row['Visitante'])
                m_match = encontrar_time_similar(m_orig, lista_times_banco)
                v_match = encontrar_time_similar(v_orig, lista_times_banco)
                
                if m_match: times_do_dia_tratados.append(m_match)
                if v_match: times_do_dia_tratados.append(v_match)

                pos_m = dict_posicoes.get(f"{liga_tratada}_{m_match}", "?")
                if pos_m == "?" and m_match:
                    for k, p in dict_posicoes.items():
                        if k.endswith(f"_{m_match}"): pos_m = p; break
                pos_v = dict_posicoes.get(f"{liga_tratada}_{v_match}", "?")
                if pos_v == "?" and v_match:
                    for k, p in dict_posicoes.items():
                        if k.endswith(f"_{v_match}"): pos_v = p; break

                icones = ""
                try:
                    odd_m = float(str(row.get('Odd Mandante', 0)).replace(',','.'))
                    odd_v = float(str(row.get('Odd Visitante', 0)).replace(',','.'))
                    if odd_m < 1.4 or odd_v < 1.4: icones += " 🌟"
                    elif odd_m <= 1.8 or odd_v <= 1.8: icones += " ⭐"
                    if abs(odd_m - odd_v) <= 1.0: icones += " ⚖️"
                except: pass

                if not df_hist.empty and m_match and v_match:
                    h_m = df_hist[(df_hist['Mandante'].apply(tratar_string) == m_match) | (df_hist['Visitante'].apply(tratar_string) == m_match)]
                    h_v = df_hist[(df_hist['Mandante'].apply(tratar_string) == v_match) | (df_hist['Visitante'].apply(tratar_string) == v_match)]
                    if not h_m.empty and not h_v.empty:
                        m_gols = (h_m['Total_Gols_FT'].mean() + h_v['Total_Gols_FT'].mean()) / 2
                        if m_gols > 3.0: 
                            icones += " 🔥⚽"
                            sugestoes_gols.append({"jogo": f"{m_orig} vs {v_orig}", "valor": m_gols})
                        
                        if 'Total_Corners' in df_hist.columns:
                            m_cantos = (h_m['Total_Corners'].mean() + h_v['Total_Corners'].mean()) / 2
                            if m_cantos > 11.0: 
                                icones += " 🔥🚩"
                                sugestoes_cantos.append({"jogo": f"{m_orig} vs {v_orig}", "valor": m_cantos})

                c1, c2, c3 = st.columns([4.2, 3.0, 1.3])
                with c1: st.write(f"**{row['Hora']}** | ({pos_m}º) {m_orig} vs {v_orig} ({pos_v}º){icones}")
                with c2: st.write(f"Odds: **{row.get('Odd Mandante','-')}** | **{row.get('Odd Empate','-')}** | **{row.get('Odd Visitante','-')}**")
                with c3:
                    if st.button("Analisar 🔍", key=f"btn_an_{idx}", use_container_width=True):
                        st.session_state.time_casa_scout, st.session_state.time_fora_scout = m_orig, v_orig
                        st.session_state.menu_ativo = "🔎 Scout"
                        st.rerun()

    st.divider()
    st.subheader("🎯 Sugestões do Dia (Top 5)")
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.write("⚽ **Over 2.5 Gols FT**")
        s_gols = sorted(sugestoes_gols, key=lambda x: x['valor'], reverse=True)[:5]
        for s in s_gols: st.success(f"{s['jogo']} ({s['valor']:.2f})")
    with col_s2:
        st.write("🚩 **Over 9.5 Cantos FT**")
        s_cantos = sorted(sugestoes_cantos, key=lambda x: x['valor'], reverse=True)[:5]
        for s in s_cantos: st.warning(f"{s['jogo']} ({s['valor']:.2f})")

    if not df_hist.empty and times_do_dia_tratados:
        st.divider()
        st.subheader(f"📊 Top 5 Performance (Times que jogam em {st.session_state.data_exibicao})")
        
        times_stats = []
        df_h = df_hist.copy()
        df_h['M_T'] = df_h['Mandante'].apply(tratar_string)
        df_h['V_T'] = df_h['Visitante'].apply(tratar_string)
        
        for t in list(set(times_do_dia_tratados)):
            jogos_t = df_h[(df_h['M_T'] == t) | (df_h['V_T'] == t)]
            if jogos_t.empty: continue
            
            # Cálculo de médias garantindo numérico
            gm_ft = jogos_t.apply(lambda r: r['Gols_Mandante_FT'] if r['M_T'] == t else r['Gols_Visitante_FT'], axis=1).mean()
            gs_ft = jogos_t.apply(lambda r: r['Gols_Visitante_FT'] if r['M_T'] == t else r['Gols_Mandante_FT'], axis=1).mean()
            gm_ht = jogos_t.apply(lambda r: r['Gols_Mandante_HT'] if r['M_T'] == t else r['Gols_Visitante_HT'], axis=1).mean()
            gs_ht = jogos_t.apply(lambda r: r['Gols_Visitante_HT'] if r['M_T'] == t else r['Gols_Mandante_HT'], axis=1).mean()
            
            # Cantos (Corners_H, Corners_A, Total_Corners, Corners_H_HT, Corners_A_HT, Total_Corners_HT)
            cf_ft = jogos_t.apply(lambda r: r['Corners_H'] if r['M_T'] == t else r['Corners_A'], axis=1).mean()
            cs_ft = jogos_t.apply(lambda r: r['Corners_A'] if r['M_T'] == t else r['Corners_H'], axis=1).mean()
            cf_ht = jogos_t.apply(lambda r: r['Corners_H_HT'] if r['M_T'] == t else r['Corners_A_HT'], axis=1).mean()
            cs_ht = jogos_t.apply(lambda r: r['Corners_A_HT'] if r['M_T'] == t else r['Corners_H_HT'], axis=1).mean()
            
            times_stats.append({
                "Time": t, 
                "GM FT": gm_ft, "GS FT": gs_ft, "GM HT": gm_ht, "GS HT": gs_ht,
                "CF FT": cf_ft, "CS FT": cs_ft, "CF HT": cf_ht, "CS HT": cs_ht
            })
        
        df_rank = pd.DataFrame(times_stats)
        if not df_rank.empty:
            r1, r2 = st.columns(2)
            with r1:
                st.write("⚽ **Marcam + (FT)**")
                st.table(df_rank.sort_values("GM FT", ascending=False)[["Time", "GM FT"]].head(5))
            with r2:
                st.write("🥅 **Sofrem + (FT)**")
                st.table(df_rank.sort_values("GS FT", ascending=False)[["Time", "GS FT"]].head(5))

            r3, r4 = st.columns(2)
            with r3:
                st.write("⏱️ **Marcam + HT**")
                st.table(df_rank.sort_values("GM HT", ascending=False)[["Time", "GM HT"]].head(5))
            with r4:
                st.write("📉 **Sofrem + HT**")
                st.table(df_rank.sort_values("GS HT", ascending=False)[["Time", "GS HT"]].head(5))

            r5, r6 = st.columns(2)
            with r5:
                st.write("🚩 **Cantos Feitos (FT)**")
                st.table(df_rank.sort_values("CF FT", ascending=False)[["Time", "CF FT"]].head(5))
            with r6:
                st.write("🚩 **Cantos Sofridos (FT)**")
                st.table(df_rank.sort_values("CS FT", ascending=False)[["Time", "CS FT"]].head(5))

            r7, r8 = st.columns(2)
            with r7:
                st.write("🚩 **Cantos Feitos (HT)**")
                st.table(df_rank.sort_values("CF HT", ascending=False)[["Time", "CF HT"]].head(5))
            with r8:
                st.write("🚩 **Cantos Sofridos (HT)**")
                st.table(df_rank.sort_values("CS HT", ascending=False)[["Time", "CS HT"]].head(5))
