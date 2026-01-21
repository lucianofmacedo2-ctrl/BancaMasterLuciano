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

def calcular_stats_completas(serie_f, serie_s):
    """Calcula estatísticas para Feitos, Sofridos e Total do Jogo"""
    if serie_f.empty or serie_f.isnull().all():
        return pd.DataFrame()
    
    def get_metrics(s):
        media = s.mean()
        desvio = s.std() if len(s) > 1 else 0.0
        cv = (desvio / media * 100) if media > 0 else 0.0
        return {"Média": media, "DP": desvio, "CV%": cv}

    df = pd.DataFrame({
        "Marcados": get_metrics(serie_f),
        "Sofridos": get_metrics(serie_s),
        "Total Jogo": get_metrics(serie_f + serie_s)
    }).T
    return df

def calcular_probabilidades_mercado(df):
    if df.empty: return pd.DataFrame()
    n = len(df)
    g_m_ht, g_v_ht = df['Gols_Mandante_HT'], df['Gols_Visitante_HT']
    g_m_ft, g_v_ft = df['Gols_Mandante_FT'], df['Gols_Visitante_FT']
    tg_ht, tg_ft = df['Total_Gols_HT'], df['Total_Gols_FT']
    tg_st = tg_ft - tg_ht
    g_m_st = g_m_ft - g_m_ht
    g_v_st = g_v_ft - g_v_ht

    def perc(condicao): return (len(df[condicao]) / n) * 100

    data = {
        "Mercado": [
            "0.5 HT", "1.5 HT", "2.5 HT", "3.5 HT", "BTTS HT",
            "0.5 ST", "1.5 ST", "2.5 ST", "3.5 ST", "BTTS ST",
            "0.5 FT", "1.5 FT", "2.5 FT", "3.5 FT", "BTTS FT"
        ],
        "% Batido": [
            perc(tg_ht >= 0.5), perc(tg_ht >= 1.5), perc(tg_ht >= 2.5), perc(tg_ht >= 3.5), perc((g_m_ht > 0) & (g_v_ht > 0)),
            perc(tg_st >= 0.5), perc(tg_st >= 1.5), perc(tg_st >= 2.5), perc(tg_st >= 3.5), perc((g_m_st > 0) & (g_v_st > 0)),
            perc(tg_ft >= 0.5), perc(tg_ft >= 1.5), perc(tg_ft >= 2.5), perc(tg_ft >= 3.5), perc((g_m_ft > 0) & (g_v_ft > 0))
        ]
    }
    return pd.DataFrame(data)

# --- 2. INTERFACE PRINCIPAL ---

