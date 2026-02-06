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

    # --- FUNÇÃO DE NORMALIZAÇÃO AGRESSIVA ---
    def normalizar_nome(texto):
        if pd.isna(texto): return ""
        texto = str(texto)
        # Corrige erros comuns de encoding (ex: Ã³ -> o)
        texto = unicodedata.normalize('NFKD', texto).encode('ascii', 'ignore').decode('ascii')
        # Remove abreviações comuns para facilitar o cruzamento
        texto = texto.upper().replace("UNIV.", "UNIVERSIDAD").replace("FC", "").replace("U.", "UNIVERSIDAD")
        # Remove qualquer caractere que não seja letra ou número
        texto = re.sub(r'[^A-Z0-9 ]', '', texto)
        return texto.strip()

    @st.cache_data(ttl=60)
    def carregar_agenda(url):
        try:
            df = pd.read_csv(url, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = [str(c).strip() for c in df.columns]
            df = df.loc[:, ~df.columns.duplicated()]
            return df
        except: return pd.DataFrame()

    # --- DICIONÁRIO DE POSIÇÕES COM NORMALIZAÇÃO ---
    def obter_classificacao(df_input):
        if df_input is None or df_input.empty: return {}
        
        df_c = df_input.copy()
        df_c.columns = [str(c).strip() for c in df_c.columns]
        
        # Identificar colunas
        col_liga = next((c for c in df_c.columns if 'LIGA' in c.upper()), 'Liga')
        
        stats = {}
        for _, row in df_c.iterrows():
            # Normalizamos os nomes do BANCO DE DADOS
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

    # UI de Datas
    if 'data_exibicao' not in st.session_state:
        st.session_state.data_exibicao = hoje_dt.strftime('%d/%m/%Y')

    cols_btn = st.columns(3)
    datas_ops = [hoje_dt, hoje_dt + timedelta(days=1), hoje_dt + timedelta(days=2)]
    labels = ["📅 Hoje", "📅 Amanhã", "📅 Depois"]
    for i in range(3):
        if cols_btn[i].button(labels[i], use_container_width=True):
            st.session_state.data_exibicao = datas_ops[i].strftime('%d/%m/%Y')
            st.rerun()

    st.info(f"Jogos de: **{st.session_state.data_exibicao}**")

    # Filtro da agenda
    df_dia = df_agenda[df_agenda['Data'].str.contains(st.session_state.data_exibicao, na=False)]
    
    if df_dia.empty:
        st.warning("Sem jogos para esta data.")
    else:
        for liga in df_dia['Liga'].unique():
            st.markdown(f"#### 🏆 {liga}")
            df_l = df_dia[df_dia['Liga'] == liga]
            liga_norm = normalizar_nome(liga)

            for idx, row in df_l.iterrows():
                m_orig, v_orig = str(row['Mandante']), str(row['Visitante'])
                # Normalizamos os nomes da AGENDA para bater com o banco
                m_norm, v_norm = normalizar_nome(m_orig), normalizar_nome(v_orig)
                
                pos_m = dict_posicoes.get(f"{liga_norm}_{m_norm}", "?")
                pos_v = dict_posicoes.get(f"{liga_norm}_{v_norm}", "?")

                c1, c2, c3 = st.columns([4, 3, 1.5])
                with c1:
                    st.write(f"**{row['Hora']}** | ({pos_m}º) {m_orig} vs {v_orig} ({pos_v}º)")
                with c2:
                    st.write(f"Odds: {row.get('Odd Mandante','-')} | {row.get('Odd Visitante','-')}")
                with c3:
                    if st.button("Analisar 🔍", key=f"btn_{idx}"):
                        st.session_state.time_casa_scout = m_orig
                        st.session_state.time_fora_scout = v_orig
                        st.session_state.menu_ativo = "🔎 Scout"
                        st.rerun()
