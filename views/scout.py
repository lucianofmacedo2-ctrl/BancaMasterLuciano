import streamlit as st
import pandas as pd
import numpy as np

# --- 1. FUNÇÕES DE APOIO E CÁLCULO ---

def render_stat_row(label, val_home, val_away):
    col1, col2, col3 = st.columns([1, 2, 1])
    total = (val_home or 0) + (val_away or 0)
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
        m, v = row['Mandante'], row['Visitante']
        gm, gv = row['Gols_Mandante_FT'], row['Gols_Visitante_FT']
        for t in [m, v]:
            if t not in stats:
                stats[t] = {'P':0, 'J':0, 'V':0, 'E':0, 'D':0, 'GP':0, 'GC':0, 'P_Casa':0, 'P_Fora':0}
        stats[m]['J'] += 1; stats[v]['J'] += 1
        stats[m]['GP'] += gm; stats[m]['GC'] += gv
        stats[v]['GP'] += gv; stats[v]['GC'] += gm
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
    def get_metrics(s):
        s = pd.to_numeric(s, errors='coerce').fillna(0)
        m = s.mean()
        dp = s.std() if len(s) > 1 else 0.0
        cv = (dp / m * 100) if m > 0 else 0.0
        return {"Média": m, "DP": dp, "CV%": cv}
    sf = pd.to_numeric(serie_f, errors='coerce').fillna(0)
    ss = pd.to_numeric(serie_s, errors='coerce').fillna(0)
    return pd.DataFrame({
        "Marcados": get_metrics(sf),
        "Sofridos": get_metrics(ss),
        "Total Jogo": get_metrics(sf + ss)
    }).T

def calcular_probabilidades_mercado(df):
    if df.empty: return pd.DataFrame()
    n = len(df)
    tg_ht, tg_ft = df['Total_Gols_HT'], df['Total_Gols_FT']
    tg_st = tg_ft - tg_ht
    gm_ht, gv_ht = df['Gols_Mandante_HT'], df['Gols_Visitante_HT']
    def perc(cond): return (len(df[cond]) / n) * 100
    
    mercados = []
    for pref, stot, sm, sv in [("HT", tg_ht, gm_ht, gv_ht), ("ST", tg_st, (df['Gols_Mandante_FT']-gm_ht), (df['Gols_Visitante_FT']-gv_ht)), ("FT", tg_ft, df['Gols_Mandante_FT'], df['Gols_Visitante_FT'])]:
        for g in [0.5, 1.5, 2.5, 3.5]:
            mercados.append({"Mercado": f"{g} {pref}", "% Batido": perc(stot >= g)})
        mercados.append({"Mercado": f"BTTS {pref}", "% Batido": perc((sm > 0) & (sv > 0))})
    return pd.DataFrame(mercados)

# --- 2. INTERFACE PRINCIPAL ---

