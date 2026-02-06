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

    # --- FUNÇÃO DE NORMALIZAÇÃO DE NOMES ---
    def normalizar_nome(texto):
        if pd.isna(texto): return ""
        texto = str(texto).upper()
        # Corrige erros de encoding comuns (Ã³, Ã¡, etc)
        texto = texto.replace("Ã³", "O").replace("Ã©", "E").replace("Ã¡", "A").replace("Ã", "A")
        # Remove acentos e caracteres especiais
        texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
        texto = re.sub(r'[^A-Z0-9 ]', '', texto)
        # Padroniza termos comuns
        texto = texto.replace("UNIV ", "UNIVERSIDAD ").replace("UTD", "UNITED").replace("FC", "")
        return texto.strip()

    @st.cache_data(ttl=60)
    def carregar_agenda(url):
        try:
            # Carregamento flexível do CSV
            df = pd.read_csv(url, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = [str(c).strip() for c in df.columns]
            df = df.loc[:, ~df.columns.duplicated()]
            return df
        except: return pd.DataFrame()

    # --- GERAÇÃO DO RANKING ---
    def obter_classificacao(df_input):
        if df_input is None or df_input.empty: return {}
        
        df_c = df_input.copy()
        df_c.columns = [str(c).strip() for c in df_c.columns]
        
        stats = {}
        for _, row in df_c.iterrows():
            # Pegamos o nome da liga e dos times e normalizamos
            liga = normalizar_nome(row.get('Liga', 'Geral'))
            m = normalizar_nome(row.get('Mandante', ''))
            v = normalizar_nome(row.get('Visitante', ''))
            
            try:
                gm, gv = float(row['Gols_Mandante_FT']), float(row['Gols_Visitante_FT'])
            except: continue
            
            if liga not in stats: stats[liga] = {}
            for t in [m, v]:
                if t and t not in stats[liga]: stats[liga][t] = {'pts': 0, 'sg': 0}
            
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

    # --- LÓGICA DE DATAS (CORRIGIDA) ---
    if 'data_exibicao' not in st.session_state:
        st.session_state.data_exibicao = hoje_dt.strftime('%d/%m/%Y')

    cols_btn = st.columns(3)
    datas_ops = [hoje_dt, hoje_dt + timedelta(days=1), hoy_dt := hoje_dt + timedelta(days=2)]
    labels = ["📅 Hoje", "📅 Amanhã", "📅 Depois"]
    
    for i in range(3):
        if cols_btn[i].button(labels[i], key=f"btn_d_{i}", use_container_width=True):
            st.session_state.data_exibicao = datas_ops[i].strftime('%d/%m/%Y')
            st.rerun()

    st.info(f"Jogos de: **{st.session_state.data_exibicao}**")

    # --- FILTRO DE AGENDA (MAIS FLEXÍVEL) ---
    if not df_agenda.empty:
        # Tenta filtrar pela data ignorando se o ano tem 2 ou 4 dígitos
        data_curta = st.session_state.data_exibicao[:6] + st.session_state.data_exibicao[8:] # dd/mm/yy
        df_dia = df_agenda[
            df_agenda['Data'].astype(str).str.contains(st.session_state.data_exibicao, na=False) |
            df_agenda['Data'].astype(str).str.contains(data_curta, na=False)
        ]
    else:
        df_dia = pd.DataFrame()

    if df_dia.empty:
        st.warning("Nenhum jogo encontrado para esta data na Lista_Jogos.csv.")
    else:
        for liga in df_dia['Liga'].unique():
            st.markdown(f"#### 🏆 {liga}")
            df_l = df_dia[df_dia['Liga'] == liga]
            liga_norm = normalizar_nome(liga)

            for idx, row in df_l.iterrows():
                m_orig, v_orig = str(row['Mandante']), str(row['Visitante'])
                m_norm, v_norm = normalizar_nome(m_orig), normalizar_nome(v_orig)
                
                # Busca posição com "Segunda Chance" (se não achar na liga, busca no geral)
                pos_m = dict_posicoes.get(f"{liga_norm}_{m_norm}", "?")
                pos_v = dict_posicoes.get(f"{liga_norm}_{v_norm}", "?")

                if pos_m == "?": # Busca global
                    for k, p in dict_posicoes.items():
                        if k.endswith(f"_{m_norm}"): pos_m = p; break
                if pos_v == "?":
                    for k, p in dict_posicoes.items():
                        if k.endswith(f"_{v_norm}"): pos_v = p; break

                c1, c2, c3 = st.columns([4, 3, 1.5])
                with c1:
                    st.write(f"**{row['Hora']}** | ({pos_m}º) {m_orig} vs {v_orig} ({pos_v}º)")
                with c2:
                    st.write(f"Odds: {row.get('Odd Mandante','-')} | {row.get('Odd Visitante','-')}")
                with c3:
                    if st.button("Analisar 🔍", key=f"btn_go_{idx}"):
                        st.session_state.time_casa_scout = m_orig
                        st.session_state.time_fora_scout = v_orig
                        st.session_state.menu_ativo = "🔎 Scout"
                        st.rerun()
