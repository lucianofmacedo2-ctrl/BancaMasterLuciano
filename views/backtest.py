import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# Links dos arquivos
URL_AGENDA = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.csv"
ARQUIVO_HISTORICO = 'dados_25_26.csv'

def carregar_dados():
    try:
        # Carregando Histórico (Resultados Reais)
        df_h = pd.read_csv(ARQUIVO_HISTORICO, sep=None, engine='python', encoding='utf-8-sig')
        df_h.columns = [c.strip() for c in df_h.columns]
        
        # Converte Data para comparação (dd/mm/yyyy)
        df_h['dt_comparacao'] = pd.to_datetime(df_h['Data'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')
        
        # Limpeza de colunas numéricas
        cols_num = ['Total_Gols_FT', 'Total_Gols_HT', 'Total_Corners', 'Total_Corners_HT', 'Gols_Mandante_FT', 'Gols_Visitante_FT']
        for col in cols_num:
            if col in df_h.columns:
                df_h[col] = pd.to_numeric(df_h[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        # Coluna auxiliar para BTTS no histórico
        if 'Gols_Mandante_FT' in df_h.columns and 'Gols_Visitante_FT' in df_h.columns:
            df_h['BTTS_Realizado'] = ((df_h['Gols_Mandante_FT'] > 0) & (df_h['Gols_Visitante_FT'] > 0)).astype(int)

        df_h = df_h.dropna(subset=['dt_comparacao'])
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
        df_h = pd.DataFrame()
        
    try:
        # Carregando Agenda (Onde estavam os emojis previstos)
        df_a = pd.read_csv(URL_AGENDA, sep=None, engine='python', encoding='utf-8-sig')
        df_a.columns = [c.strip() for c in df_a.columns]
        # Pegamos apenas jogos que já passaram ou são de hoje para conferir
        df_a['dt_comparacao'] = pd.to_datetime(df_a['Data'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')
        df_a = df_a.dropna(subset=['dt_comparacao'])
    except Exception as e:
        st.error(f"Erro ao carregar agenda: {e}")
        df_a = pd.DataFrame()
        
    return df_h, df_a

def calcular_winrate(df, coluna):
    if df.empty: return 0
    total = len(df)
    greens = len(df[df[coluna] == "✅"])
    return (greens / total) * 100 if total > 0 else 0

def mostrar_backtest():
    st.title("🧪 Backtest de Assertividade (Auditoria)")
    st.markdown("Verificação automática dos jogos da agenda que já possuem resultado no histórico.")

    df_h, df_a = carregar_dados()
    
    if df_h.empty or df_a.empty:
        st.warning("Aguardando carregamento das bases...")
        return

    # --- PROCESSAMENTO ---
    lista_backtest = []

    # Vamos percorrer a agenda e ver quais jogos já existem no histórico com resultado
    for _, row in df_a.iterrows():
        m, v, data_j = str(row['Mandante']).strip(), str(row['Visitante']).strip(), row['dt_comparacao']
        
        # Busca o jogo no histórico pelo Mandante, Visitante e Data
        res_real = df_h[(df_h['Mandante'] == m) & (df_h['Visitante'] == v) & (df_h['dt_comparacao'] == data_j)]
        
        if not res_real.empty:
            real = res_real.iloc[0]
            
            # 1. Identificar o que o sistema "previu" (Baseado na mesma lógica do mostrar_jogos)
            # Buscamos as médias desse time no histórico (excluindo o jogo atual para um backtest real)
            hist_m = df_h[((df_h['Mandante'] == m) | (df_h['Visitante'] == m)) & (df_h['dt_comparacao'] != data_j)]
            hist_v = df_h[((df_h['Mandante'] == v) | (df_h['Visitante'] == v)) & (df_h['dt_comparacao'] != data_j)]
            
            if not hist_m.empty and not hist_v.empty:
                m_gols = (hist_m['Total_Gols_FT'].mean() + hist_v['Total_Gols_FT'].mean()) / 2
                m_cantos = (hist_m['Total_Corners'].mean() + hist_v['Total_Corners'].mean()) / 2
                m_btts = (hist_m['BTTS_Realizado'].mean() + hist_v['BTTS_Realizado'].mean()) / 2
                
                # Só entra no backtest se o sistema teria dado algum "emoji"
                if m_gols > 3.0 or m_cantos > 11.0 or m_btts > 0.65:
                    
                    lista_backtest.append({
                        "Data": data_j,
                        "Jogo": f"{m} x {v}",
                        "Prev: Gols": "🔥" if m_gols > 3.0 else "-",
                        "Prev: Cantos": "🚩" if m_cantos > 11.0 else "-",
                        "Prev: BTTS": "🤝" if m_btts > 0.65 else "-",
                        "0.5 HT": "✅" if real['Total_Gols_HT'] > 0.5 else "❌",
                        "2.5 FT": "✅" if real['Total_Gols_FT'] > 2.5 else "❌",
                        "BTTS Sim": "✅" if (real['Gols_Mandante_FT'] > 0 and real['Gols_Visitante_FT'] > 0) else "❌",
                        "4.5 Cnt HT": "✅" if real['Total_Corners_HT'] > 4.5 else "❌",
                        "9.5 Cnt FT": "✅" if real['Total_Corners'] > 9.5 else "❌"
                    })

    if lista_backtest:
        df_final = pd.DataFrame(lista_backtest)
        
        # --- MÉTRICAS DE RESUMO ---
        st.subheader("📈 Performance das Sugestões")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Winrate 0.5 HT", f"{calcular_winrate(df_final, '0.5 HT'):.1f}%")
        m2.metric("Winrate 2.5 FT", f"{calcular_winrate(df_final, '2.5 FT'):.1f}%")
        m3.metric("Winrate BTTS", f"{calcular_winrate(df_final, 'BTTS Sim'):.1f}%")
        m4.metric("Winrate 4.5 CHT", f"{calcular_winrate(df_final, '4.5 Cnt HT'):.1f}%")
        m5.metric("Winrate 9.5 CFT", f"{calcular_winrate(df_final, '9.5 Cnt FT'):.1f}%")

        # --- TABELA ESTILIZADA ---
        def style_backtest(val):
            if val == "✅": return 'background-color: #d4edda; color: #155724'
            if val == "❌": return 'background-color: #f8d7da; color: #721c24'
            return ''

        st.dataframe(
            df_final.style.applymap(style_backtest, subset=['0.5 HT', '2.5 FT', 'BTTS Sim', '4.5 Cnt HT', '9.5 Cnt FT']),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("Nenhum jogo da agenda foi encontrado no histórico ainda. Verifique se os nomes dos times na Agenda e no Histórico são exatamente iguais.")
