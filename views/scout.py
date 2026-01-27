import streamlit as st
import pandas as pd
import numpy as np
import ast

# --- DICIONÁRIO DE REGRAS ---
REGRAS_LIGAS = {
    "AUSTRALIA 1": {"times": 12, "rodadas": 26, "alvos": {"Playoff Título": [1, 6]}},
    "AUSTRIA 1": {"times": 12, "rodadas": 22, "alvos": {"Champions League": [1, 1], "Europa League": [2, 2], "Conference League": [3, 3], "Rebaixamento": [12, 12]}},
    "BELGIUM 1": {"times": 16, "rodadas": 30, "alvos": {"Champions League": [1, 1], "Europa League": [2, 2], "Conference League": [3, 3], "Rebaixamento": [15, 16]}},
    "BRAZIL 1": {"times": 20, "rodadas": 38, "alvos": {"Libertadores": [1, 6], "Pré-Libertadores": [7, 8], "Sul-Americana": [9, 14], "Rebaixamento": [17, 20]}},
    "BRAZIL 2": {"times": 20, "rodadas": 38, "alvos": {"Acesso": [1, 4], "Rebaixamento": [17, 20]}},
    "BRAZIL 3": {"times": 20, "rodadas": 38, "alvos": {"Acesso": [1, 4], "Rebaixamento": [17, 20]}},
    "CHILE 1": {"times": 16, "rodadas": 30, "alvos": {"Libertadores": [1, 3], "Sul-Americana": [4, 7], "Rebaixamento": [15, 16]}},
    "CHINA 1": {"times": 16, "rodadas": 30, "alvos": {"Champions Asia": [1, 3], "Rebaixamento": [15, 16]}},
    "COPA LIBERTADORES": {"times": 32, "rodadas": 6, "alvos": {"Oitavas de Final": [1, 2]}},
    "CROATIA 1": {"times": 10, "rodadas": 36, "alvos": {"Champions League": [1, 1], "Conference League": [2, 2], "Rebaixamento": [9, 10]}},
    "CZECH 1": {"times": 16, "rodadas": 30, "alvos": {"Champions League": [1, 1], "Europa League": [2, 2], "Conference League": [3, 3], "Rebaixamento": [15, 16]}},
    "DENMARK 1": {"times": 12, "rodadas": 22, "alvos": {"Champions League": [1, 1], "Europa League": [2, 2], "Conference League": [3, 3], "Rebaixamento": [11, 12]}},
    "EGYPT 1": {"times": 18, "rodadas": 34, "alvos": {"Champions Africa": [1, 2], "Rebaixamento": [16, 18]}},
    "ENGLAND 1": {"times": 20, "rodadas": 38, "alvos": {"Champions League": [1, 4], "Europa League": [5, 5], "Conference League": [6, 6], "Rebaixamento": [18, 20]}},
    "ENGLAND 2": {"times": 24, "rodadas": 46, "alvos": {"Acesso": [1, 2], "Playoff Acesso": [3, 6], "Rebaixamento": [22, 24]}},
    "ENGLAND 3": {"times": 24, "rodadas": 46, "alvos": {"Acesso": [1, 2], "Playoff Acesso": [3, 6], "Rebaixamento": [21, 24]}},
    "ENGLAND 4": {"times": 24, "rodadas": 46, "alvos": {"Acesso": [1, 3], "Playoff Acesso": [4, 7], "Rebaixamento": [23, 24]}},
    "EUROPA CHAMPIONS LEAGUE": {"times": 32, "rodadas": 6, "alvos": {"Oitavas de Final": [1, 2]}},
    "FRANCE 1": {"times": 18, "rodadas": 34, "alvos": {"Champions League": [1, 3], "Europa League": [4, 4], "Conference League": [5, 5], "Rebaixamento": [17, 18]}},
    "FRANCE 2": {"times": 20, "rodadas": 38, "alvos": {"Acesso": [1, 2], "Playoff Acesso": [3, 5], "Rebaixamento": [18, 20]}},
    "FRANCE 3": {"times": 18, "rodadas": 34, "alvos": {"Acesso": [1, 1], "Rebaixamento": [15, 18]}},
    "GERMANY 1": {"times": 18, "rodadas": 34, "alvos": {"Champions League": [1, 4], "Europa League": [5, 5], "Conference League": [6, 6], "Rebaixamento": [17, 18]}},
    "GERMANY 2": {"times": 18, "rodadas": 34, "alvos": {"Acesso": [1, 2], "Playoff Permanência": [16, 16], "Rebaixamento": [17, 18]}},
    "GERMANY 3": {"times": 20, "rodadas": 38, "alvos": {"Acesso": [1, 2], "Playoff Acesso": [3, 3], "Rebaixamento": [17, 20]}},
    "GREECE 1": {"times": 14, "rodadas": 26, "alvos": {"Champions League": [1, 1], "Conference League": [2, 2], "Rebaixamento": [13, 14]}},
    "ISRAEL 1": {"times": 14, "rodadas": 26, "alvos": {"Champions League": [1, 1], "Conference League": [2, 2], "Rebaixamento": [13, 14]}},
    "ITALY 1": {"times": 20, "rodadas": 38, "alvos": {"Champions League": [1, 4], "Europa League": [5, 5], "Conference League": [6, 6], "Rebaixamento": [18, 20]}},
    "ITALY 2": {"times": 20, "rodadas": 38, "alvos": {"Acesso": [1, 2], "Playoff Acesso": [3, 8], "Rebaixamento": [18, 20]}},
    "JAPAN 1": {"times": 20, "rodadas": 38, "alvos": {"Champions Asia": [1, 3], "Rebaixamento": [18, 20]}},
    "JAPAN 2": {"times": 22, "rodadas": 42, "alvos": {"Acesso": [1, 2], "Playoff Acesso": [3, 6], "Rebaixamento": [21, 22]}},
    "NETHERLANDS 1": {"times": 18, "rodadas": 34, "alvos": {"Champions League": [1, 2], "Europa League": [3, 3], "Conference League": [4, 4], "Rebaixamento": [17, 18]}},
    "NETHERLANDS 2": {"times": 20, "rodadas": 38, "alvos": {"Acesso": [1, 1], "Playoff Acesso": [2, 8], "Rebaixamento": [19, 20]}},
    "NORWAY 1": {"times": 16, "rodadas": 30, "alvos": {"Champions League": [1, 1], "Conference League": [2, 2], "Rebaixamento": [15, 16]}},
    "POLAND 1": {"times": 18, "rodadas": 34, "alvos": {"Champions League": [1, 1], "Conference League": [2, 2], "Rebaixamento": [16, 18]}},
    "PORTUGAL 1": {"times": 18, "rodadas": 34, "alvos": {"Champions League": [1, 2], "Europa League": [3, 3], "Conference League": [4, 4], "Rebaixamento": [17, 18]}},
    "PORTUGAL 2": {"times": 18, "rodadas": 34, "alvos": {"Acesso": [1, 2], "Rebaixamento": [17, 18]}},
    "ROMANIA 1": {"times": 16, "rodadas": 30, "alvos": {"Champions League": [1, 1], "Conference League": [2, 2], "Rebaixamento": [15, 16]}},
    "SAUDI ARABIA 1": {"times": 18, "rodadas": 34, "alvos": {"Champions Asia": [1, 3], "Rebaixamento": [16, 18]}},
    "SCOTLAND 1": {"times": 12, "rodadas": 38, "alvos": {"Champions League": [1, 1], "Europa League": [2, 2], "Conference League": [3, 3], "Rebaixamento": [12, 12]}},
    "SERBIA 1": {"times": 16, "rodadas": 30, "alvos": {"Champions League": [1, 1], "Conference League": [2, 2], "Rebaixamento": [15, 16]}},
    "SLOVAKIA 1": {"times": 12, "rodadas": 22, "alvos": {"Champions League": [1, 1], "Conference League": [2, 2], "Rebaixamento": [11, 12]}},
    "SLOVENIA 1": {"times": 10, "rodadas": 36, "alvos": {"Champions League": [1, 1], "Conference League": [2, 2], "Rebaixamento": [9, 10]}},
    "SOUTH AFRICA 1": {"times": 16, "rodadas": 30, "alvos": {"Champions Africa": [1, 2], "Rebaixamento": [15, 16]}},
    "SOUTH KOREA 1": {"times": 12, "rodadas": 38, "alvos": {"Champions Asia": [1, 3], "Rebaixamento": [11, 12]}},
    "SOUTH KOREA 2": {"times": 14, "rodadas": 39, "alvos": {"Acesso": [1, 1], "Playoff Acesso": [2, 5]}},
    "SPAIN 1": {"times": 20, "rodadas": 38, "alvos": {"Champions League": [1, 4], "Europa League": [5, 6], "Conference League": [7, 7], "Rebaixamento": [18, 20]}},
    "SPAIN 2": {"times": 22, "rodadas": 42, "alvos": {"Acesso": [1, 2], "Playoff Acesso": [3, 6], "Rebaixamento": [19, 22]}},
    "SWEDEN 1": {"times": 16, "rodadas": 30, "alvos": {"Champions League": [1, 1], "Conference League": [2, 2], "Rebaixamento": [15, 16]}},
    "SWITZERLAND 1": {"times": 12, "rodadas": 38, "alvos": {"Champions League": [1, 1], "Europa League": [2, 2], "Conference League": [3, 3], "Rebaixamento": [11, 12]}},
    "USA 1": {"times": 29, "rodadas": 34, "alvos": {"Playoffs": [1, 9]}},
}

