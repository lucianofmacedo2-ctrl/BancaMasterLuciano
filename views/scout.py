import streamlit as st
import pandas as pd
import numpy as np

# --- 1. FUNÇÕES DE APOIO E CÁLCULO ---

def render_stat_row(label, val_home, val_away):
    """Gera a linha visual estilo barra de comparação"""
    col1, col2, col3 = st.columns([1, 2, 1])
    total = val_home + val_away
    p_home = (val_home / total) if total > 0 else 0.5
    with col1:
        st.markdown(f"<p style='text-align: right; font-size: 18px; font-weight: bold; margin:0;'>{val_home:.2f}</p>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<p style='text-align: center; font-size: 11px; color: gray; margin:0;'>{label}</p>", unsafe_allow_html=True)
        st.progress(p_home)
    with col3:
        st.markdown(f"<p style='text-align: left; font-size: 18px; font-weight: bold; margin:0;'>{val_away:.2f}</p>", unsafe_allow_html=True)

def calcular_tabela_classificacao(df_liga):
    stats = {}
    for _, row in df_liga.iterrows():
        m, v = row['Mandande'], row['Visitante']
        gm, gv = row['Gols_Mandante_FT'], row['Gols_Visitante_FT']
        for t in [m, v]:
            if t not in stats:
                stats[t] = {'P':0, 'J':0, 'V':0, 'E':0, 'D':0, 'GP':0, 'GC':0, 'P_Casa':0, 'J_Casa':0, 'P_Fora':0, 'J_Fora':0}
        stats[m]['J'] += 1; stats[v]['J'] += 1
        stats[m]['GP'] += gm; stats[m]['GC'] += gv
        stats[v]['GP'] += gv; stats[v]['GC'] += gm
        stats[m]['J_Casa'] += 1; stats[v]['J_Fora'] += 1
        if gm > gv:
            stats[m]['P'] += 3; stats[m]['V'] += 1; stats[m]['P_Casa'] += 3; stats[v]['D'] += 1
        elif gm == gv:
            stats[m]['P'] += 1; stats[v]['P'] += 1; stats[m]['E'] += 1; stats[v]['E'] += 1
            stats[m]['P_Casa'] += 1; stats[v]['P_Fora'] += 1
        else:
            stats[v]['P'] += 3; stats[v]['V'] += 1; stats[v]['P_Fora'] += 3; stats[m]['D'] += 1
    df_tab = pd.DataFrame.from_dict(stats, orient='index').reset_index().rename(columns={'index': 'Time'})
    df_tab['SG'] = df_tab['GP'] - df_tab['GC']
    return df_tab.sort_values(by=['P', 'V', 'SG'], ascending=False).reset_index(drop=True)

def calcular_stats_completas(serie):
    if serie.empty or serie.isnull().all():
        return {"Média": 0.0, "Mediana": 0.0, "DP": 0.0, "CV%": 0.0}
    s = serie.dropna()
    media = s.mean()
    mediana = s.median()
    desvio = s.std() if len(s) > 1 else 0.0
    cv = (desvio / media * 100) if media > 0 else 0.0
    return {"Média": media, "Mediana": mediana, "DP": desvio, "CV%": cv}

def extrair_eficiencia(df_jogos, mando="casa"):
    if df_jogos.empty: return 0, 0, 0
    gols_sofridos = df_jogos['Gols_Visitante_FT'] if mando == "casa" else df_jogos['Gols_Mandante_FT']
    cs = len(gols_sofridos[gols_sofridos == 0])
    gols_feitos = df_jogos['Gols_Mandante_FT'] if mando == "casa" else df_jogos['Gols_Visitante_FT']
    fts = len(gols_feitos[gols_feitos == 0])
    chutes = df_jogos['Chutes_Gol_Mandante'].sum() if mando == "casa" else df_jogos['Chutes_Gol_Visitante'].sum()
    gols = gols_feitos.sum()
    ch_por_gol = chutes / gols if gols > 0 else 0
    return cs, fts, ch_por_gol

