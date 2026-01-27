import streamlit as st
import pandas as pd
import numpy as np

# Links dos arquivos
URL_AGENDA = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.csv"
ARQUIVO_HISTORICO = 'dados_25_26.csv'

def carregar_dados():
    try:
        df_h = pd.read_csv(ARQUIVO_HISTORICO, sep=None, engine='python', encoding='utf-8-sig')
        df_h.columns = [c.strip() for c in df_h.columns]
    except:
        df_h = pd.DataFrame()
        
    try:
        df_a = pd.read_csv(URL_AGENDA, sep=None, engine='python', encoding='utf-8-sig')
        df_a.columns = [c.strip() for c in df_a.columns]
    except:
        df_a = pd.DataFrame()
        
    return df_h, df_a

def mostrar_backtest():
    st.title("🧪 Backtest de Assertividade")
    st.markdown("""
    Cruzamento automático entre os **Sinais da Agenda** e os **Resultados Reais** do histórico.
    """)

    df_hist, df_agenda = carregar_dados()

    if df_hist.empty or df_agenda.empty:
        st.error("Arquivos de dados não encontrados para processar o Backtest.")
        return

    backtest_list = []

    for _, row in df_agenda.iterrows():
        mandante = row['Mandante']
        visitante = row['Visitante']
        
        # Filtros de sinal (mesma lógica do jogos.py)
        df_m = df_hist[df_hist['Mandante'] == mandante]
        df_v = df_hist[df_hist['Visitante'] == visitante]
        
        tem_gol = False
        tem_canto = False
        
        if not df_m.empty and not df_v.empty:
            m_gols = (df_m['Gols_Mandante_FT'].mean() + df_m['Gols_Visitante_FT'].mean()) + \
                     (df_v['Gols_Mandante_FT'].mean() + df_v['Gols_Visitante_FT'].mean())
            m_cantos = (df_m['Cantos_Mandante'].mean() + df_m['Cantos_Visitante'].mean()) + \
                       (df_v['Cantos_Mandante'].mean() + df_v['Cantos_Visitante'].mean())

            if m_gols > 5.0: tem_gol = True
            if m_cantos > 15.0: tem_canto = True

        # Se tinha sinal, busca no histórico o resultado
        if tem_gol or tem_canto:
            resultado = df_hist[(df_hist['Mandante'] == mandante) & (df_hist['Visitante'] == visitante)].head(1)
            
            if not resultado.empty:
                res = resultado.iloc[0]
                
                # Dados FT
                g_tot_ft = res['Gols_Mandante_FT'] + res['Gols_Visitante_FT']
                c_tot = res['Cantos_Mandante'] + res['Cantos_Visitante']
                
                # Dados HT
                g_tot_ht = res['Gols_Mandante_HT'] + res['Gols_Visitante_HT']
                
                sinal = []
                if tem_gol: sinal.append("⚽")
                if tem_canto: sinal.append("🚩")

                backtest_list.append({
                    "Data": res['Data'],
                    "Jogo": f"{mandante} x {visitante}",
                    "Sinal": " ".join(sinal),
                    "Placar HT": f"{int(res['Gols_Mandante_HT'])}x{int(res['Gols_Visitante_HT'])}",
                    "Placar FT": f"{int(res['Gols_Mandante_FT'])}x{int(res['Gols_Visitante_FT'])}",
                    "Cantos": int(c_tot),
                    "0.5 HT?": "✅" if g_tot_ht >= 0.5 else "❌",
                    "Over 2.5": "✅" if g_tot_ft > 2.5 else "❌",
                    "Over 9.5": "✅" if c_tot > 9.5 else "❌"
                })

    if backtest_list:
        df_final = pd.DataFrame(backtest_list)
        
        # Métricas de topo - Agora com 4 colunas
        c1, c2, c3, c4 = st.columns(4)
        total_j = len(df_final)
        
        # Cálculos de Assertividade
        taxa_ht = (len(df_final[df_final['0.5 HT?'] == "✅"]) / total_j * 100) if total_j > 0 else 0
        
        jogos_g = df_final[df_final['Sinal'].str.contains("⚽")]
        taxa_g = (len(jogos_g[jogos_g['Over 2.5'] == "✅"]) / len(jogos_g) * 100) if not jogos_g.empty else 0
        
        jogos_c = df_final[df_final['Sinal'].str.contains("🚩")]
        taxa_c = (len(jogos_c[jogos_c['Over 9.5'] == "✅"]) / len(jogos_c) * 100) if not jogos_c.empty else 0

        c1.metric("Total Jogos", total_j)
        c2.metric("% Batido 0.5 HT", f"{taxa_ht:.1f}%")
        c3.metric("Acerto Over 2.5", f"{taxa_g:.1f}%")
        c4.metric("Acerto Over 9.5", f"{taxa_c:.1f}%")

        st.divider()
        
        # Estilização básica para destacar os acertos/erros
        def style_results(val):
            if val == "✅": return 'color: green; font-weight: bold'
            if val == "❌": return 'color: red; font-weight: bold'
            return ''

        st.dataframe(
            df_final.style.applymap(style_results, subset=['0.5 HT?', 'Over 2.5', 'Over 9.5']),
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.info("Nenhum jogo com sinal encontrado no histórico ainda.")