def get_objetivo_txt(liga, pos):
    liga_clean = str(liga).upper().strip()
    if liga_clean not in REGRAS_LIGAS: return "⚪ S/ Info"
    regras = REGRAS_LIGAS[liga_clean]["alvos"]
    for obj, faixa in regras.items():
        if faixa[0] <= pos <= faixa[1]:
            emoji = "🔴" if "Rebaixamento" in obj else "🟢"
            return f"{emoji} {obj}"
    return "⚪ Meio de Tabela"

def render_stat_row(label, val_home, val_away):
    col1, col2, col3 = st.columns([1, 2, 1])
    v_h = float(val_home) if pd.notnull(val_home) else 0.0
    v_a = float(val_away) if pd.notnull(val_away) else 0.0
    total = v_h + v_a
    p_home = (v_h / total) if total > 0 else 0.5
    
    with col1: st.markdown(f"<p style='text-align: right; font-size: 18px; font-weight: bold; margin:0;'>{v_h:.2f}</p>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<p style='text-align: center; font-size: 11px; color: gray; margin:0;'>{label}</p>", unsafe_allow_html=True)
        st.progress(p_home)
    with col3: st.markdown(f"<p style='text-align: left; font-size: 18px; font-weight: bold; margin:0;'>{v_a:.2f}</p>", unsafe_allow_html=True)

