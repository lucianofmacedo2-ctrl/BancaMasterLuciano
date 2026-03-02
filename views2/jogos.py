import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import unicodedata
from scipy.stats import poisson

# --- CONFIGURAÇÕES E LINKS ---
URL_AGENDA = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.csv"

# --- 1. FUNÇÕES DE TRATAMENTO E LÓGICA DE RANKING (PRESERVADAS) ---

def tratar_string_fast(texto):
    if not texto or pd.isna(texto): return ""
    texto = str(texto).upper()
    mapa = {"Ã³": "O", "Ã©": "E", "Ã¡": "A", "Ã£": "A", "Ãª": "E", "Ã­": "I", "Ã§": "C", "Ã": "A", "Ã²": "O", "Ã¹": "U"}
    for erro, correto in mapa.items():
        texto = texto.replace(erro, correto)
    nksf = unicodedata.normalize('NFKD', texto)
    texto = "".join([c for c in nksf if not unicodedata.combining(c)])
    return " ".join(texto.replace(".", "").replace("-", " ").split()).strip()

@st.cache_data(ttl=3600)
def preparar_base_e_ranking(df_hist):
    if df_hist is None or df_hist.empty: 
        return pd.DataFrame(), {}, {}, set()
    
    df = df_hist.copy()
    if 'Data' in df.columns:
        df['Data_DT'] = pd.to_datetime(df['Data'], errors='coerce')

    cols_num = [
        'Corners_H', 'Corners_A', 'Total_Corners', 'Total_Gols_FT', 
        'Total_Gols_HT', 'Total_Corners_HT', 'Gols_Mandante_FT', 
        'Gols_Visitante_FT', 'Gols_Mandante_HT', 'Gols_Visitante_HT',
        'Corners_H_HT', 'Corners_A_HT', 'Odd_Mandante_FT', 'Odd_Visitante_FT'
    ]
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    
    df['BTTS_Realizado'] = 0
    if 'Gols_Mandante_FT' in df.columns and 'Gols_Visitante_FT' in df.columns:
        df['BTTS_Realizado'] = ((df['Gols_Mandante_FT'] > 0) & (df['Gols_Visitante_FT'] > 0)).astype(int)

    df['M_T'] = df['Mandante'].apply(tratar_string_fast)
    df['V_T'] = df['Visitante'].apply(tratar_string_fast)
    df['L_T'] = df['Liga'].apply(tratar_string_fast)

    dict_posicoes = {}
    df_rank = df.copy()
    for liga, dados_liga in df_rank.groupby('L_T'):
        stats_rank = {}
        for _, r in dados_liga.iterrows():
            for t, gf, gs in [(r['M_T'], r['Gols_Mandante_FT'], r['Gols_Visitante_FT']), 
                                (r['V_T'], r['Gols_Visitante_FT'], r['Gols_Mandante_FT'])]:
                if t not in stats_rank: stats_rank[t] = {'pts': 0, 'v': 0, 'sg': 0, 'gf': 0}
                stats_rank[t]['gf'] += gf
                stats_rank[t]['sg'] += (gf - gs)
                if gf > gs: stats_rank[t]['pts'] += 3; stats_rank[t]['v'] += 1
                elif gf == gs: stats_rank[t]['pts'] += 1
        ranking = sorted(stats_rank.items(), key=lambda x: (x[1]['pts'], x[1]['v'], x[1]['sg'], x[1]['gf']), reverse=True)
        for i, (time, _) in enumerate(ranking):
            dict_posicoes[f"{liga}_{time}"] = i + 1

    m_stats = df.groupby('M_T').agg({col: 'mean' for col in cols_num + ['BTTS_Realizado'] if col in df.columns})
    v_stats = df.groupby('V_T').agg({col: 'mean' for col in cols_num + ['BTTS_Realizado'] if col in df.columns})

    stats_times = {}
    todos_times = set(df['M_T'].unique()) | set(df['V_T'].unique())
    for t in todos_times:
        s_m = m_stats.loc[t] if t in m_stats.index else None
        s_v = v_stats.loc[t] if t in v_stats.index else None
        if s_m is not None and s_v is not None: stats_times[t] = (s_m + s_v) / 2
        elif s_m is not None: stats_times[t] = s_m
        else: stats_times[t] = s_v

    return df, stats_times, dict_posicoes, todos_times

