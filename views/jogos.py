import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import unicodedata

# Links dos arquivos
URL_AGENDA = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.csv"

def tratar_string_fast(texto):
    if not texto or pd.isna(texto): return ""
    texto = str(texto).upper().replace("Ã³", "O").replace("Ã©", "E").replace("Ã¡", "A").replace("Ã", "A")
    nksf = unicodedata.normalize('NFKD', texto)
    texto = "".join([c for c in nksf if not unicodedata.combining(c)])
    return " ".join(texto.replace(".", "").replace("-", " ").split()).strip()

@st.cache_data(ttl=3600)
def preparar_base_historica(df_hist):
    if df_hist.empty: return df_hist, {}, {}
    
    df = df_hist.copy()
    # Tratamento de colunas numéricas em bloco
    cols_num = ['Corners_H', 'Corners_A', 'Total_Corners', 'Total_Gols_FT', 'Total_Gols_HT', 'Total_Corners_HT', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Gols_Mandante_HT', 'Gols_Visitante_HT', 'Corners_H_HT', 'Corners_A_HT']
    for col in cols_num:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    
    df['BTTS_Realizado'] = ((df['Gols_Mandante_FT'] > 0) & (df['Gols_Visitante_FT'] > 0)).astype(int)
    df['M_T'] = df['Mandante'].apply(tratar_string_fast)
    df['V_T'] = df['Visitante'].apply(tratar_string_fast)
    df['L_T'] = df['Liga'].apply(tratar_string_fast)

    # Pré-calculando Médias de todos os times de uma vez
    stats_times = {}
    todos_times = pd.concat([df['M_T'], df['V_T']]).unique()
    
    # Criando tabelas auxiliares para média rápida
    m_stats = df.groupby('M_T').agg({'Total_Gols_FT':'mean', 'Total_Gols_HT':'mean', 'BTTS_Realizado':'mean', 'Total_Corners':'mean', 'Total_Corners_HT':'mean', 'Gols_Mandante_FT':'mean', 'Gols_Visitante_FT':'mean', 'Gols_Mandante_HT':'mean', 'Gols_Visitante_HT':'mean', 'Corners_H':'mean', 'Corners_A':'mean', 'Corners_H_HT':'mean', 'Corners_A_HT':'mean'})
    v_stats = df.groupby('V_T').agg({'Total_Gols_FT':'mean', 'Total_Gols_HT':'mean', 'BTTS_Realizado':'mean', 'Total_Corners':'mean', 'Total_Corners_HT':'mean', 'Gols_Mandante_FT':'mean', 'Gols_Visitante_FT':'mean', 'Gols_Mandante_HT':'mean', 'Gols_Visitante_HT':'mean', 'Corners_H':'mean', 'Corners_A':'mean', 'Corners_H_HT':'mean', 'Corners_A_HT':'mean'})

    for t in todos_times:
        # Média ponderada entre jogos em casa e fora
        s_m = m_stats.loc[t] if t in m_stats.index else None
        s_v = v_stats.loc[t] if t in v_stats.index else None
        
        if s_m is not None and s_v is not None:
            stats_times[t] = (s_m + s_v) / 2
        elif s_m is not None:
            stats_times[t] = s_m
        else:
            stats_times[t] = s_v

    return df, stats_times, set(todos_times)

def mostrar_jogos(df_hist_input):
    st.title("📅 Agenda & Inteligência de Dados")
    
    # 1. Preparação Otimizada
    df_hist, dict_stats, lista_times_banco = preparar_base_historica(df_hist_input)
    
    brasil_tz = pytz.timezone('America/Sao_Paulo')
    hoje_dt = datetime.now(brasil_tz).date()

    with st.expander("💡 Legenda do Radar de Valor"):
        st.markdown("🔥⚽ > 2.5 FT | 🔥🚩 > 9.5 Cnt | 🤝 BTTS > 60% | ⏱️ Gols HT >= 1.0")

    @st.cache_data(ttl=300)
    def carregar_agenda_fast(url):
        try:
            df = pd.read_csv(url, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = [c.strip() for c in df.columns]
            return df
        except: return pd.DataFrame()

    df_agenda = carregar_agenda_fast(URL_AGENDA)

    # Controle de Datas
    if 'data_exibicao' not in st.session_state: st.session_state.data_ex_jogos = hoje_dt.strftime('%d/%m/%Y')
    
    cols_btn = st.columns(3)
    datas_ops = [hoje_dt, hoje_dt + timedelta(days=1), hoje_dt + timedelta(days=2)]
    for i, label in enumerate(["📅 Hoje", "📅 Amanhã", "📅 Depois"]):
        if cols_btn[i].button(label, key=f"btn_d_{i}", use_container_width=True):
            st.session_state.data_ex_jogos = datas_ops[i].strftime('%d/%m/%Y')
            st.rerun()

    data_alvo = st.session_state.data_ex_jogos[0:5]
    df_dia = df_agenda[df_agenda['Data'].str.contains(data_alvo, na=False)] if not df_agenda.empty else pd.DataFrame()

    if df_dia.empty:
        st.warning(f"Sem jogos para {st.session_state.data_ex_jogos}.")
        return

    # Listas para Sugestões
    sugestoes = {"gFT":[], "cFT":[], "gHT":[], "btts":[], "cHT":[]}
    times_do_dia = []

    # Exibição dos Jogos
    for liga, df_l in df_dia.groupby('Liga'):
        st.markdown(f"#### 🏆 {liga}")
        
        for idx, row in df_l.iterrows():
            m_orig, v_orig = str(row['Mandante']), str(row['Visitante'])
            m_t, v_t = tratar_string_fast(m_orig), tratar_string_fast(v_orig)
            
            icones = ""
            # Odds Logic
            try:
                om, ov = float(str(row.get('Odd Mandante', 0)).replace(',','.')), float(str(row.get('Odd Visitante', 0)).replace(',','.'))
                if om < 1.4 or ov < 1.4: icones += " 🌟"
                elif om <= 1.8 or ov <= 1.8: icones += " ⭐"
                if abs(om - ov) <= 1.0: icones += " ⚖️"
            except: pass

            # Stats Logic (Instantânea via Dicionário)
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
                    sugestoes["gFT"].append({"jogo": f"{m_orig} vs {v_orig}", "v": m_gFT})
                if m_gHT >= 1.0: 
                    icones += " ⏱️"
                    sugestoes["gHT"].append({"jogo": f"{m_orig} vs {v_orig}", "v": m_gHT})
                if m_btts > 0.65: 
                    icones += " 🤝"
                    sugestoes["btts"].append({"jogo": f"{m_orig} vs {v_orig}", "v": m_btts})
                if m_cFT > 11.0: 
                    icones += " 🔥🚩"
                    sugestoes["cFT"].append({"jogo": f"{m_orig} vs {v_orig}", "v": m_cFT})
                if m_cHT > 4.5:
                    sugestoes["cHT"].append({"jogo": f"{m_orig} vs {v_orig}", "v": m_cHT})

            c1, c2, c3 = st.columns([5, 3, 2])
            c1.write(f"**{row['Hora']}** | {m_orig} vs {v_orig} {icones}")
            c2.caption(f"Odds: {row.get('Odd Mandante','-')} | {row.get('Odd Empate','-')} | {row.get('Odd Visitante','-')}")
            with c3:
                if st.button("Analisar", key=f"btn_an_{idx}"):
                    st.session_state.liga_scout = liga
                    st.session_state.time_casa_scout, st.session_state.time_fora_scout = m_orig, v_orig
                    st.session_state.menu_ativo = "🔎 Scout"
                    st.rerun()

    # Seção de Sugestões Otimizada
    st.divider()
    st.subheader("🎯 Sugestões do Dia")
    cols = st.columns(5)
    titles = ["Over 2.5 FT", "Over 9.5 Cnt", "Over 0.5 HT", "Ambas Sim", "Over 4.5 Cnt HT"]
    keys = ["gFT", "cFT", "gHT", "btts", "cHT"]
    
    for i, col in enumerate(cols):
        with col:
            st.markdown(f"**{titles[i]}**")
            top = sorted(sugestoes[keys[i]], key=lambda x: x['v'], reverse=True)[:3]
            for s in top:
                val_fmt = f"{s['v']*100:.0f}%" if keys[i] == "btts" else f"{s['v']:.2f}"
                st.caption(f"✅ {s['jogo']} ({val_fmt})")

    # Top Performance Times do Dia (Processamento Vetorizado Final)
    if times_do_dia:
        st.divider()
        st.subheader("📊 Performance dos Times de Hoje")
        df_rank = pd.DataFrame([dict_stats[t] for t in set(times_do_dia) if t in dict_stats])
        df_rank["Time"] = [t for t in set(times_do_dia) if t in dict_stats]
        
        r1, r2, r3, r4 = st.columns(4)
        with r1:
            st.write("⚽ Marcam + (FT)")
            st.dataframe(df_rank.sort_values("Gols_Mandante_FT", ascending=False)[["Time", "Gols_Mandante_FT"]].head(5), hide_index=True)
        with r2:
            st.write("⏱️ Marcam + HT")
            st.dataframe(df_rank.sort_values("Gols_Mandante_HT", ascending=False)[["Time", "Gols_Mandante_HT"]].head(5), hide_index=True)
        with r3:
            st.write("🚩 Cantos + (FT)")
            st.dataframe(df_rank.sort_values("Corners_H", ascending=False)[["Time", "Corners_H"]].head(5), hide_index=True)
        with r4:
            st.write("🚩 Cantos + HT")
            st.dataframe(df_rank.sort_values("Corners_H_HT", ascending=False)[["Time", "Corners_H_HT"]].head(5), hide_index=True)

if __name__ == "__main__":
    # Para teste, assumindo que df_hist vem de fora como no seu app principal
    pass