def calcular_tabela_classificacao(df_liga):
    stats = {}
    if df_liga.empty: return pd.DataFrame()
    for _, row in df_liga.iterrows():
        m, v = row['Mandante'], row['Visitante']
        gm, gv = row['Gols_Mandante_FT'], row['Gols_Visitante_FT']
        for t in [m, v]:
            if t not in stats: stats[t] = {'P':0, 'J':0, 'V':0, 'E':0, 'D':0, 'GP':0, 'GC':0}
        stats[m]['J'] += 1; stats[v]['J'] += 1
        stats[m]['GP'] += gm; stats[m]['GC'] += gv
        stats[v]['GP'] += gv; stats[v]['GC'] += gm
        if gm > gv: stats[m]['P'] += 3; stats[m]['V'] += 1
        elif gm == gv: stats[m]['P'] += 1; stats[v]['P'] += 1
        else: stats[v]['P'] += 3; stats[v]['V'] += 1
    df_tab = pd.DataFrame.from_dict(stats, orient='index').reset_index().rename(columns={'index': 'Time'})
    df_tab['SG'] = df_tab['GP'] - df_tab['GC']
    return df_tab.sort_values(by=['P', 'V', 'SG'], ascending=False).reset_index(drop=True)

def calcular_stats_completas(serie_f, serie_s):
    def get_metrics(s):
        s = pd.to_numeric(s, errors='coerce').fillna(0)
        m = s.mean(); dp = s.std() if len(s) > 1 else 0.0
        cv = (dp / m * 100) if m > 0 else 0.0
        return {"Média": m, "DP": dp, "CV%": cv}
    
    return pd.DataFrame({
        "Marcados": get_metrics(serie_f), 
        "Sofridos": get_metrics(serie_s), 
        "Saldo": get_metrics(serie_f - serie_s),
        "Total Jogo": get_metrics(serie_f + serie_s)
    }).T