# --- 2. FUNÇÃO PRINCIPAL ---

def mostrar_jogos(df_hist_input):
    st.title("📅 Agenda & Inteligência de Dados")
    
    if "id_analisar" not in st.session_state: st.session_state.id_analisar = None
    if "id_simular" not in st.session_state: st.session_state.id_simular = None

    brasil_tz = pytz.timezone('America/Sao_Paulo')
    hoje_dt = datetime.now(brasil_tz).date()
    if 'data_ex_jogos' not in st.session_state: st.session_state.data_ex_jogos = hoje_dt.strftime('%d/%m/%Y')

    df_hist, dict_stats, dict_pos, _ = preparar_base_e_ranking(df_hist_input)

    @st.cache_data(ttl=300)
    def carregar_agenda_fast(url):
        try:
            df = pd.read_csv(url, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = [c.strip() for c in df.columns]
            return df
        except: return pd.DataFrame()

    df_agenda = carregar_agenda_fast(URL_AGENDA)
    
    c_data = st.columns(3)
    datas_ops = [hoje_dt, hoje_dt + timedelta(days=1), hoje_dt + timedelta(days=2)]
    labels = ["📅 Hoje", "📅 Amanhã", "📅 Depois"]
    for i in range(3):
        if c_data[i].button(labels[i], key=f"nav_{i}", use_container_width=True):
            st.session_state.data_ex_jogos = datas_ops[i].strftime('%d/%m/%Y')
            st.rerun()

    data_alvo = st.session_state.data_ex_jogos[0:5]
    df_dia = df_agenda[df_agenda['Data'].str.contains(data_alvo, na=False)] if not df_agenda.empty else pd.DataFrame()

    if df_dia.empty:
        st.warning(f"Sem jogos para {st.session_state.data_ex_jogos}."); return

    sugestoes = {"gFT":[], "cFT":[], "gHT":[], "btts":[], "cHT":[]}
    times_do_dia = []

    for liga, df_l in df_dia.groupby('Liga'):
        st.markdown(f"#### 🏆 {liga}")
        liga_t = tratar_string_fast(liga)
        for idx, row in df_l.iterrows():
            m_orig, v_orig = str(row['Mandante']), str(row['Visitante'])
            m_t, v_t = tratar_string_fast(m_orig), tratar_string_fast(v_orig)
            p_m = dict_pos.get(f"{liga_t}_{m_t}", "?")
            p_v = dict_pos.get(f"{liga_t}_{v_t}", "?")
            
            icones = ""
            if m_t in dict_stats and v_t in dict_stats:
                s1, s2 = dict_stats[m_t], dict_stats[v_t]
                m_gFT = (s1['Total_Gols_FT'] + s2['Total_Gols_FT']) / 2
                m_gHT = (s1['Total_Gols_HT'] + s2['Total_Gols_HT']) / 2
                m_btts = (s1['BTTS_Realizado'] + s2['BTTS_Realizado']) / 2
                m_cFT = (s1['Total_Corners'] + s2['Total_Corners']) / 2
                m_cHT = (s1['Total_Corners_HT'] + s2['Total_Corners_HT']) / 2
                times_do_dia.extend([m_t, v_t])
                
                if m_gFT > 3.0: 
                    icones += " 🔥⚽"
                    sugestoes["gFT"].append({"j": f"{m_orig} vs {v_orig}", "v": m_gFT})
                if m_gHT >= 1.0: 
                    icones += " ⏱️"
                    sugestoes["gHT"].append({"j": f"{m_orig} vs {v_orig}", "v": m_gHT})
                if m_btts > 0.65: 
                    icones += " 🤝"
                    sugestoes["btts"].append({"j": f"{m_orig} vs {v_orig}", "v": m_btts})
                if m_cFT > 11.0: 
                    icones += " 🔥🚩"
                    sugestoes["cFT"].append({"j": f"{m_orig} vs {v_orig}", "v": m_cFT})
                if m_cHT > 4.5:
                    sugestoes["cHT"].append({"j": f"{m_orig} vs {v_orig}", "v": m_cHT})

            c1, c2, c3, c4 = st.columns([4.2, 2.8, 1.5, 1.5])
            with c1: st.write(f"**{row['Hora']}** | ({p_m}º) {m_orig} vs {v_orig} ({p_v}º){icones}")
            with c2: st.caption(f"Odds: {row.get('Odd Mandante','-')} | {row.get('Odd Visitante','-')}")
            with c3:
                if st.button("Analisar 🔍", key=f"a_{idx}", use_container_width=True):
                    st.session_state.id_analisar = idx if st.session_state.id_analisar != idx else None
                    st.session_state.id_simular = None
            with c4:
                if st.button("Simular 🎲", key=f"s_{idx}", use_container_width=True):
                    st.session_state.id_simular = idx if st.session_state.id_simular != idx else None
                    st.session_state.id_analisar = None

            # --- QUADROS PREMIUM DE ANÁLISE (CENTRALIZAÇÃO ABSOLUTA) ---
            if st.session_state.id_analisar == idx:
                with st.container(border=True):
                    # Configuração para forçar alinhamento central em cada tipo de coluna
                    config_p = {
                        "Jogos": st.column_config.TextColumn("Jogos", alignment="center"),
                        "Data": st.column_config.TextColumn("Data", alignment="center"),
                        "Odd Casa": st.column_config.NumberColumn("Odd Casa", format="%.2f", alignment="center"),
                        "Odd Fora": st.column_config.NumberColumn("Odd Fora", format="%.2f", alignment="center"),
                        "Gols FT Feitos": st.column_config.NumberColumn("Gols FT Feitos", format="%d", alignment="center"),
                        "Gols FT Sofridos": st.column_config.NumberColumn("Gols FT Sofridos", format="%d", alignment="center"),
                        "Gols HT Feitos": st.column_config.NumberColumn("Gols HT Feitos", format="%d", alignment="center"),
                        "Gols HT Sofridos": st.column_config.NumberColumn("Gols HT Sofridos", format="%d", alignment="center"),
                        "Cantos FT Feitos": st.column_config.NumberColumn("Cantos FT Feitos", format="%d", alignment="center"),
                        "Cantos FT Sofridos": st.column_config.NumberColumn("Cantos FT Sofridos", format="%d", alignment="center"),
                        "Cantos HT Feitos": st.column_config.NumberColumn("Cantos HT Feitos", format="%d", alignment="center"),
                        "Cantos HT Sofridos": st.column_config.NumberColumn("Cantos HT Sofridos", format="%d", alignment="center"),
                    }

                    # QUADRO MANDANTE
                    st.markdown(f"**Jogos do {m_orig} jogando na condição de mandante**")
                    df_m_casa = df_hist[df_hist['Mandante'] == m_orig].sort_values('Data_DT', ascending=False).head(10).copy()
                    if not df_m_casa.empty:
                        df_m_casa['Jogos'] = [f"Jogo {i+1}" for i in range(len(df_m_casa))]
                        q_m = df_m_casa[['Jogos', 'Data', 'Odd_Mandante_FT', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Gols_Mandante_HT', 'Gols_Visitante_HT', 'Corners_H', 'Corners_A', 'Corners_H_HT', 'Corners_A_HT']].rename(columns={
                            'Odd_Mandante_FT': 'Odd Casa', 'Gols_Mandante_FT': 'Gols FT Feitos', 'Gols_Visitante_FT': 'Gols FT Sofridos',
                            'Gols_Mandante_HT': 'Gols HT Feitos', 'Gols_Visitante_HT': 'Gols HT Sofridos',
                            'Corners_H': 'Cantos FT Feitos', 'Corners_A': 'Cantos FT Sofridos', 'Corners_H_HT': 'Cantos HT Feitos', 'Corners_A_HT': 'Cantos HT Sofridos'
                        })
                        st.dataframe(q_m, use_container_width=True, hide_index=True, column_config=config_p)
                    
                    st.markdown("<br>", unsafe_allow_html=True)

                    # QUADRO VISITANTE
                    st.markdown(f"**Jogos do {v_orig} jogando na condição de visitante**")
                    df_v_fora = df_hist[df_hist['Visitante'] == v_orig].sort_values('Data_DT', ascending=False).head(10).copy()
                    if not df_v_fora.empty:
                        df_v_fora['Jogos'] = [f"Jogo {i+1}" for i in range(len(df_v_fora))]
                        q_v = df_v_fora[['Jogos', 'Data', 'Odd_Visitante_FT', 'Gols_Visitante_FT', 'Gols_Mandante_FT', 'Gols_Visitante_HT', 'Gols_Mandante_HT', 'Corners_A', 'Corners_H', 'Corners_A_HT', 'Corners_H_HT']].rename(columns={
                            'Odd_Visitante_FT': 'Odd Fora', 'Gols_Visitante_FT': 'Gols FT Feitos', 'Gols_Mandante_FT': 'Gols FT Sofridos',
                            'Gols_Visitante_HT': 'Gols HT Feitos', 'Gols_Mandante_HT': 'Gols HT Sofridos',
                            'Corners_A': 'Cantos FT Feitos', 'Corners_H': 'Cantos FT Sofridos', 'Corners_A_HT': 'Cantos HT Feitos', 'Corners_H_HT': 'Cantos HT Sofridos'
                        })
                        st.dataframe(q_v, use_container_width=True, hide_index=True, column_config=config_p)

            if st.session_state.id_simular == idx:
                with st.container(border=True):
                    st.success(f"🎲 **Simulação Poisson:** {m_orig} vs {v_orig}")
                    if m_t in dict_stats and v_t in dict_stats:
                        g_m, g_v = dict_stats[m_t]['Gols_Mandante_FT'], dict_stats[v_t]['Gols_Visitante_FT']
                        st.metric("Expectativa de Gols", f"{g_m:.1f} x {g_v:.1f}")

    # --- 3. SUGESTÕES E PERFORMANCE (MANTIDOS INTEGRALMENTE) ---
    st.divider()
    st.subheader("🎯 Sugestões do Dia (Top Performance)")
    cols_sug = st.columns(5)
    titulos = ["Over 2.5 FT", "Over 9.5 Cnt", "Over 0.5 HT", "Ambas Sim", "Over 4.5 Cnt HT"]
    chaves = ["gFT", "cFT", "gHT", "btts", "cHT"]
    for i, col in enumerate(cols_sug):
        with col:
            st.markdown(f"**{titulos[i]}**")
            lista_top = sorted(sugestoes[chaves[i]], key=lambda x: x['v'], reverse=True)[:3]
            for s in lista_top:
                val = f"{s['v']*100:.1f}%" if chaves[i] == "btts" else f"{s['v']:.2f}"
                st.caption(f"✅ {s['j']} ({val})")

    if times_do_dia:
        st.divider()
        st.subheader(f"📊 Performance dos Times ({st.session_state.data_ex_jogos})")
        df_perf = pd.DataFrame([dict_stats[t] for t in set(times_do_dia) if t in dict_stats])
        df_perf["Time"] = [t for t in set(times_do_dia) if t in dict_stats]
        r1, r2, r3, r4 = st.columns(4)
        with r1:
            st.write("⚽ Marcam + (FT)")
            st.dataframe(df_perf.sort_values("Gols_Mandante_FT", ascending=False)[["Time", "Gols_Mandante_FT"]].head(5), hide_index=True)
        with r2:
            st.write("⏱️ Marcam + HT")
            st.dataframe(df_perf.sort_values("Gols_Mandante_HT", ascending=False)[["Time", "Gols_Mandante_HT"]].head(5), hide_index=True)
        with r3:
            st.write("🚩 Cantos + (FT)")
            st.dataframe(df_perf.sort_values("Corners_H", ascending=False)[["Time", "Corners_H"]].head(5), hide_index=True)
        with r4:
            st.write("🚩 Cantos + HT")
            st.dataframe(df_perf.sort_values("Corners_H_HT", ascending=False)[["Time", "Corners_H_HT"]].head(5), hide_index=True)
