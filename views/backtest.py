import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
from datetime import datetime

# --- CONFIGURAÇÕES DE LINKS ---
URL_AGENDA = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/refs/heads/main/Lista_Jogos.csv"
# Link do mapeamento em formato RAW para o pandas conseguir ler
URL_MAPEAMENTO = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/mapeamento_times.xlsx%20-%20Tudo.csv"
ARQUIVO_HISTORICO = 'dados_25_26.csv'

def normalizar_texto(texto):
    """Remove acentos, resolve problemas de encoding (Ã³, etc) e padroniza para maiúsculas."""
    if not texto or pd.isna(texto): return ""
    texto = str(texto)
    # Correção de caracteres comuns de erro de encoding
    mapa_erros = {
        "Ã³": "O", "Ã©": "E", "Ã¡": "A", "Ã£": "A", "Ãª": "E", "Ã­": "I",
        "Ã§": "C", "Ã": "A", "Ã²": "O", "Ã¹": "U"
    }
    for erro, correto in mapa_erros.items():
        texto = texto.replace(erro, correto)
    
    # Remove acentos residuais
    nksf = unicodedata.normalize('NFKD', texto)
    texto = "".join([c for c in nksf if not unicodedata.combining(c)])
    return texto.upper().strip()

@st.cache_data(ttl=600)
def carregar_bases():
    # 1. Carregar Mapeamento
    try:
        df_map = pd.read_csv(URL_MAPEAMENTO)
        # Criamos um dicionário: O que vem do Soccerway (Agenda) -> Nome Base (Histórico)
        # Usamos strip() para evitar espaços invisíveis nas colunas
        mapa_times = dict(zip(df_map['Time Soccerway'].apply(normalizar_texto), 
                              df_map['Time Base '].apply(normalizar_texto))) # Note o espaço em 'Time Base '
    except Exception as e:
        st.error(f"Erro ao carregar Mapeamento: {e}")
        mapa_times = {}

    # 2. Carregar Histórico
    try:
        df_h = pd.read_csv(ARQUIVO_HISTORICO, sep=None, engine='python', encoding='utf-8-sig')
        df_h.columns = [c.strip() for c in df_h.columns]
        df_h['dt_comparacao'] = pd.to_datetime(df_h['Data'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')
        
        # Criamos colunas normalizadas no histórico para busca rápida
        df_h['M_NORM'] = df_h['Mandante'].apply(normalizar_texto)
        df_h['V_NORM'] = df_h['Visitante'].apply(normalizar_texto)
        
        # Tratamento numérico
        cols_num = ['Total_Gols_FT', 'Total_Gols_HT', 'Total_Corners', 'Total_Corners_HT', 'Gols_Mandante_FT', 'Gols_Visitante_FT']
        for col in cols_num:
            if col in df_h.columns:
                df_h[col] = pd.to_numeric(df_h[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        # Coluna BTTS real
        df_h['BTTS_REAL'] = ((df_h['Gols_Mandante_FT'] > 0) & (df_h['Gols_Visitante_FT'] > 0)).astype(int)
    except Exception as e:
        st.error(f"Erro ao carregar Histórico: {e}")
        df_h = pd.DataFrame()

    # 3. Carregar Agenda
    try:
        df_a = pd.read_csv(URL_AGENDA, sep=None, engine='python', encoding='utf-8-sig')
        df_a.columns = [c.strip() for c in df_a.columns]
        df_a['dt_comparacao'] = pd.to_datetime(df_a['Data'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')
        
        # Traduz os nomes da agenda para os nomes do histórico usando o mapeamento
        def traduzir_time(nome):
            norm = normalizar_texto(nome)
            return mapa_times.get(norm, norm)

        df_a['M_TRADUZIDO'] = df_a['Mandante'].apply(traduzir_time)
        df_a['V_TRADUZIDO'] = df_a['Visitante'].apply(traduzir_time)
    except Exception as e:
        st.error(f"Erro ao carregar Agenda: {e}")
        df_a = pd.DataFrame()

    return df_h, df_a

def calcular_winrate(df, coluna):
    if df.empty: return 0
    return (len(df[df[coluna] == "✅"]) / len(df)) * 100

def mostrar_backtest():
    st.title("🧪 Backtest & Auditoria de Sinais")
    st.info("Esta página cruza a Agenda (Sinais) com o Histórico (Resultados) usando seu arquivo de mapeamento.")

    df_h, df_a = carregar_bases()

    if df_h.empty or df_a.empty:
        st.warning("Dados não disponíveis para processamento.")
        return

    registros = []

    # Percorre a agenda para validar os sinais que já aconteceram
    for _, row in df_a.iterrows():
        m_trad, v_trad, data_j = row['M_TRADUZIDO'], row['V_TRADUZIDO'], row['dt_comparacao']
        
        # Busca o resultado real no histórico
        res_real = df_h[(df_h['M_NORM'] == m_trad) & 
                        (df_h['V_NORM'] == v_trad) & 
                        (df_h['dt_comparacao'] == data_j)]
        
        if not res_real.empty:
            real = res_real.iloc[0]
            
            # Lógica de Sinais (Baseada nas médias passadas, ignorando o jogo do dia)
            h_m = df_h[((df_h['M_NORM'] == m_trad) | (df_h['V_NORM'] == m_trad)) & (df_h['dt_comparacao'] != data_j)]
            h_v = df_h[((df_h['M_NORM'] == v_trad) | (df_h['V_NORM'] == v_trad)) & (df_h['dt_comparacao'] != data_j)]
            
            if not h_m.empty and not h_v.empty:
                med_gols = (h_m['Total_Gols_FT'].mean() + h_v['Total_Gols_FT'].mean()) / 2
                med_cantos = (h_m['Total_Corners'].mean() + h_v['Total_Corners'].mean()) / 2
                med_btts = (h_m['BTTS_REAL'].mean() + h_v['BTTS_REAL'].mean()) / 2

                # Verifica se o jogo teria algum emoji (Sinal)
                tem_sinal = False
                sinal_txt = ""
                if med_gols > 3.0: sinal_txt += "🔥⚽ "; tem_sinal = True
                if med_cantos > 11.0: sinal_txt += "🔥🚩 "; tem_sinal = True
                if med_btts > 0.65: sinal_txt += "🤝 "; tem_sinal = True

                if tem_sinal:
                    registros.append({
                        "Data": data_j,
                        "Jogo": f"{row['Mandante']} x {row['Visitante']}",
                        "Sinal": sinal_txt,
                        "0.5 HT": "✅" if real['Total_Gols_HT'] >= 1 else "❌",
                        "2.5 FT": "✅" if real['Total_Gols_FT'] > 2.5 else "❌",
                        "Ambas Sim": "✅" if real['BTTS_REAL'] == 1 else "❌",
                        "4.5 Cnt HT": "✅" if real['Total_Corners_HT'] > 4.5 else "❌",
                        "9.5 Cnt FT": "✅" if real['Total_Corners'] > 9.5 else "❌"
                    })

    if registros:
        df_res = pd.DataFrame(registros)
        
        # Métricas
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Winrate 0.5 HT", f"{calcular_winrate(df_res, '0.5 HT'):.1f}%")
        c2.metric("Winrate 2.5 FT", f"{calcular_winrate(df_res, '2.5 FT'):.1f}%")
        c3.metric("Winrate Ambas", f"{calcular_winrate(df_res, 'Ambas Sim'):.1f}%")
        c4.metric("Winrate 9.5 Cnt", f"{calcular_winrate(df_res, '9.5 Cnt FT'):.1f}%")

        # Tabela Estilizada
        def aplicar_estilo(val):
            if val == "✅": return 'background-color: #d4edda; color: #155724'
            if val == "❌": return 'background-color: #f8d7da; color: #721c24'
            return ''

        st.dataframe(
            df_res.style.applymap(aplicar_estilo, subset=['0.5 HT', '2.5 FT', 'Ambas Sim', '4.5 Cnt HT', '9.5 Cnt FT']),
            use_container_width=True, hide_index=True
        )
    else:
        st.warning("Nenhum sinal da agenda foi encontrado no histórico até agora. Certifique-se de que os dados de ontem já foram atualizados no arquivo CSV.")