def calcular_probabilidades_mercado(df):
    if df.empty: return pd.DataFrame()
    n = len(df); tg_ht, tg_ft = df['Total_Gols_HT'], df['Total_Gols_FT']
    tg_st = tg_ft - tg_ht; gm_ht, gv_ht = df['Gols_Mandante_HT'], df['Gols_Visitante_HT']
    def perc(cond): return (len(df[cond]) / n) * 100
    mercados = []
    for pref, stot, sm, sv in [("HT", tg_ht, gm_ht, gv_ht), ("ST", tg_st, (df['Gols_Mandante_FT']-gm_ht), (df['Gols_Visitante_FT']-gv_ht)), ("FT", tg_ft, df['Gols_Mandante_FT'], df['Gols_Visitante_FT'])]:
        for g in [0.5, 1.5, 2.5, 3.5]: mercados.append({"Mercado": f"{g} {pref}", "% Batido": perc(stot >= g)})
        mercados.append({"Mercado": f"BTTS {pref}", "% Batido": perc((sm > 0) & (sv > 0))})
    return pd.DataFrame(mercados)

def mostrar_scout(df):
    st.markdown("""
    <style>
        div[data-testid="stDataFrame"] td { text-align: center !important; }
        [data-testid="stMetricValue"] { text-align: center !important; color: #000000 !important; font-weight: 800 !important; width: 100%; }
        [data-testid="stMetricLabel"] { text-align: center !important; width: 100%; }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🚀 Scout Profissional")

    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')

    l_v = st.session_state.get('liga_scout', None)
    t_m_v = st.session_state.get('time_casa_scout', None)
    t_v_v = st.session_state.get('time_fora_scout', None)

    ligas_list = sorted(df['Liga'].unique())
    idx_l = ligas_list.index(l_v) if l_v in ligas_list else 0
    
    c1, c2 = st.columns(2)
    liga_sel = c1.selectbox("Selecione a Liga", ligas_list, index=idx_l)
    df_l = df[df['Liga'] == liga_sel].copy()
    temp_sel = c2.selectbox("Temporada", sorted(df_l['Temporada'].unique(), reverse=True))
    
    df_s = df_l[df_l['Temporada'] == temp_sel].copy()
    times_liga = sorted(df_s['Mandante'].unique())
    
    idx_m = times_liga.index(t_m_v) if t_m_v in times_liga else 0
    c3, c4 = st.columns(2)
    m_sel = c3.selectbox("Mandante (Casa)", times_liga, index=idx_m)
    opcoes_v = [t for t in times_liga if t != m_sel]
    idx_v = opcoes_v.index(t_v_v) if t_v_v in opcoes_v else 0
    v_sel = c4.selectbox("Visitante (Fora)", opcoes_v, index=idx_v)

    tab_geral = calcular_tabela_classificacao(df_s)
    
    st.markdown("---")
    df_m_h = df_s[df_s['Mandante'] == m_sel].sort_values('Data', ascending=False).head(10)
    df_v_a = df_s[df_s['Visitante'] == v_sel].sort_values('Data', ascending=False).head(10)

    if not df_m_h.empty and not df_v_a.empty:
        col_i1, col_i2 = st.columns(2)
        for col, t_name, df_hist, mando in zip([col_i1, col_i2], [m_sel, v_sel], [df_m_h, df_v_a], ["Casa", "Fora"]):
            with col:
                pos_row = tab_geral[tab_geral['Time'] == t_name] if not tab_geral.empty else pd.DataFrame()
                if not pos_row.empty:
                    pos = pos_row.index[0] + 1
                    obj = get_objetivo_txt(liga_sel, pos)
                    
                    if mando == "Casa":
                        cs = (df_hist['Gols_Visitante_FT'] == 0).sum()
                        fsm = (df_hist['Gols_Mandante_FT'] == 0).sum()
                        ch_media = df_hist['Chutes_Gol_Mandante'].mean()
                    else:
                        cs = (df_hist['Gols_Mandante_FT'] == 0).sum()
                        fsm = (df_hist['Gols_Visitante_FT'] == 0).sum()
                        ch_media = df_hist['Chutes_Gol_Visitante'].mean()

                    st.info(f"**{t_name}** ({mando})\n\n🏆 {pos}º Lugar | 🎯 {obj}")
                    k1, k2, k3 = st.columns(3)
                    k1.metric("Clean Sheets", int(cs))
                    k2.metric("F.S.M", int(fsm))
                    k3.metric("Chutes/G", f"{ch_media:.1f}")

    st.divider()
    
    # VOLUME (FT)
    with st.container(border=True):
        st.subheader("🔥 Médias de Volume")
        render_stat_row("GOLS MARCADOS FT", df_m_h['Gols_Mandante_FT'].mean(), df_v_a['Gols_Visitante_FT'].mean())
        render_stat_row("CHUTES AO GOL", df_m_h['Chutes_Gol_Mandante'].mean(), df_v_a['Chutes_Gol_Visitante'].mean())
        render_stat_row("ESCANTEIOS PRO", df_m_h['Cantos_Mandante'].mean(), df_v_a['Cantos_Visitante'].mean())

    # MÉTRICAS AVANÇADAS COM EXPLICAÇÃO
    with st.container(border=True):
        c_title, c_help = st.columns([0.8, 0.2])
        c_title.subheader("🎯 Eficiência e Dominância")
        
        # O Ícone de interrogação com o texto explicativo
        c_help.markdown("### ℹ️")
        c_help.help("""
        **COMO INTERPRETAR:**
        
        1. **Chutes p/ 1 Canto:** Indica quantos chutes o time precisa dar para gerar 1 escanteio. 
           - *Quanto MENOR o número, mais eficiente é a pressão do time.*
        
        2. **Saldo Médio de Cantos:** É a diferença entre Cantos Pró e Cantos Contra.
           - *Saldo Positivo (+):* O time domina e sufoca o adversário.
           - *Saldo Negativo (-):* O time é dominado e cede muita pressão.
        """)
        
        # Cálculos
        ef_m = df_m_h['Finalizações_Totais_Mandante'].sum() / df_m_h['Cantos_Mandante'].sum() if df_m_h['Cantos_Mandante'].sum() > 0 else 0
        ef_v = df_v_a['Finalizações_Totais_Visitante'].sum() / df_v_a['Cantos_Visitante'].sum() if df_v_a['Cantos_Visitante'].sum() > 0 else 0
        render_stat_row("CHUTES TOTAIS P/ 1 CANTO", ef_m, ef_v)
        
        saldo_m = df_m_h['Cantos_Mandante'].mean() - df_m_h['Cantos_Visitante'].mean()
        saldo_v = df_v_a['Cantos_Visitante'].mean() - df_v_a['Cantos_Mandante'].mean()
        render_stat_row("SALDO MÉDIO DE CANTOS", saldo_m, saldo_v)

    t1, t2, t3, t4 = st.tabs(["🕒 Forma Recente", "⚔️ H2H", "📊 Stats Detalhadas", "⏰ Minutos"])
    
    # ... (Restante do código permanece o mesmo para garantir funcionalidade) ...
    with t1:
        cf1, cf2 = st.columns(2)
        for col_f, t_name, df_h, eh_mandante in zip([cf1, cf2], [m_sel, v_sel], [df_m_h, df_v_a], [True, False]):
            with col_f:
                st.markdown(f"**{t_name}**")
                for _, r in df_h.iterrows():
                    res = "✅" if (eh_mandante and r['Gols_Mandante_FT'] > r['Gols_Visitante_FT']) or (not eh_mandante and r['Gols_Visitante_FT'] > r['Gols_Mandante_FT']) else ("🟧" if r['Gols_Mandante_FT'] == r['Gols_Visitante_FT'] else "❌")
                    data_str = r['Data'].strftime('%d/%m') if pd.notnull(r['Data']) else "S/D"
                    st.write(f"{res} {data_str} vs {r['Visitante'] if eh_mandante else r['Mandante']} ({int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])})")
    
    with t2:
        h2h = df_s[((df_s['Mandante'] == m_sel) & (df_s['Visitante'] == v_sel)) | ((df_s['Mandante'] == v_sel) & (df_s['Visitante'] == m_sel))].sort_values('Data', ascending=False).head(10)
        if not h2h.empty:
            h2h_view = h2h[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']].copy()
            h2h_view['Data'] = h2h_view['Data'].dt.strftime('%d/%m/%Y')
            st.dataframe(h2h_view, use_container_width=True, hide_index=True)
    
    with t3:
        for label, (cm, cv) in {"Gols HT": ("Gols_Mandante_HT", "Gols_Visitante_HT"), "Gols FT": ("Gols_Mandante_FT", "Gols_Visitante_FT"), "Cantos": ("Cantos_Mandante", "Cantos_Visitante")}.items():
            st.subheader(label); ca, cb = st.columns(2)
            with ca: st.dataframe(calcular_stats_completas(df_m_h[cm], df_m_h[cv]).style.format("{:.2f}"), use_container_width=True)
            with cb: st.dataframe(calcular_stats_completas(df_v_a[cv], df_v_a[cm]).style.format("{:.2f}"), use_container_width=True)
    
    with t4:
        for t_n, df_j, mando in [(m_sel, df_m_h, "Mandante"), (v_sel, df_v_a, "Visitante")]:
            st.write(f"**{t_n}**"); adv = "Visitante" if mando == "Mandante" else "Mandante"
            cols_f = [f"{c}_{mando}" for c in ["0-15", "16-30", "31-45+", "46-60", "61-75", "76-90+"]]
            cols_s = [f"{c}_{adv}" for c in ["0-15", "16-30", "31-45+", "46-60", "61-75", "76-90+"]]
            cols_f_exist = [c for c in cols_f if c in df_j.columns]
            cols_s_exist = [c for c in cols_s if c in df_j.columns]
            if cols_f_exist:
                st.dataframe(pd.DataFrame([df_j[cols_f_exist].sum().values, df_j[cols_s_exist].sum().values], columns=["0-15","16-30","31-45","46-60","61-75","76-90"][:len(cols_f_exist)], index=["Marcados", "Sofridos"]), use_container_width=True)

    st.divider(); st.subheader("🎯 Frequência de Mercados")
    cp1, cp2 = st.columns(2)
    with cp1: st.dataframe(calcular_probabilidades_mercado(df_m_h).style.format({"% Batido": "{:.1f}%"}).background_gradient(cmap="RdYlGn"), use_container_width=True)
    with cp2: st.dataframe(calcular_probabilidades_mercado(df_v_a).style.format({"% Batido": "{:.1f}%"}).background_gradient(cmap="RdYlGn"), use_container_width=True)