def calcular_probabilidades_mercado(df):
    if df.empty: return pd.DataFrame()
    n = len(df)
    gols_st = df['Total_Gols_FT'] - df['Total_Gols_HT']
    data = {
        "Mercado": [
            "Ambas Marcam FT", "0.5 Gols HT", "1.5 Gols HT", 
            "0.5 Gols FT", "1.5 Gols FT", "2.5 Gols FT", "3.5 Gols FT",
            "0.5 Gols ST", "1.5 Gols ST"
        ],
        "% Batido": [
            (len(df[(df['Gols_Mandante_FT'] > 0) & (df['Gols_Visitante_FT'] > 0)]) / n) * 100,
            (len(df[df['Total_Gols_HT'] >= 0.5]) / n) * 100,
            (len(df[df['Total_Gols_HT'] >= 1.5]) / n) * 100,
            (len(df[df['Total_Gols_FT'] >= 0.5]) / n) * 100,
            (len(df[df['Total_Gols_FT'] >= 1.5]) / n) * 100,
            (len(df[df['Total_Gols_FT'] >= 2.5]) / n) * 100,
            (len(df[df['Total_Gols_FT'] >= 3.5]) / n) * 100,
            (len(df[gols_st >= 0.5]) / n) * 100,
            (len(df[gols_st >= 1.5]) / n) * 100,
        ]
    }
    return pd.DataFrame(data)

def formatar_data_seguro(valor):
    try: return valor.strftime('%d/%m/%y')
    except: return "N/D"

# --- 2. INTERFACE PRINCIPAL ---

