import streamlit as st
import pandas as pd
from datetime import datetime

# Links dos arquivos
URL_AGENDA = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/Lista_Jogos.csv"
ARQUIVO_HISTORICO = 'dados_25_26.csv'

def carregar_dados():
    try:
        df_h = pd.read_csv(ARQUIVO_HISTORICO, sep=None, engine='python', encoding='utf-8-sig')
        df_h.columns = [c.strip() for c in df_h.columns]
        df_h['dt_formatada'] = pd.to_datetime(df_h['Data'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')
        
        colunas_odds = ['Odd_Mandante_HT', 'Odd_Empate_HT', 'Odd_Visitante_HT', 'Odd_Over_25Gols_FT', 'Odd_BTTS_Sim']
        for col in colunas_odds:
            if col in df_h.columns:
                df_h[col] = pd.to_numeric(df_h[col].astype(str).str.replace(',', '.'), errors='coerce')
        
        df_h = df_h.dropna(subset=['dt_formatada'])
    except:
        df_h = pd.DataFrame()
        
    try:
        df_a = pd.read_csv(URL_AGENDA, sep=None, engine='python', encoding='utf-8-sig')
        df_a.columns = [c.strip() for c in df_a.columns]
        df_a['dt_obj'] = pd.to_datetime(df_a['Data'], dayfirst=True, errors='coerce')
        data_corte = datetime(2026, 1, 22)
        df_a = df_a[df_a['dt_obj'] >= data_corte].copy()
        df_a['dt_formatada'] = df_a['dt_obj'].dt.strftime('%d/%m/%Y')
        df_a = df_a.dropna(subset=['dt_formatada'])
    except:
        df_a = pd.DataFrame()
        
    return df_h, df_a

def calcular_winrate(df):
    if df.empty: return 0
    # Média de acerto considerando as 3 colunas principais
    hits = (len(df[df['0.5 HT?'] == "✅"]) + len(df[df['Over 2.5'] == "✅"]) + len(df[df['Over 9.5'] == "✅"]))
    total = len(df) * 3
    return (hits / total) * 100 if total > 0 else 0

def processar_metricas_categoria(df_cat, titulo_aba):
    if df_cat.empty:
        st.warning(f"Sem jogos para exibir em: {titulo_aba}")
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
        if val == "✅": return 'background-color: #d4edda; color: #155724; font-weight: bold'
        if val == "❌": return 'background-color: #f8d7da; color: #721c24; font-weight: bold'
        return ''

    st.dataframe(
        df_cat.style.applymap(style_results, subset=['0.5 HT?', 'Over 2.5', 'Over 9.5']),
        use_container_width=True, hide_index=True
    )

def mostrar_backtest():
    st.title("🧪 Backtest Profissional")

    # --- FILTROS ---
    st.subheader("🔍 Filtros de Estratégia")
    df_hist, df_agenda = carregar_dados()
    
    with st.expander("Configurações de Filtro (Odds e Gap)", expanded=True):
        f_c1, f_c2 = st.columns(2)
        with f_c1:
            usar_filtro = st.radio("Filtrar por Range de Odd?", ["Não", "Sim"], horizontal=True)
        with f_c2:
            gap_minimo = st.number_input("Gap Mínimo (Odd Visitante - Mandante):", value=0.0, step=0.5, help="Ex: 4.0 filtrará jogos com odds como 1.5 e 5.5")

        df_filtered_hist = df_hist.copy()
        col_alvo = None

        if usar_filtro == "Sim":
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                mercado = st.selectbox("Selecione o Mercado:", ["Over 2.5 Gols FT", "Mandante HT", "Empate HT", "Visitante HT", "Ambas Marcam (BTTS)"])
                mapa = {"Over 2.5 Gols FT": "Odd_Over_25Gols_FT", "Mandante HT": "Odd_Mandante_HT", "Empate HT": "Odd_Empate_HT", "Visitante HT": "Odd_Visitante_HT", "Ambas Marcam (BTTS)": "Odd_BTTS_Sim"}
                col_alvo = mapa[mercado]
            with c2:
                o_min = st.number_input("Odd Mínima", value=1.0, step=0.05)
            with c3:
                o_max = st.number_input("Odd Máxima", value=10.0, step=0.05)
            
            if col_alvo in df_filtered_hist.columns:
                df_filtered_hist = df_filtered_hist[(df_filtered_hist[col_alvo] >= o_min) & (df_filtered_hist[col_alvo] <= o_max)]

    if df_hist.empty or df_agenda.empty:
        st.warning("Carregando bases...")
        return

    back_gols, back_cantos, back_equi, back_combo = [], [], [], []

    for _, row in df_agenda.iterrows():
        mandante, visitante, data_j = str(row['Mandante']).strip(), str(row['Visitante']).strip(), row['dt_formatada']
        
        # Filtro de Gap (conforme solicitado)
        try:
            o_m = float(str(row.get('Odd Mandante', 0)).replace(',', '.'))
            o_v = float(str(row.get('Odd Visitante', 0)).replace(',', '.'))
            if abs(o_m - o_v) < gap_minimo: continue
        except: continue

        # Radar
        df_m_h = df_hist[df_hist['Mandante'] == mandante]
        df_v_h = df_hist[df_hist['Visitante'] == visitante]
        tem_gol, tem_canto, equi = False, False, False

        if not df_m_h.empty and not df_v_h.empty:
            m_gols = (df_m_h['Gols_Mandante_FT'].mean() + df_m_h['Gols_Visitante_FT'].mean()) + (df_v_h['Gols_Mandante_FT'].mean() + df_v_h['Gols_Visitante_FT'].mean())
            m_cants = (df_m_h['Cantos_Mandante'].mean() + df_m_h['Cantos_Visitante'].mean()) + (df_v_h['Cantos_Mandante'].mean() + df_v_h['Cantos_Visitante'].mean())
            if m_gols > 5.0: tem_gol = True
            if m_cants > 15.0: tem_canto = True
        
        try:
            if abs(o_m - o_v) <= 1.0: equi = True
        except: pass

        res_p = df_filtered_hist[(df_filtered_hist['Mandante'] == mandante) & (df_filtered_hist['Visitante'] == visitante) & (df_filtered_hist['dt_formatada'] == data_j)]
        
        if not res_p.empty:
            res = res_p.iloc[0]
            g_ht, g_ft, c_ft = (res['Gols_Mandante_HT'] + res['Gols_Visitante_HT']), (res['Gols_Mandante_FT'] + res['Gols_Visitante_FT']), (res['Cantos_Mandante'] + res['Cantos_Visitante'])
            item = {"Data": res['Data'], "Jogo": f"{mandante} x {visitante}", "Odd": res[col_alvo] if col_alvo and usar_filtro == "Sim" else "-", "Placar FT": f"{int(res['Gols_Mandante_FT'])}x{int(res['Gols_Visitante_FT'])}", "0.5 HT?": "✅" if g_ht >= 0.5 else "❌", "Over 2.5": "✅" if g_ft > 2.5 else "❌", "Over 9.5": "✅" if c_ft > 9.5 else "❌"}
            if tem_gol: back_gols.append(item)
            if tem_canto: back_cantos.append(item)
            if equi: back_equi.append(item)
            if tem_gol and tem_canto: back_combo.append(item)

    # --- RANKING DE LUCRATIVIDADE ---
    st.divider()
    st.subheader("🏆 Ranking de Assertividade")
    df_g, df_c, df_e, df_cb = pd.DataFrame(back_gols), pd.DataFrame(back_cantos), pd.DataFrame(back_equi), pd.DataFrame(back_combo)
    
    ranks = [
        {"Estratégia": "🔥 Gols", "Winrate": calcular_winrate(df_g), "Jogos": len(df_g)},
        {"Estratégia": "🚩 Cantos", "Winrate": calcular_winrate(df_c), "Jogos": len(df_c)},
        {"Estratégia": "⚖️ Equilíbrio", "Winrate": calcular_winrate(df_e), "Jogos": len(df_e)},
        {"Estratégia": "🔥🚩 Combo", "Winrate": calcular_winrate(df_cb), "Jogos": len(df_cb)},
    ]
    df_rank = pd.DataFrame(ranks).sort_values(by="Winrate", ascending=False)
    
    cols = st.columns(4)
    for i, row_r in enumerate(df_rank.iterrows()):
        cols[i].metric(row_r[1]['Estratégia'], f"{row_r[1]['Winrate']:.1f}%", f"{row_r[1]['Jogos']} jogos")

    # --- EXIBIÇÃO DAS ABAS ---
    t1, t2, t3, t4 = st.tabs(["🔥 Gols", "🚩 Cantos", "⚖️ Equilíbrio", "🔥🚩 Fogo Combo"])
    with t1: processar_metricas_categoria(df_g, "Estratégia Gols")
    with t2: processar_metricas_categoria(df_c, "Estratégia Cantos")
    with t3: processar_metricas_categoria(df_e, "Estratégia Equilíbrio")
    with t4: processar_metricas_categoria(df_cb, "Estratégia Fogo Combo")