def mostrar_scout(df):
    st.markdown("""<style>div[data-testid="stDataFrame"] td { text-align: center !important; } .stMetric { text-align: center !important; }</style>""", unsafe_allow_html=True)
    st.title("🚀 Scout Profissional")

    # Recupera times vindos da Agenda
    t_m_v = st.session_state.get('time_casa_scout', None)
    t_v_v = st.session_state.get('time_fora_scout', None)

    # Seleção automática de Liga
    default_liga_idx = 0
    if t_m_v:
        l_encontrada = df[df['Mandante'] == t_m_v]['Liga'].unique()
        if len(l_encontrada) > 0:
            ligas_lista = sorted(df['Liga'].unique())
            default_liga_idx = ligas_lista.index(l_encontrada[0])

    c1, c2 = st.columns(2)
    liga_sel = c1.selectbox("Selecione a Liga", sorted(df['Liga'].unique()), index=default_liga_idx, key="scout_liga_sel")
    df_l = df[df['Liga'] == liga_sel].copy()
    
    temp_sel = c2.selectbox("Temporada", sorted(df_l['Temporada'].unique(), reverse=True), key="scout_temp_sel")
    df_s = df_l[df_l['Temporada'] == temp_sel].copy()
    df_s['Data'] = pd.to_datetime(df_s['Data'], dayfirst=True, errors='coerce')
    
    times = sorted(df_s['Mandante'].unique())
    idx_m = times.index(t_m_v) if t_m_v in times else 0
    
    # Define Mandante e Visitante com Session State
    m_sel = c3, c4 = st.columns(2)
    m_sel = c3.selectbox("Mandante (Casa)", times, index=idx_m, key="scout_m_sel")
    
    opcoes_v = [t for t in times if t != m_sel]
    idx_v = opcoes_v.index(t_v_v) if t_v_v in opcoes_v else 0
    v_sel = c4.selectbox("Visitante (Fora)", opcoes_v, index=idx_v, key="scout_v_sel")

    # BASES DE DADOS
    df_m_h = df_s[df_s['Mandante'] == m_sel].sort_values('Data', ascending=False).head(10)
    df_v_a = df_s[df_s['Visitante'] == v_sel].sort_values('Data', ascending=False).head(10)

    # 1. VOLUME DE JOGO
    st.divider()
    with st.container(border=True):
        st.caption("🔥 Volume de Jogo (Últimos 10 Jogos Casa/Fora)")
        render_stat_row("GOLS MARCADOS FT", df_m_h['Gols_Mandante_FT'].mean(), df_v_a['Gols_Visitante_FT'].mean())
        render_stat_row("CHUTES AO GOL", df_m_h['Chutes_Gol_Mandante'].mean(), df_v_a['Chutes_Gol_Visitante'].mean())
        render_stat_row("ESCANTEIOS", df_m_h['Cantos_Mandante'].mean(), df_v_a['Cantos_Visitante'].mean())

    # 2. POSIÇÕES E EFICIÊNCIA (RESTAURADO)
    tab_geral = calcular_tabela_classificacao(df_s)
    tab_casa = tab_geral[['Time', 'P_Casa']].sort_values(by='P_Casa', ascending=False).reset_index(drop=True)
    tab_fora = tab_geral[['Time', 'P_Fora']].sort_values(by='P_Fora', ascending=False).reset_index(drop=True)

    col_i1, col_i2 = st.columns(2)
    for col, time, mando, t_esp in zip([col_i1, col_i2], [m_sel, v_sel], ["casa", "fora"], [tab_casa, tab_fora]):
        with col:
            pos_g = tab_geral[tab_geral['Time'] == time].index[0] + 1
            pos_m = t_esp[t_esp['Time'] == time].index[0] + 1
            df_ref = df_m_h if mando == "casa" else df_v_a
            gf = df_ref['Gols_Mandante_FT'] if mando == "casa" else df_ref['Gols_Visitante_FT']
            gs = df_ref['Gols_Visitante_FT'] if mando == "casa" else df_ref['Gols_Mandante_FT']
            ch = df_ref['Chutes_Gol_Mandante'] if mando == "casa" else df_ref['Chutes_Gol_Visitante']
            
            st.info(f"**{time}**\n\n🏆 {pos_g}º Geral | {pos_m}º {mando.capitalize()}\n\n"
                    f"🧤 Clean Sheets: {len(gs[gs==0])} | 🚫 Falhou em Marcar: {len(gf[gf==0])}\n\n"
                    f"🎯 Chutes / Gol: {(ch.sum()/gf.sum() if gf.sum()>0 else 0):.2f}")

    # 3. TABS
    t1, t2, t3, t4 = st.tabs(["🕒 Forma Recente", "⚔️ H2H", "📊 Stats Detalhadas", "⏰ Minutos"])

    with t1:
        cf1, cf2 = st.columns(2)
        with cf1:
            st.markdown(f"**{m_sel} (Casa)**")
            for _, r in df_m_h.iterrows():
                res = "✅" if r['Gols_Mandante_FT'] > r['Gols_Visitante_FT'] else ("🟧" if r['Gols_Mandante_FT'] == r['Gols_Visitante_FT'] else "❌")
                st.write(f"{res} {r['Data'].strftime('%d/%m')} vs {r['Visitante']} ({int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])})")
        with cf2:
            st.markdown(f"**{v_sel} (Fora)**")
            for _, r in df_v_a.iterrows():
                res = "✅" if r['Gols_Visitante_FT'] > r['Gols_Mandante_FT'] else ("🟧" if r['Gols_Visitante_FT'] == r['Gols_Visitante_FT'] else "❌")
                st.write(f"{res} {r['Data'].strftime('%d/%m')} vs {r['Mandante']} ({int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])})")

    with t2:
        h2h = df_s[((df_s['Mandante'] == m_sel) & (df_s['Visitante'] == v_sel)) | ((df_s['Mandante'] == v_sel) & (df_s['Visitante'] == m_sel))].sort_values('Data', ascending=False).head(10)
        st.dataframe(h2h[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], use_container_width=True, hide_index=True)

    with t3:
        mapa = {"Gols HT": ("Gols_Mandante_HT", "Gols_Visitante_HT"), "Gols FT": ("Gols_Mandante_FT", "Gols_Visitante_FT"), 
                "Escanteios": ("Cantos_Mandante", "Cantos_Visitante"), "Chutes ao G": ("Chutes_Gol_Mandante", "Chutes_Gol_Visitante")}
        for label, (cm, cv) in mapa.items():
            st.subheader(label)
            ca, cb = st.columns(2)
            with ca: st.dataframe(calcular_stats_completas(df_m_h[cm], df_m_h[cv]).style.format("{:.2f}"), use_container_width=True)
            with cb: st.dataframe(calcular_stats_completas(df_v_a[cv], df_v_a[cm]).style.format("{:.2f}"), use_container_width=True)

    with t4:
        for time, df_j, mando in [(m_sel, df_m_h, "Mandante"), (v_sel, df_v_a, "Visitante")]:
            st.write(f"**{time}**")
            adv = "Visitante" if mando == "Mandante" else "Mandante"
            cols_f = [f"0-15_{mando}", f"16-30_{mando}", f"31-45+_{mando}", f"46-60_{mando}", f"61-75_{mando}", f"76-90+_{mando}"]
            cols_s = [f"0-15_{adv}", f"16-30_{adv}", f"31-45+_{adv}", f"46-60_{adv}", f"61-75_{adv}", f"76-90+_{adv}"]
            df_min = pd.DataFrame([df_j[cols_f].sum().values, df_j[cols_s].sum().values], columns=["0-15","16-30","31-45","46-60","61-75","76-90"], index=["Marcados", "Sofridos"])
            st.dataframe(df_min, use_container_width=True)

    st.divider()
    st.subheader("🎯 Frequência de Mercados")
    cp1, cp2 = st.columns(2)
    with cp1: st.dataframe(calcular_probabilidades_mercado(df_m_h).style.format({"% Batido": "{:.1f}%"}).background_gradient(cmap="RdYlGn"), use_container_width=True)
    with cp2: st.dataframe(calcular_probabilidades_mercado(df_v_a).style.format({"% Batido": "{:.1f}%"}).background_gradient(cmap="RdYlGn"), use_container_width=True)