def mostrar_scout(df):
    st.title("🚀 Scout Profissional & Inteligência")
    df.columns = [c.strip() for c in df.columns]

    # FILTROS
    c1, c2 = st.columns(2)
    liga_sel = c1.selectbox("Liga", sorted(df['Liga'].unique()))
    df_liga = df[df['Liga'] == liga_sel].copy()
    temp_sel = c2.selectbox("Temporada", sorted(df_liga['Temporada'].unique(), reverse=True))
    
    df_season = df_liga[df_liga['Temporada'] == temp_sel].copy()
    df_season['Data'] = pd.to_datetime(df_season['Data'], dayfirst=True, errors='coerce')

    times = sorted(df_season['Mandande'].unique())
    c3, c4 = st.columns(2)
    m_sel = c3.selectbox("Mandante", times)
    v_sel = c4.selectbox("Visitante", [t for t in times if t != m_sel])

    # BASES
    df_m_home = df_season[df_season['Mandande'] == m_sel].sort_values('Data', ascending=False).head(10)
    df_v_away = df_season[df_season['Visitante'] == v_sel].sort_values('Data', ascending=False).head(10)
    
    # 1. PAINEL DE PRESSÃO
    st.divider()
    with st.container(border=True):
        st.caption("🔥 Comparativo de Médias (Últimos 10 Jogos em Casa/Fora)")
        render_stat_row("GOLS MARCADOS FT", df_m_home['Gols_Mandante_FT'].mean(), df_v_away['Gols_Visitante_FT'].mean())
        render_stat_row("CHUTES AO GOL", df_m_home['Chutes_Gol_Mandante'].mean(), df_v_away['Chutes_Gol_Visitante'].mean())
        render_stat_row("ESCANTEIOS", df_m_home['Cantos_Mandante'].mean(), df_v_away['Cantos_Visitante'].mean())
        render_stat_row("FINALIZAÇÕES", df_m_home['Finalizações_Totais_Mandante'].mean(), df_v_away['Finalizações_Totais_Visitante'].mean())

    # 2. POSIÇÕES E EFICIÊNCIA
    tabela = calcular_tabela_classificacao(df_season)
    cs_m, fts_m, ch_g_m = extrair_eficiencia(df_m_home, "casa")
    cs_v, fts_v, ch_g_v = extrair_eficiencia(df_v_away, "fora")

    col_info1, col_info2 = st.columns(2)
    with col_info1:
        try:
            pos_m = tabela[tabela['Time'] == m_sel].index[0] + 1
            st.info(f"🏆 {m_sel}: {pos_m}º Lugar\n\n🧤 CS: {cs_m} | 🚫 FTS: {fts_m} | 🎯 Ch/Gol: {ch_g_m:.1f}")
        except: st.warning(f"Sem dados de tabela para {m_sel}")
        
    with col_info2:
        try:
            pos_v = tabela[tabela['Time'] == v_sel].index[0] + 1
            st.info(f"🏆 {v_sel}: {pos_v}º Lugar\n\n🧤 CS: {cs_v} | 🚫 FTS: {fts_v} | 🎯 Ch/Gol: {ch_g_v:.1f}")
        except: st.warning(f"Sem dados de tabela para {v_sel}")

    # 3. TABS
    tab1, tab2, tab3, tab4 = st.tabs(["🕒 Forma Recente", "⚔️ H2H", "📊 Stats Detalhadas", "⏰ Minutos"])

    with tab1:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            st.markdown(f"**{m_sel} (Casa)**")
            for _, r in df_m_home.iterrows():
                res = "✅" if r['Gols_Mandante_FT'] > r['Gols_Visitante_FT'] else ("🟧" if r['Gols_Mandante_FT'] == r['Gols_Visitante_FT'] else "❌")
                st.write(f"{res} {formatar_data_seguro(r['Data'])} vs {r['Visitante']} ({int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])})")
        with col_f2:
            st.markdown(f"**{v_sel} (Fora)**")
            for _, r in df_v_away.iterrows():
                res = "✅" if r['Gols_Visitante_FT'] > r['Gols_Mandante_FT'] else ("🟧" if r['Gols_Mandante_FT'] == r['Gols_Visitante_FT'] else "❌")
                st.write(f"{res} {formatar_data_seguro(r['Data'])} vs {r['Mandande']} ({int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])})")

    with tab2:
        h2h = df_liga[((df_liga['Mandande'] == m_sel) & (df_liga['Visitante'] == v_sel)) | ((df_liga['Mandande'] == v_sel) & (df_liga['Visitante'] == m_sel))].sort_values('Data', ascending=False).head(10)
        if not h2h.empty:
            st.dataframe(h2h[['Data', 'Mandande', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], use_container_width=True)
        else:
            st.write("Nenhum confronto direto encontrado.")

    with tab3:
        metricas = {"Gols FT": ("Gols_Mandante_FT", "Gols_Visitante_FT"), "Cantos": ("Cantos_Mandante", "Cantos_Visitante")}
        for label, (col_m, col_v) in metricas.items():
            st.write(f"**{label}**")
            m_col, v_col = st.columns(2)
            df_st_m = pd.DataFrame({"Mandante": calcular_stats_completas(df_m_home[col_m])}).T
            df_st_v = pd.DataFrame({"Visitante": calcular_stats_completas(df_v_away[col_v])}).T
            m_col.dataframe(df_st_m.style.format("{:.2f}"))
            v_col.dataframe(df_st_v.style.format("{:.2f}"))

    with tab4:
        faixas_m = ["0-15_Mandante", "16-30_Mandante", "31-45+_Mandante", "46-60_Mandante", "61-75_Mandante", "76-90+_Mandante"]
        faixas_v = ["0-15_Visitante", "16-30_Visitante", "31-45+_Visitante", "46-60_Visitante", "61-75_Visitante", "76-90+_Visitante"]
        labels = ["0-15'", "16-30'", "31-45'", "46-60'", "61-75'", "76-90'"]
        try:
            st.write(f"**Gols por minuto - {m_sel} (Casa)**")
            st.dataframe(pd.DataFrame([df_m_home[faixas_m].sum().values], columns=labels, index=["Gols"]), use_container_width=True)
            st.write(f"**Gols por minuto - {v_sel} (Fora)**")
            st.dataframe(pd.DataFrame([df_v_away[faixas_v].sum().values], columns=labels, index=["Gols"]), use_container_width=True)
        except: st.warning("Colunas de minutos não encontradas no CSV.")

    st.divider()
    st.subheader("🎯 Frequência de Mercados")
    cp1, cp2 = st.columns(2)
    with cp1: st.dataframe(calcular_probabilidades_mercado(df_m_home).style.background_gradient(cmap="RdYlGn", subset=['% Batido']), use_container_width=True)
    with cp2: st.dataframe(calcular_probabilidades_mercado(df_v_away).style.background_gradient(cmap="RdYlGn", subset=['% Batido']), use_container_width=True)