def mostrar_scout(df):
    # CSS para centralizar dados das tabelas
    st.markdown("""
        <style>
            div[data-testid="stDataFrame"] td { text-align: center !important; }
            div[data-testid="stDataFrame"] th { text-align: center !important; }
        </style>
    """, unsafe_allow_html=True)

    st.title("🚀 Scout Profissional & Inteligência")
    df.columns = [c.strip() for c in df.columns]

    # FILTROS
    c1, c2 = st.columns(2)
    liga_sel = c1.selectbox("Selecione a Liga", sorted(df['Liga'].unique()))
    df_liga = df[df['Liga'] == liga_sel].copy()
    temp_sel = c2.selectbox("Temporada", sorted(df_liga['Temporada'].unique(), reverse=True))
    
    df_season = df_liga[df_liga['Temporada'] == temp_sel].copy()
    df_season['Data'] = pd.to_datetime(df_season['Data'], dayfirst=True, errors='coerce')

    times = sorted(df_season['Mandande'].unique())
    c3, c4 = st.columns(2)
    m_sel = c3.selectbox("Mandante (Casa)", times)
    v_sel = c4.selectbox("Visitante (Fora)", [t for t in times if t != m_sel])

    # BASES
    df_m_home = df_season[df_season['Mandande'] == m_sel].sort_values('Data', ascending=False).head(10)
    df_v_away = df_season[df_season['Visitante'] == v_sel].sort_values('Data', ascending=False).head(10)
    
    # 1. COMPARATIVO DE MÉDIAS (BARRAS)
    st.divider()
    with st.container(border=True):
        st.caption("🔥 Comparativo de Médias (Últimos 10 Jogos em Casa/Fora)")
        render_stat_row("GOLS MARCADOS FT", df_m_home['Gols_Mandante_FT'].mean(), df_v_away['Gols_Visitante_FT'].mean())
        render_stat_row("CHUTES AO GOL", df_m_home['Chutes_Gol_Mandante'].mean(), df_v_away['Chutes_Gol_Visitante'].mean())
        render_stat_row("ESCANTEIOS", df_m_home['Cantos_Mandante'].mean(), df_v_away['Cantos_Visitante'].mean())
        render_stat_row("FINALIZAÇÕES", df_m_home['Finalizações_Totais_Mandante'].mean(), df_v_away['Finalizações_Totais_Visitante'].mean())

    # 2. POSIÇÕES E EFICIÊNCIA (TEXTO COMPLETO)
    tab_geral = calcular_tabela_classificacao(df_season)
    tab_casa = tab_geral[['Time', 'P_Casa']].sort_values(by='P_Casa', ascending=False).reset_index(drop=True)
    tab_fora = tab_geral[['Time', 'P_Fora']].sort_values(by='P_Fora', ascending=False).reset_index(drop=True)

    def get_info_time(df_jogos, time_nome, mando, tab_pos, tab_especifica):
        try:
            p_geral = tab_pos[tab_pos['Time'] == time_nome].index[0] + 1
            p_mando = tab_especifica[tab_especifica['Time'] == time_nome].index[0] + 1
            
            g_f = df_jogos['Gols_Mandante_FT'] if mando == "casa" else df_jogos['Gols_Visitante_FT']
            g_s = df_jogos['Gols_Visitante_FT'] if mando == "casa" else df_jogos['Gols_Mandante_FT']
            chutes = df_jogos['Chutes_Gol_Mandante'] if mando == "casa" else df_jogos['Chutes_Gol_Visitante']
            
            cs = len(g_s[g_s == 0])
            fts = len(g_f[g_f == 0])
            ch_gol = chutes.sum() / g_f.sum() if g_f.sum() > 0 else 0
            
            st.info(f"**{time_nome}**\n\n🏆 {p_geral}º Geral | {p_mando}º {'Casa' if mando=='casa' else 'Fora'}\n\n"
                    f"🧤 Clean Sheets: {cs} | 🚫 Falhou em Marcar: {fts} | 🎯 Chutes / Gol: {ch_gol:.2f}")
        except: st.warning(f"Erro ao processar dados de {time_nome}")

    ci1, ci2 = st.columns(2)
    with ci1: get_info_time(df_m_home, m_sel, "casa", tab_geral, tab_casa)
    with ci2: get_info_time(df_v_away, v_sel, "fora", tab_geral, tab_fora)

    # 3. TABS
    tab1, tab2, tab3, tab4 = st.tabs(["🕒 Forma Recente", "⚔️ H2H", "📊 Stats Detalhadas", "⏰ Minutos"])

    with tab1:
        c_f1, c_f2 = st.columns(2)
        def listar_jogos(df_j, nome, is_m):
            st.markdown(f"**{nome}**")
            for _, r in df_j.iterrows():
                res = "✅" if (r['Gols_Mandante_FT'] > r['Gols_Visitante_FT'] if is_m else r['Gols_Visitante_FT'] > r['Gols_Mandante_FT']) else ("🟧" if r['Gols_Mandante_FT'] == r['Gols_Visitante_FT'] else "❌")
                st.write(f"{res} {r['Data'].strftime('%d/%m/%y') if pd.notnull(r['Data']) else 'N/D'} vs {r['Visitante'] if is_m else r['Mandande']} ({int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])})")
        with c_f1: listar_jogos(df_m_home, m_sel, True)
        with c_f2: listar_jogos(df_v_away, v_sel, False)

    with tab2:
        h2h = df_liga[((df_liga['Mandande'] == m_sel) & (df_liga['Visitante'] == v_sel)) | ((df_liga['Mandande'] == v_sel) & (df_liga['Visitante'] == m_sel))].sort_values('Data', ascending=False).head(10)
        st.dataframe(h2h[['Data', 'Mandande', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], use_container_width=True)

    with tab3:
        metrics_map = {
            "Gols HT": ("Gols_Mandante_HT", "Gols_Visitante_HT"),
            "Gols FT": ("Gols_Mandante_FT", "Gols_Visitante_FT"),
            "Escanteios": ("Cantos_Mandante", "Cantos_Visitante"),
            "Cartões": ("Cartões_Total_Mandante", "Cartões_Total_Visitante"),
            "Chutes ao Gol": ("Chutes_Gol_Mandante", "Chutes_Gol_Visitante"),
            "Finalizações": ("Finalizações_Totais_Mandante", "Finalizações_Totais_Visitante")
        }
        for label, (col_m, col_v) in metrics_map.items():
            st.subheader(label)
            mc1, mc2 = st.columns(2)
            with mc1:
                st.write(f"**{m_sel} (Casa)**")
                st.dataframe(calcular_stats_completas(df_m_home[col_m], df_m_home[col_v]).style.format("{:.2f}"), use_container_width=True)
            with mc2:
                st.write(f"**{v_sel} (Fora)**")
                st.dataframe(calcular_stats_completas(df_v_away[col_v], df_v_away[col_m]).style.format("{:.2f}"), use_container_width=True)

    with tab4:
        def tab_minutos(df_j, nome, mando):
            st.write(f"**{nome}**")
            f_m = [f"0-15_{mando}", f"16-30_{mando}", f"31-45+_{mando}", f"46-60_{mando}", f"61-75_{mando}", f"76-90+_{mando}"]
            adv = "Visitante" if mando == "Mandante" else "Mandante"
            f_s = [f"0-15_{adv}", f"16-30_{adv}", f"31-45+_{adv}", f"46-60_{adv}", f"61-75_{adv}", f"76-90+_{adv}"]
            labels = ["0-15'", "16-30'", "31-45'", "46-60'", "61-75'", "76-90'"]
            
            feitos = df_j[f_m].sum().values
            sofridos = df_j[f_s].sum().values
            totais = feitos + sofridos
            
            df_min = pd.DataFrame([feitos, sofridos, totais], columns=labels, index=["Gols Marcados", "Gols Sofridos", "Somatório Total"])
            st.dataframe(df_min, use_container_width=True)

        tab_minutos(df_m_home, m_sel, "Mandante")
        tab_minutos(df_v_away, v_sel, "Visitante")

    # 4. FREQUÊNCIA DE MERCADOS
    st.divider()
    st.subheader("🎯 Frequência de Mercados")
    cp1, cp2 = st.columns(2)
    with cp1:
        st.write(f"**{m_sel} (Casa)**")
        st.dataframe(calcular_probabilidades_mercado(df_m_home).style.format({"% Batido": "{:.2f}%"}).background_gradient(cmap="RdYlGn", subset=['% Batido']), use_container_width=True)
    with cp2:
        st.write(f"**{v_sel} (Fora)**")
        st.dataframe(calcular_probabilidades_mercado(df_v_away).style.format({"% Batido": "{:.2f}%"}).background_gradient(cmap="RdYlGn", subset=['% Batido']), use_container_width=True)
