import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
from scipy.stats import poisson
import plotly.graph_objects as go

# --- FUNÇÕES AUXILIARES PARA O SCOUT DENTRO DA PÁGINA ---

def extrair_metrica_local(df_hist, time, col_h, col_a):
    m = df_hist[df_hist['Mandante'] == time][col_h]
    v = df_hist[df_hist['Visitante'] == time][col_a]
    return pd.to_numeric(pd.concat([m, v]), errors='coerce').fillna(0)

def calc_inc_local(df_h):
    m = {
        'O 0.5 HT': df_h['Total_Gols_HT']>0.5, 
        'O 1.5 FT': df_h['Total_Gols_FT']>1.5, 
        'O 2.5 FT': df_h['Total_Gols_FT']>2.5,
        'BTTS Sim': (df_h['Gols_Mandante_FT']>0)&(df_h['Gols_Visitante_FT']>0),
        'O 8.5 Cantos': df_h['Total_Corners']>8.5, 
        'O 9.5 Cantos': df_h['Total_Corners']>9.5
    }
    return pd.DataFrame([{'Mercado': k, 'Freq': f"{v.mean()*100:.1f}%"} for k, v in m.items()])

# --- FUNÇÃO PRINCIPAL ATUALIZADA ---

def mostrar_jogos(df_hist_input):
    st.title("📅 Agenda & Inteligência de Dados")
    
    # Inicializa estados para controle de expansão sem mudar de página
    if "jogo_analisar" not in st.session_state: st.session_state.jogo_analisar = None
    if "jogo_simular" not in st.session_state: st.session_state.jogo_simular = None

    brasil_tz = pytz.timezone('America/Sao_Paulo')
    hoje_dt = datetime.now(brasil_tz).date()
    if 'data_ex_jogos' not in st.session_state:
        st.session_state.data_ex_jogos = hoje_dt.strftime('%d/%m/%Y')

    df_hist, dict_stats, dict_pos, _ = preparar_base_e_ranking(df_hist_input)

    # Carregamento da Agenda (mesma lógica)
    @st.cache_data(ttl=300)
    def carregar_agenda_fast(url):
        try:
            df = pd.read_csv(url, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = [c.strip() for c in df.columns]
            return df
        except: return pd.DataFrame()

    df_agenda = carregar_agenda_fast(URL_AGENDA)

    # Navegação de Datas
    cols_btn = st.columns(3)
    datas_ops = [hoje_dt, hoje_dt + timedelta(days=1), hoje_dt + timedelta(days=2)]
    labels = ["📅 Hoje", "📅 Amanhã", "📅 Depois"]
    for i in range(3):
        if cols_btn[i].button(labels[i], key=f"btn_nav_{i}", use_container_width=True):
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
            
            # Lógica de Ícones (Preservada conforme Pergunta 1.txt) [cite: 8, 9]
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

            # Layout da Linha do Jogo
            c1, c2, c3, c4 = st.columns([4.2, 2.8, 1.5, 1.5])
            with c1: st.write(f"**{row['Hora']}** | ({p_m}º) {m_orig} vs {v_orig} ({p_v}º){icones}")
            with c2: st.caption(f"Odds: {row.get('Odd Mandante','-')} | {row.get('Odd Empate','-')} | {row.get('Odd Visitante','-')}")
            
            with c3:
                if st.button("Analisar 🔍", key=f"ana_{idx}", use_container_width=True):
                    st.session_state.jogo_analisar = idx if st.session_state.jogo_analisar != idx else None
                    st.session_state.jogo_simular = None
            with c4:
                if st.button("Simular 🎲", key=f"sim_{idx}", use_container_width=True):
                    st.session_state.jogo_simular = idx if st.session_state.jogo_simular != idx else None
                    st.session_state.jogo_analisar = None

            # --- CONTEÚDO EXPANSÍVEL (DENTRO DA MESMA PÁGINA) ---
            if st.session_state.jogo_analisar == idx:
                with st.container(border=True):
                    st.info(f"📊 **Scout Rápido:** {m_orig} vs {v_orig}")
                    df_m_last = df_hist[(df_hist['Mandante']==m_orig)|(df_hist['Visitante']==m_orig)].head(10)
                    df_v_last = df_hist[(df_hist['Mandante']==v_orig)|(df_hist['Visitante']==v_orig)].head(10)
                    
                    ca, cb = st.columns(2)
                    ca.write(f"**Freq. {m_orig}**")
                    ca.table(calc_inc_local(df_m_last))
                    cb.write(f"**Freq. {v_orig}**")
                    cb.table(calc_inc_local(df_v_last))
                    if st.button("Fechar", key=f"close_ana_{idx}"):
                        st.session_state.jogo_analisar = None
                        st.rerun()

            if st.session_state.jogo_simular == idx:
                with st.container(border=True):
                    st.success(f"🎲 **Projeção Poisson:** {m_orig} x {v_orig}")
                    # Cálculo simplificado de Poisson para exibição rápida
                    exp_g_m = dict_stats[m_t]['Gols_Mandante_FT'] if m_t in dict_stats else 1.0
                    exp_g_v = dict_stats[v_t]['Gols_Visitante_FT'] if v_t in dict_stats else 1.0
                    st.write(f"Placar Estimado: **{exp_g_m:.1f} x {exp_g_v:.1f}**")
                    prob_btts = (1 - poisson.pmf(0, exp_g_m)) * (1 - poisson.pmf(0, exp_g_v)) * 100
                    st.metric("Probabilidade BTTS", f"{prob_btts:.1f}%")
                    if st.button("Fechar", key=f"close_sim_{idx}"):
                        st.session_state.jogo_simular = None
                        st.rerun()

    # --- SUGESTÕES DO DIA (PRESERVADAS NO FINAL) ---
    st.divider()
    st.subheader("🎯 Sugestões do Dia (Top Performance)")
    cols = st.columns(5)
    titulos = ["Over 2.5 FT", "Over 9.5 Cnt", "Over 0.5 HT", "Ambas Sim", "Over 4.5 Cnt HT"]
    chaves = ["gFT", "cFT", "gHT", "btts", "cHT"]
    
    for i, col in enumerate(cols):
        with col:
            st.markdown(f"**{titulos[i]}**")
            lista_top = sorted(sugestoes[chaves[i]], key=lambda x: x['v'], reverse=True)[:3] [cite: 11]
            for s in lista_top:
                val = f"{s['v']*100:.1f}%" if chaves[i] == "btts" else f"{s['v']:.2f}"
                st.caption(f"✅ {s['j']} ({val})") [cite: 11]

    # --- PERFORMANCE DOS TIMES (PRESERVADA) ---
    if times_do_dia:
        st.divider()
        st.subheader(f"📊 Performance dos Times ({st.session_state.data_ex_jogos})")
        df_rank_perf = pd.DataFrame([dict_stats[t] for t in set(times_do_dia) if t in dict_stats])
        df_rank_perf["Time"] = [t for t in set(times_do_dia) if t in dict_stats]
        
        r1, r2, r3, r4 = st.columns(4)
        with r1:
            st.write("⚽ Marcam + (FT)")
            st.dataframe(df_rank_perf.sort_values("Gols_Mandante_FT", ascending=False)[["Time", "Gols_Mandante_FT"]].head(5), hide_index=True)
        with r2:
            st.write("⏱️ Marcam + HT")
            st.dataframe(df_rank_perf.sort_values("Gols_Mandante_HT", ascending=False)[["Time", "Gols_Mandante_HT"]].head(5), hide_index=True)
        # ... (repetir para cantos conforme Pergunta 1.txt)
