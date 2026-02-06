import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import unicodedata
import re

# Links dos arquivos
URL_AGENDA = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.csv"

def mostrar_jogos(df_hist): 
    st.title("📅 Agenda de Jogos")
    
    brasil_tz = pytz.timezone('America/Sao_Paulo')
    hoje_dt = datetime.now(brasil_tz).date()

    # --- DICIONÁRIO DE CORREÇÃO MANUAL (Adicione aqui as variações que encontrar) ---
    MAPEAMENTO_TIMES = {
        "UNIV. CONCEPCION": "UNIVERSIDAD CONCEPCION",
        "CONCEPCIÃ³N": "CONCEPCION",
        "SAO PAULO": "SAO PAULO",
        "SAO PAULO FC": "SAO PAULO",
        "ST.": "SAINT",
        "UTD": "UNITED"
    }

    def normalizar_nome(texto):
        if pd.isna(texto): return ""
        texto = str(texto).upper()
        # Corrige erros de encoding comuns
        texto = texto.replace("Ã³", "O").replace("Ã©", "E").replace("Ã¡", "A").replace("Ã", "A")
        # Remove acentos
        texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
        # Limpeza de pontuação
        texto = re.sub(r'[^A-Z0-9 ]', '', texto)
        texto = texto.strip()
        
        # Aplica o mapeamento manual
        for de, para in MAPEAMENTO_TIMES.items():
            if de in texto:
                texto = texto.replace(de, para)
        
        return texto

    @st.cache_data(ttl=60)
    def carregar_agenda(url):
        try:
            df = pd.read_csv(url, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = [str(c).strip() for c in df.columns]
            df = df.loc[:, ~df.columns.duplicated()]
            return df
        except: return pd.DataFrame()

    def obter_classificacao(df_input):
        if df_input is None or df_input.empty: return {}
        
        df_c = df_input.copy()
        df_c.columns = [str(c).strip() for c in df_c.columns]
        
        # Identificar colunas vitais
        col_liga = next((c for c in df_c.columns if 'LIGA' in c.upper()), 'Liga')
        
        stats = {}
        for _, row in df_c.iterrows():
            liga = normalizar_nome(row[col_liga])
            m = normalizar_nome(row['Mandante'])
            v = normalizar_nome(row['Visitante'])
            
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
        
        posicoes = {}
        for liga in stats:
            ranking = sorted(stats[liga].items(), key=lambda x: (x[1]['pts'], x[1]['sg']), reverse=True)
            for i, (time, _) in enumerate(ranking):
                posicoes[f"{liga}_{time}"] = i + 1
        return posicoes

    df_agenda = carregar_agenda(URL_AGENDA)
    dict_posicoes = obter_classificacao(df_hist)

    # --- UI DE DATAS ---
    if 'data_exibicao' not in st.session_state:
        st.session_state.data_exibicao = hoje_dt.strftime('%d/%m/%Y')

    cols_btn = st.columns(3)
    datas_ops = [hoje_dt, hoje_dt + timedelta(days=1), hoje_dt + timedelta(days=2)]
    labels = ["📅 Hoje", "📅 Amanhã", "📅 Depois"]
    for i in range(3):
        if cols_btn[i].button(labels[i], key=f"btn_nav_{i}", use_container_width=True):
            st.session_state.data_exibicao = datas_ops[i].strftime('%d/%m/%Y')
            st.rerun()

    st.info(f"Jogos de: **{st.session_state.data_exibicao}**")

    # --- FILTRO DA AGENDA ---
    df_dia = df_agenda[df_agenda['Data'].astype(str).str.contains(st.session_state.data_exibicao, na=False)]
    
    if df_dia.empty:
        st.warning(f"Sem jogos mapeados para {st.session_state.data_exibicao}.")
    else:
        for liga in df_dia['Liga'].unique():
            st.markdown(f"#### 🏆 {liga}")
            df_l = df_dia[df_dia['Liga'] == liga]
            liga_norm = normalizar_nome(liga)

            for idx, row in df_l.iterrows():
                m_orig, v_orig = str(row['Mandante']), str(row['Visitante'])
                m_norm, v_norm = normalizar_nome(m_orig), normalizar_nome(v_orig)
                
                # Busca Posição
                pos_m = dict_posicoes.get(f"{liga_norm}_{m_norm}", "?")
                pos_v = dict_posicoes.get(f"{liga_norm}_{v_norm}", "?")

                # --- SEGUNDA CHANCE: Busca apenas pelo nome do time (caso a Liga mude de nome) ---
                if pos_m == "?":
                    # Procura em qualquer liga pelo time normalizado
                    for chave, p in dict_posicoes.items():
                        if chave.endswith(f"_{m_norm}"):
                            pos_m = p
                            break
                if pos_v == "?":
                    for chave, p in dict_posicoes.items():
                        if chave.endswith(f"_{v_norm}"):
                            pos_v = p
                            break

                c1, c2, c3 = st.columns([4, 3, 1.5])
                with c1:
                    st.write(f"**{row['Hora']}** | ({pos_m}º) {m_orig} vs {v_orig} ({pos_v}º)")
                with c2:
                    st.write(f"Odds: {row.get('Odd Mandante','-')} | {row.get('Odd Visitante','-')}")
                with c3:
                    if st.button("Analisar 🔍", key=f"btn_sc_{idx}"):
                        st.session_state.time_casa_scout = m_orig
                        st.session_state.time_fora_scout = v_orig
                        st.session_state.menu_ativo = "🔎 Scout"
                        st.rerun()
