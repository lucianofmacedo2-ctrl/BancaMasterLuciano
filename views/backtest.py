import streamlit as st
import pandas as pd
import numpy as np

# Links dos arquivos (Mantendo o padrão do seu jogos.py)
URL_AGENDA = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.csv"
ARQUIVO_HISTORICO = 'dados_25_26.csv'

def carregar_dados():
    try:
        # Lendo histórico
        df_h = pd.read_csv(ARQUIVO_HISTORICO, sep=None, engine='python', encoding='utf-8-sig')
        df_h.columns = [c.strip() for c in df_h.columns]
    except:
        df_h = pd.DataFrame()
        
    try:
        # Lendo agenda (com cache para não travar o app)
        df_a = pd.read_csv(URL_AGENDA, sep=None, engine='python', encoding='utf-8-sig')
        df_a.columns = [c.strip() for c in df_a.columns]
    except:
        df_a = pd.DataFrame()
        
    return df_h, df_a

def mostrar_backtest():
    st.title("🧪 Backtest de Assertividade")
    st.markdown("""
    Esta página filtra apenas os jogos que receberam **Sinais de Alerta** e cruza com os resultados reais 
    registrados no histórico.
    """)

    df_hist, df_agenda = carregar_dados()

    if df_hist.empty or df_agenda.empty:
        st.error("Erro ao carregar arquivos para Backtest. Verifique as fontes de dados.")
        return

    backtest_list = []

    # --- LÓGICA DE FILTRAGEM (REVERSA) ---
    for _, row in df_agenda.iterrows():
        mandante = row['Mandante']
        visitante = row['Visitante']
        
        # Filtra histórico desses times para calcular se eles TINHAM sinal
        df_m = df_hist[df_hist['Mandante'] == mandante]
        df_v = df_hist[df_hist['Visitante'] == visitante]
        
        tem_gol = False
        tem_canto = False
        equilibrio = False
        
        if not df_m.empty and not df_v.empty:
            m_gols = (df_m['Gols_Mandante_FT'].mean() + df_m['Gols_Visitante_FT'].mean()) + \
                     (df_v['Gols_Mandante_FT'].mean() + df_v['Gols_Visitante_FT'].mean())
            m_cantos = (df_m['Cantos_Mandante'].mean() + df_m['Cantos_Visitante'].mean()) + \
                       (df_v['Cantos_Mandante'].mean() + df_v['Cantos_Visitante'].mean())

            if m_gols > 5.0: tem_gol = True
            if m_cantos > 15.0: tem_canto = True

        try:
            val_m = float(str(row.get('Odd Mandante', 0)).replace(',', '.'))
            val_v = float(str(row.get('Odd Visitante', 0)).replace(',', '.'))
            if abs(val_m - val_v) <= 1.0: equilibrio = True
        except: pass

        # Se tinha sinal, buscamos o resultado final no histórico
        if tem_gol or tem_canto or equilibrio:
            # Busca o resultado real da partida (Gols e Cantos)
            resultado = df_hist[(df_hist['Mandante'] == mandante) & (df_hist['Visitante'] == visitante)].head(1)
            
            if not resultado.empty:
                res = resultado.iloc[0]
                gols_total = res['Gols_Mandante_FT'] + res['Gols_Visitante_FT']
                cantos_total = res['Cantos_Mandante'] + res['Cantos_Visitante']
                
                sinal = []
                if tem_gol: sinal.append("⚽")
                if tem_canto: sinal.append("🚩")
                if equilibrio: sinal.append("⚖️")

                backtest_list.append({
                    "Data": res['Data'],
                    "Jogo": f"{mandante} x {visitante}",
                    "Sinal": " ".join(sinal),
                    "Placar": f"{int(res['Gols_Mandante_FT'])}x{int(res['Gols_Visitante_FT'])}",
                    "Cantos": int(cantos_total),
                    "Over 2.5?": "✅ SIM" if gols_total > 2.5 else "❌ NÃO",
                    "Over 9.5?": "✅ SIM" if cantos_total > 9.5 else "❌ NÃO"
                })

    if backtest_list:
        df_final = pd.DataFrame(backtest_list)
        
        # Métricas
        c1, c2, c3 = st.columns(3)
        total_j = len(df_final)
        
        # Assertividade Gols
        jogos_g = df_final[df_final['Sinal'].str.contains("⚽")]
        taxa_g = (len(jogos_g[jogos_g['Over 2.5?'] == "✅ SIM"]) / len(jogos_g) * 100) if not jogos_g.empty else 0
        
        # Assertividade Cantos
        jogos_c = df_final[df_final['Sinal'].str.contains("🚩")]
        taxa_c = (len(jogos_c[jogos_c['Over 9.5?'] == "✅ SIM"]) / len(jogos_c) * 100) if not jogos_c.empty else 0

        c1.metric("Jogos Com Sinal", total_j)
        c2.metric("Assertividade Gols", f"{taxa_g:.1f}%")
        c3.metric("Assertividade Cantos", f"{taxa_c:.1f}%")

        st.divider()
        st.dataframe(df_final, use_container_width=True, hide_index=True)
    else:
        st.info("Aguardando resultados no histórico para validar os sinais da agenda.")
