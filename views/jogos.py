import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import pytz
import unicodedata
from difflib import get_close_matches # Biblioteca para comparação de strings

# Links dos arquivos
URL_AGENDA = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.csv"

def mostrar_jogos(df_hist): 
    st.title("📅 Agenda de Jogos")
    
    brasil_tz = pytz.timezone('America/Sao_Paulo')
    hoje_dt = datetime.now(brasil_tz).date()

    # --- 1. TRATAMENTO PROFISSIONAL DE STRINGS ---
    def tratar_string(texto):
        if not texto or pd.isna(texto): return ""
        # Remove acentos e caracteres especiais de encoding
        texto = str(texto).replace("Ã³", "o").replace("Ã©", "e").replace("Ã¡", "a").replace("Ã", "a")
        nksf = unicodedata.normalize('NFKD', texto)
        texto = "".join([c for c in nksf if not unicodedata.combining(c)])
        # Limpeza final: remove pontos, traços e excesso de espaços
        texto = texto.upper().replace(".", "").replace("-", " ").strip()
        return " ".join(texto.split()) # Remove espaços duplos

    @st.cache_data(ttl=60)
    def carregar_agenda(url):
        try:
            df = pd.read_csv(url, sep=None, engine='python', encoding='utf-8-sig')
            df.columns = [c.strip() for c in df.columns]
            return df
        except: return pd.DataFrame()

    # --- 2. MOTOR DE CLASSIFICAÇÃO COM NORMALIZAÇÃO ---
    def obter_classificacao(df_input):
        if df_input is None or df_input.empty: return {}, []
        
        df_c = df_input.copy()
        # Normaliza as colunas do banco de dados
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

    # --- 3. FUNÇÃO DE MATCHING (O "PULO DO GATO") ---
    def encontrar_time_similar(nome_agenda, lista_referencia):
        nome_agenda = tratar_string(nome_agenda)
        # Tenta achar o nome exato primeiro
        if nome_agenda in lista_referencia:
            return nome_agenda
        # Se não achar, busca o mais parecido (mínimo 60% de similaridade)
        matches = get_close_matches(nome_agenda, lista_referencia, n=1, cutoff=0.6)
        return matches[0] if matches else None

    # --- 4. INTERFACE E EXIBIÇÃO ---
    if 'data_exibicao' not in st.session_state:
        st.session_state.data_exibicao = hoje_dt.strftime('%d/%m/%Y')

    cols_btn = st.columns(3)
    datas_ops = [hoje_dt, hoje_dt + timedelta(days=1), hoje_dt + timedelta(days=2)]
    labels = ["📅 Hoje", "📅 Amanhã", "📅 Depois"]
    
    for i in range(3):
        if cols_btn[i].button(labels[i], key=f"btn_nav_{i}"):
            st.session_state.data_exibicao = datas_ops[i].strftime('%d/%m/%Y')
            st.rerun()

    st.info(f"Jogos de: **{st.session_state.data_exibicao}**")

    # Filtro da agenda (compatível com dd/mm/yyyy ou dd/mm/yy)
    df_dia = df_agenda[df_agenda['Data'].str.contains(st.session_state.data_exibicao[0:5], na=False)]

    if df_dia.empty:
        st.warning("Agenda vazia para hoje.")
    else:
        for liga_orig in df_dia['Liga'].unique():
            st.markdown(f"#### 🏆 {liga_orig}")
            df_l = df_dia[df_dia['Liga'] == liga_orig]
            liga_tratada = tratar_string(liga_orig)

            for idx, row in df_l.iterrows():
                m_agenda, v_agenda = str(row['Mandante']), str(row['Visitante'])
                
                # Faz o matching inteligente entre Agenda e Banco
                m_match = encontrar_time_similar(m_agenda, lista_times_banco)
                v_match = encontrar_time_similar(v_agenda, lista_times_banco)

                # Busca a posição usando o nome que "casou"
                pos_m = dict_posicoes.get(f"{liga_tratada}_{m_match}", "?")
                if pos_m == "?" and m_match: # Busca em qualquer liga se falhar na específica
                    for k, p in dict_posicoes.items():
                        if k.endswith(f"_{m_match}"): pos_m = p; break

                pos_v = dict_posicoes.get(f"{liga_tratada}_{v_match}", "?")
                if pos_v == "?" and v_match:
                    for k, p in dict_posicoes.items():
                        if k.endswith(f"_{v_match}"): pos_v = p; break

                c1, c2, c3 = st.columns([4, 3, 1.5])
                with c1:
                    st.write(f"**{row['Hora']}** | ({pos_m}º) {m_agenda} vs {v_agenda} ({pos_v}º)")
                with c2:
                    st.write(f"Odds: {row.get('Odd Mandante','-')} | {row.get('Odd Visitante','-')}")
                with c3:
                    if st.button("Analisar 🔍", key=f"bt_{idx}"):
                        st.session_state.time_casa_scout = m_agenda
                        st.session_state.time_fora_scout = v_agenda
                        st.session_state.menu_ativo = "🔎 Scout"
                        st.rerun()
