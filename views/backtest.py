import streamlit as st
import pandas as pd
from datetime import datetime

# Links dos arquivos
URL_AGENDA = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.csv"
ARQUIVO_HISTORICO = 'dados_25_26.csv'

def carregar_dados():
    # Carregar Histórico
    try:
        df_h = pd.read_csv(ARQUIVO_HISTORICO, sep=None, engine='python', encoding='utf-8-sig')
        df_h.columns = [c.strip() for c in df_h.columns]
        # Garante que a coluna de data no histórico seja string para comparação direta
        df_h['Data_Ref'] = pd.to_datetime(df_h['Data'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')
    except:
        df_h = pd.DataFrame()
        
    # Carregar Agenda
    try:
        df_a = pd.read_csv(URL_AGENDA, sep=None, engine='python', encoding='utf-8-sig')
        df_a.columns = [c.strip() for c in df_a.columns]
        
        # Converter coluna Data para objeto datetime para o filtro de corte
        df_a['dt_obj'] = pd.to_datetime(df_a['Data'], dayfirst=True, errors='coerce')
        
        # Filtro: Apenas jogos de 22/01/2026 em diante
        data_corte = datetime(2026, 1, 22)
        df_a = df_a[df_a['dt_obj'] >= data_corte].copy()
        
        # Criar coluna de comparação formatada
        df_a['Data_Ref'] = df_a['dt_obj'].dt.strftime('%d/%m/%Y')
    except:
        df_a = pd.DataFrame()
        
    return df_h, df_a

def processar_metricas_categoria(df_cat, titulo_aba):
    if df_cat.empty:
        st.warning(f"Nenhum jogo processado para: {titulo_aba}")
        return

    total_j = len(df_cat)
    taxa_ht = (len(df_cat[df_cat['0.5 HT?'] == "✅"]) / total_j * 100)
    taxa_ft = (len(df_cat[df_cat['Over 2.5'] == "✅"]) / total_j * 100)
    taxa_cnt = (len(df_cat[df_cat['Over 9.5'] == "✅"]) / total_j * 100)

    st.markdown(f"### 📊 Performance: {titulo_aba}")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Jogos", total_j)
    c2.metric("Taxa 0.5 HT", f"{taxa_ht:.1f}%")
    c3.metric("Taxa 2.5 FT", f"{taxa_ft:.1f}%")
    c4.metric("Taxa 9.5 Cantos", f"{taxa_cnt:.1f}%")

    def style_results(val):
        if val == "✅": return 'color: green; font-weight: bold'
        if val == "❌": return 'color: red; font-weight: bold'
        return ''

    st.dataframe(
        df_cat.style.applymap(style_results, subset=['0.5 HT?', 'Over 2.5', 'Over 9.5']),
        use_container_width=True, 
        hide_index=True
    )
    st.divider()

def mostrar_backtest():
    st.title("🧪 Backtest (Desde 22/01/2026)")
    st.info("Analizando jogos da agenda que possuem resultados registrados no histórico.")

    df_hist, df_agenda = carregar_dados()

    if df_hist.empty or df_agenda.empty:
        st.error("Não foi possível carregar os dados da Agenda ou do Histórico.")
        return

    back_gols, back_cantos, back_equilibrio = [], [], []

    # Percorre a agenda filtrada (>= 22/01/2026)
    for _, row in df_agenda.iterrows():
        mandante = str(row['Mandante']).strip()
        visitante = str(row['Visitante']).strip()
        data_ref = row['Data_Ref']
        
        # --- LÓGICA DE CRITÉRIOS (IDÊNTICA AO JOGOS.PY) ---
        df_m_hist = df_hist[df_hist['Mandante'] == mandante]
        df_v_hist = df_hist[df_hist['Visitante'] == visitante]
        
        tem_gol = False
        tem_canto = False
        equilibrio = False

        if not df_m_hist.empty and not df_v_hist.empty:
            m_gols = (df_m_hist['Gols_Mandante_FT'].mean() + df_m_hist['Gols_Visitante_FT'].mean()) + \
                     (df_v_hist['Gols_Mandante_FT'].mean() + df_v_hist['Gols_Visitante_FT'].mean())
            
            m_cantos = (df_m_hist['Cantos_Mandante'].mean() + df_m_hist['Cantos_Visitante'].mean()) + \
                       (df_v_hist['Cantos_Mandante'].mean() + df_v_hist['Cantos_Visitante'].mean())

            if m_gols > 5.0: tem_gol = True
            if m_cantos > 15.0: tem_canto = True

        # Lógica de Equilíbrio pelas Odds
        try:
            val_m = float(str(row.get('Odd Mandante', 0)).replace(',', '.'))
            val_v = float(str(row.get('Odd Visitante', 0)).replace(',', '.'))
            if abs(val_m - val_v) <= 1.0:
                equilibrio = True
        except:
            pass

        # --- BUSCA DO RESULTADO NO HISTÓRICO ---
        # Procura o jogo específico pela data e times
        res_partida = df_hist[
            (df_hist['Mandante'] == mandante) & 
            (df_hist['Visitante'] == visitante) & 
            (df_hist['Data_Ref'] == data_ref)
        ]
        
        if not res_partida.empty:
            res = res_partida.iloc[0]
            g_ht = res['Gols_Mandante_HT'] + res['Gols_Visitante_HT']
            g_ft = res['Gols_Mandante_FT'] + res['Gols_Visitante_FT']
            c_ft = res['Cantos_Mandante'] + res['Cantos_Visitante']
            
            dados = {
                "Data": res['Data'],
                "Jogo": f"{mandante} x {visitante}",
                "Placar HT": f"{int(res['Gols_Mandante_HT'])}x{int(res['Gols_Visitante_HT'])}",
                "Placar FT": f"{int(res['Gols_Mandante_FT'])}x{int(res['Gols_Visitante_FT'])}",
                "Cantos": int(c_ft),
                "0.5 HT?": "✅" if g_ht >= 0.5 else "❌",
                "Over 2.5": "✅" if g_ft > 2.5 else "❌",
                "Over 9.5": "✅" if c_ft > 9.5 else "❌"
            }

            if tem_gol: back_gols.append(dados)
            if tem_canto: back_cantos.append(dados)
            if equilibrio: back_equilibrio.append(dados)

    # Exibição nas Tabs
    tab1, tab2, tab3 = st.tabs(["🔥 Gols", "🚩 Cantos", "⚖️ Equilíbrio"])
    
    with tab1:
        processar_metricas_categoria(pd.DataFrame(back_gols), "Fogo 2.5 FT")
    
    with tab2:
        processar_metricas_categoria(pd.DataFrame(back_cantos), "Fogo 9.5 Cantos")
        
    with tab3:
        processar_metricas_categoria(pd.DataFrame(back_equilibrio), "Equilibrados")
