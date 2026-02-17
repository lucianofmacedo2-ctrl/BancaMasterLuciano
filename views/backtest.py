import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
from datetime import datetime

# --- CONFIGURAÇÕES DE LINKS ---
URL_AGENDA = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/refs/heads/main/Lista_Jogos.csv"
URL_MAPEAMENTO = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/mapeamento_times.xlsx%20-%20Tudo.csv"
ARQUIVO_HISTORICO = 'dados_25_26.csv'

def tratar_string_backtest(texto):
    if not texto or pd.isna(texto): return ""
    texto = str(texto)
    mapa_caracteres = {
        "Ã³": "O", "Ã©": "E", "Ã¡": "A", "Ã£": "A", "Ãª": "E", "Ã­": "I",
        "Ã§": "C", "Ã": "A", "Ã²": "O", "Ã¹": "U"
    }
    for erro, correto in mapa_caracteres.items():
        texto = texto.replace(erro, correto)
    
    nksf = unicodedata.normalize('NFKD', texto)
    texto = "".join([c for c in nksf if not unicodedata.combining(c)])
    return texto.upper().strip()

@st.cache_data(ttl=600)
def carregar_dados_auditoria():
    try:
        df_map = pd.read_csv(URL_MAPEAMENTO)
        mapa_times = dict(zip(df_map['Time Soccerway'].apply(tratar_string_backtest), 
                              df_map['Time Base '].apply(tratar_string_backtest)))
    except:
        mapa_times = {}

    try:
        df_h = pd.read_csv(ARQUIVO_HISTORICO, sep=None, engine='python', encoding='utf-8-sig')
        df_h.columns = [c.strip() for c in df_h.columns]
        df_h['dt_comparacao'] = pd.to_datetime(df_h['Data'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')
        df_h['M_NORM'] = df_h['Mandante'].apply(tratar_string_backtest)
        df_h['V_NORM'] = df_h['Visitante'].apply(tratar_string_backtest)
        
        cols_num = ['Total_Gols_FT', 'Total_Gols_HT', 'Total_Corners', 'Total_Corners_HT', 'Gols_Mandante_FT', 'Gols_Visitante_FT']
        for col in cols_num:
            if col in df_h.columns:
                df_h[col] = pd.to_numeric(df_h[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        df_h['BTTS_REAL'] = ((df_h['Gols_Mandante_FT'] > 0) & (df_h['Gols_Visitante_FT'] > 0)).astype(int)
    except:
        df_h = pd.DataFrame()

    try:
        df_a = pd.read_csv(URL_AGENDA, sep=None, engine='python', encoding='utf-8-sig')
        df_a.columns = [c.strip() for c in df_a.columns]
        df_a['dt_comparacao'] = pd.to_datetime(df_a['Data'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')
        
        def aplicar_mapa(nome):
            norm = tratar_string_backtest(nome)
            return mapa_times.get(norm, norm)

        df_a['M_TRADUZ'] = df_a['Mandante'].apply(aplicar_mapa)
        df_a['V_TRADUZ'] = df_a['Visitante'].apply(aplicar_mapa)
    except:
        df_a = pd.DataFrame()

    return df_h, df_a

def calcular_winrate(df, coluna):
    if df.empty: return 0
    return (len(df[df[coluna] == "✅"]) / len(df)) * 100

def mostrar_backtest():
    st.markdown("<style>[data-testid='stMetricValue'] { color: #31333F !important; }</style>", unsafe_allow_html=True)
    st.title("🧪 Auditoria Separada por Estratégia")
    
    df_h, df_a = carregar_dados_auditoria()
    if df_h.empty or df_a.empty:
        st.warning("Bases de dados não encontradas.")
        return

    resultados_lista = []
    for _, row in df_a.iterrows():
        m_trad, v_trad, data_j = row['M_TRADUZ'], row['V_TRADUZ'], row['dt_comparacao']
        match = df_h[(df_h['M_NORM'] == m_trad) & (df_h['V_NORM'] == v_trad) & (df_h['dt_comparacao'] == data_j)]
        
        if not match.empty:
            real = match.iloc[0]
            h_m = df_h[((df_h['M_NORM'] == m_trad) | (df_h['V_NORM'] == m_trad)) & (df_h['dt_comparacao'] != data_j)]
            h_v = df_h[((df_h['M_NORM'] == v_trad) | (df_h['V_NORM'] == v_trad)) & (df_h['dt_comparacao'] != data_j)]
            
            if not h_m.empty and not h_v.empty:
                med_gols = (h_m['Total_Gols_FT'].mean() + h_v['Total_Gols_FT'].mean()) / 2
                med_ht = (h_m['Total_Gols_HT'].mean() + h_v['Total_Gols_HT'].mean()) / 2
                med_cantos = (h_m['Total_Corners'].mean() + h_v['Total_Corners'].mean()) / 2
                med_btts = (h_m['BTTS_REAL'].mean() + h_v['BTTS_REAL'].mean()) / 2
                
                sinais = []
                if med_gols > 2.5: sinais.append("🔥⚽")
                if med_cantos > 9.5: sinais.append("🔥🚩")
                if med_btts > 0.60: sinais.append("🤝")
                if med_ht >= 1.0: sinais.append("⏱️")

                if sinais:
                    resultados_lista.append({
                        "Data": data_j,
                        "Jogo": f"{row['Mandante']} x {row['Visitante']}",
                        "Sinais_Ativos": sinais,
                        "0.5 HT": "✅" if real['Total_Gols_HT'] >= 1 else "❌",
                        "2.5 FT": "✅" if real['Total_Gols_FT'] > 2.5 else "❌",
                        "Ambas Sim": "✅" if real['BTTS_REAL'] == 1 else "❌",
                        "9.5 Cnt": "✅" if real['Total_Corners'] > 9.5 else "❌"
                    })

    if not resultados_lista:
        st.info("Nenhum sinal auditável encontrado.")
        return

    df_geral = pd.DataFrame(resultados_lista)

    def color_result(val):
        if val == "✅": return 'background-color: #d4edda; color: #155724'
        if val == "❌": return 'background-color: #f8d7da; color: #721c24'
        return ''

    # --- SEÇÃO POR ESTRATÉGIA ---
    config_sinais = [
        {"emoji": "⏱️", "label": "Estratégia Gols HT (0.5 HT)", "col_res": "0.5 HT"},
        {"emoji": "🔥⚽", "label": "Estratégia Gols FT (2.5 FT)", "col_res": "2.5 FT"},
        {"emoji": "🤝", "label": "Estratégia Ambas Marcam (BTTS)", "col_res": "Ambas Sim"},
        {"emoji": "🔥🚩", "label": "Estratégia Cantos (9.5 Cnt)", "col_res": "9.5 Cnt"}
    ]

    for config in config_sinais:
        # Filtra apenas jogos que receberam esse emoji específico
        df_sinal = df_geral[df_geral['Sinais_Ativos'].apply(lambda x: config['emoji'] in x)].copy()
        
        st.divider()
        st.subheader(f"{config['emoji']} {config['label']}")
        
        if not df_sinal.empty:
            wr = calcular_winrate(df_sinal, config['col_res'])
            odd_j = f"{100/wr:.2f}" if wr > 0 else "0.00"
            
            c1, c2, c3 = st.columns([1, 1, 2])
            c1.metric("Winrate", f"{wr:.1f}%")
            c2.metric("Odd Justa", f"{odd_j}")
            c3.write(f"Total de jogos analisados para este sinal: **{len(df_sinal)}**")
            
            # Mostra a tabela apenas deste sinal
            st.dataframe(df_sinal.drop(columns=['Sinais_Ativos']).style.applymap(color_result, subset=[config['col_res']]), 
                         use_container_width=True, hide_index=True)
        else:
            st.write("Nenhum jogo encontrado com este sinal no período.")

# Execução
if __name__ == "__main__":
    mostrar_backtest()
