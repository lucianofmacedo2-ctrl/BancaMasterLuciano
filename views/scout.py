import streamlit as st
import pandas as pd
import numpy as np
import os
import requests
from io import BytesIO

# --- DICIONÁRIO DE REGRAS COMPLETO ---
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
    "FRANCE 1": {"times": 18, "rodadas": 34, "alvos": {"Champions League": [1, 3], "Europa League": [4, 4], "Conference League": [5, 5], "Rebaixamento": [17, 18]}},
    "FRANCE 2": {"times": 20, "rodadas": 38, "alvos": {"Acesso": [1, 2], "Playoff Acesso": [3, 5], "Rebaixamento": [18, 20]}},
    "GERMANY 1": {"times": 18, "rodadas": 34, "alvos": {"Champions League": [1, 4], "Europa League": [5, 5], "Conference League": [6, 6], "Rebaixamento": [17, 18]}},
    "ITALY 1": {"times": 20, "rodadas": 38, "alvos": {"Champions League": [1, 4], "Europa League": [5, 5], "Conference League": [6, 6], "Rebaixamento": [18, 20]}},
    "SPAIN 1": {"times": 20, "rodadas": 38, "alvos": {"Champions League": [1, 4], "Europa League": [5, 6], "Conference League": [7, 7], "Rebaixamento": [18, 20]}},
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
    if label == "SALDO MÉDIO DE CANTOS":
        diff = v_h - v_a
        p_home = 0.5 + (diff / 12.0)
    else:
        total = abs(v_h) + abs(v_a)
        p_home = (v_h / total) if total > 0 else 0.5
    p_home = max(0.0, min(1.0, float(p_home)))
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
        s = pd.to_numeric(pd.Series(s), errors='coerce').fillna(0)
        m = s.mean(); dp = s.std() if len(s) > 1 else 0.0
        cv = (dp / m * 100) if m > 0 else 0.0
        return {"Média": m, "DP": dp, "CV%": cv}
    s_f = pd.to_numeric(pd.Series(serie_f), errors='coerce').fillna(0)
    s_s = pd.to_numeric(pd.Series(serie_s), errors='coerce').fillna(0)
    return pd.DataFrame({
        "Marcados": get_metrics(s_f), 
        "Sofridos": get_metrics(s_s), 
        "Saldo": get_metrics(s_f - s_s), 
        "Total Jogo": get_metrics(s_f + s_s)
    }).T

def calcular_probabilidades_mercado(df, periodo='FT'):
    if df.empty: return pd.DataFrame()
    n = len(df)
    temp_df = df.copy()
    if periodo == 'ST':
        c_gm, c_gv = 'Gols_Mandante_ST_Calc', 'Gols_Visitante_ST_Calc'
        temp_df[c_gm] = temp_df['Gols_Mandante_FT'] - temp_df['Gols_Mandante_HT']
        temp_df[c_gv] = temp_df['Gols_Visitante_FT'] - temp_df['Gols_Visitante_HT']
        temp_df['Total_Gols_ST_Calc'] = temp_df[c_gm] + temp_df[c_gv]
        c_tg = 'Total_Gols_ST_Calc'
    else:
        c_gm, c_gv, c_tg = f'Gols_Mandante_{periodo}', f'Gols_Visitante_{periodo}', f'Total_Gols_{periodo}'
    
    if c_gm not in temp_df.columns: return pd.DataFrame()
    def perc(cond): return (len(temp_df[cond]) / n) * 100
    mercados = [
        {"Mercado": f"0,5 {periodo}", "% Batido": perc(temp_df[c_tg] >= 0.5)},
        {"Mercado": f"1,5 {periodo}", "% Batido": perc(temp_df[c_tg] >= 1.5)},
        {"Mercado": f"2,5 {periodo}", "% Batido": perc(temp_df[c_tg] >= 2.5)},
        {"Mercado": f"3,5 {periodo}", "% Batido": perc(temp_df[c_tg] >= 3.5)},
        {"Mercado": f"BTTS {periodo}", "% Batido": perc((temp_df[c_gm] > 0) & (temp_df[c_gv] > 0))},
    ]
    return pd.DataFrame(mercados)

def filtrar_por_n(df, n):
    if n == "Todos": return df
    return df.head(int(n))

def mostrar_scout(df):
    st.markdown("<style>.golden-container { border: 2px solid #FFD700; border-radius: 10px; padding: 15px; background-color: rgba(255, 215, 0, 0.05); margin-bottom: 20px;} [data-testid='stMetricValue'] { text-align: center !important; font-weight: 800 !important; }</style>", unsafe_allow_html=True)
    st.title("🚀 Scout Profissional")

    df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
    ligas_list = sorted(df['Liga'].unique())
    c1, c2 = st.columns(2)
    liga_sel = c1.selectbox("Selecione a Liga", ligas_list)
    temp_sel = c2.selectbox("Temporada", sorted(df[df['Liga'] == liga_sel]['Temporada'].unique(), reverse=True))
    
    df_s = df[(df['Liga'] == liga_sel) & (df['Temporada'] == temp_sel)].copy()
    times_liga = sorted(df_s['Mandante'].unique())
    
    c3, c4 = st.columns(2)
    m_sel = c3.selectbox("Time Mandante", times_liga)
    v_sel = c4.selectbox("Time Visitante", [t for t in times_liga if t != m_sel])

    st.divider()
    st.subheader("⚙️ Configurações de Análise")
    col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
    n_jogos = col_cfg1.radio("Quantidade de Jogos", ["5", "10", "Todos"], index=1, horizontal=True)
    criterio_mando = col_cfg2.radio("Critério de Mando", ["Geral", "Mando de Campo"], index=1, horizontal=True)
    criterio_h2h = col_cfg3.radio("Critério H2H", ["Geral", "Mando Específico"], index=0, horizontal=True)

    if criterio_mando == "Geral":
        df_m = df_s[(df_s['Mandante'] == m_sel) | (df_s['Visitante'] == m_sel)].sort_values('Data', ascending=False)
        df_v = df_s[(df_s['Mandante'] == v_sel) | (df_s['Visitante'] == v_sel)].sort_values('Data', ascending=False)
    else:
        df_m = df_s[df_s['Mandante'] == m_sel].sort_values('Data', ascending=False)
        df_v = df_s[df_s['Visitante'] == v_sel].sort_values('Data', ascending=False)

    df_m = filtrar_por_n(df_m, n_jogos)
    df_v = filtrar_por_n(df_v, n_jogos)

    if criterio_h2h == "Geral":
        df_h2h = df[((df['Mandante'] == m_sel) & (df['Visitante'] == v_sel)) | ((df['Mandante'] == v_sel) & (df['Visitante'] == m_sel))].sort_values('Data', ascending=False)
    else:
        df_h2h = df[(df['Mandante'] == m_sel) & (df['Visitante'] == v_sel)].sort_values('Data', ascending=False)
    df_h2h = filtrar_por_n(df_h2h, n_jogos)

    def get_avg_stats(df_target, t_name):
        is_m = (df_target['Mandante'] == t_name)
        gm = np.where(is_m, df_target['Gols_Mandante_FT'], df_target['Gols_Visitante_FT']).mean()
        ch = np.where(is_m, df_target['Chutes_Gol_Mandante'], df_target['Chutes_Gol_Visitante']).mean()
        ct = np.where(is_m, df_target['Cantos_Mandante'], df_target['Cantos_Visitante']).mean()
        fin = np.where(is_m, df_target['Finalizações_Totais_Mandante'], df_target['Finalizações_Totais_Visitante']).sum()
        ct_t = np.where(is_m, df_target['Cantos_Mandante'], df_target['Cantos_Visitante']).sum()
        ef = fin / ct_t if ct_t > 0 else 0
        sd = np.where(is_m, df_target['Cantos_Mandante'] - df_target['Cantos_Visitante'], df_target['Cantos_Visitante'] - df_target['Cantos_Mandante']).mean()
        return gm, ch, ct, ef, sd

    gm_m, ch_m, ct_m, ef_m, sd_m = get_avg_stats(df_m, m_sel)
    gm_v, ch_v, ct_v, ef_v, sd_v = get_avg_stats(df_v, v_sel)

    tab_geral = calcular_tabela_classificacao(df_s)
    ci1, ci2 = st.columns(2)
    for col, t_name in zip([ci1, ci2], [m_sel, v_sel]):
        with col:
            pos = tab_geral[tab_geral['Time'] == t_name].index[0]+1 if t_name in tab_geral['Time'].values else 0
            st.info(f"**{t_name}** | 🏆 {pos}º Lugar - {get_objetivo_txt(liga_sel, pos)}")

    with st.container(border=True):
        st.subheader("🔥 Médias de Volume")
        render_stat_row("GOLS MARCADOS FT", gm_m, gm_v)
        render_stat_row("CHUTES AO GOL", ch_m, ch_v)
        render_stat_row("ESCANTEIOS PRO", ct_m, ct_v)

    is_golden = (ef_m <= 1.5) and (ef_v <= 1.5) and (ef_m > 0) and (ef_v > 0)
    with st.container(border=True):
        st.markdown(f'<div class="{"golden-container" if is_golden else ""}">', unsafe_allow_html=True)
        st.subheader("🎯 Eficiência e Dominância")
        render_stat_row("CHUTES TOTAIS P/ 1 CANTO", ef_m, ef_v)
        render_stat_row("SALDO MÉDIO DE CANTOS", sd_m, sd_v)
        st.markdown('</div>', unsafe_allow_html=True)

    t1, t2, t3, t4 = st.tabs(["🕒 Forma", "⚔️ H2H", "📊 Detalhes", "⏰ Minutos"])
    
    with t1:
        cf1, cf2 = st.columns(2)
        for col, t_name, d_h in zip([cf1, cf2], [m_sel, v_sel], [df_m, df_v]):
            with col:
                st.write(f"**Últimos de {t_name}**")
                for _, r in d_h.iterrows():
                    eh_m = (r['Mandante'] == t_name)
                    res = "✅" if (eh_m and r['Gols_Mandante_FT'] > r['Gols_Visitante_FT']) or (not eh_m and r['Gols_Visitante_FT'] > r['Gols_Mandante_FT']) else ("🟧" if r['Gols_Mandante_FT'] == r['Gols_Visitante_FT'] else "❌")
                    st.write(f"{res} {r['Data'].strftime('%d/%m')} vs {r['Visitante'] if eh_m else r['Mandante']} ({int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])})")

    with t2:
        if not df_h2h.empty:
            h2_v = df_h2h[['Temporada', 'Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']].copy()
            h2_v['Data'] = h2_v['Data'].dt.strftime('%d/%m/%Y')
            st.dataframe(h2_v, use_container_width=True, hide_index=True)

    with t3:
        metrics_list = [
            ("Gols FT", "Gols_Mandante_FT", "Gols_Visitante_FT"),
            ("Gols HT", "Gols_Mandante_HT", "Gols_Visitante_HT"),
            ("Cantos", "Cantos_Mandante", "Cantos_Visitante"),
            ("Chutes no Gol", "Chutes_Gol_Mandante", "Chutes_Gol_Visitante"),
            ("Finalizações", "Finalizações_Totais_Mandante", "Finalizações_Totais_Visitante")
        ]
        for label, cm, cv in metrics_list:
            if cm in df.columns:
                st.write(f"**{label}**")
                ca, cb = st.columns(2)
                ism = df_m['Mandante'] == m_sel
                with ca: st.dataframe(calcular_stats_completas(np.where(ism, df_m[cm], df_m[cv]), np.where(ism, df_m[cv], df_m[cm])).style.format("{:.2f}"), use_container_width=True)
                isv = df_v['Mandante'] == v_sel
                with cb: st.dataframe(calcular_stats_completas(np.where(isv, df_v[cm], df_v[cv]), np.where(isv, df_v[cv], df_v[cm])).style.format("{:.2f}"), use_container_width=True)

    with t4:
        faixas = ["0-15", "16-30", "31-45+", "46-60", "61-75", "76-90+"]
        for t_n, d_j in [(m_sel, df_m), (v_sel, df_v)]:
            st.write(f"**{t_n}**")
            feitos, sofridos = [], []
            for fx in faixas:
                f = np.where(d_j['Mandante'] == t_n, d_j.get(f"{fx}_Mandante", 0), d_j.get(f"{fx}_Visitante", 0)).sum()
                s = np.where(d_j['Mandante'] == t_n, d_j.get(f"{fx}_Visitante", 0), d_j.get(f"{fx}_Mandante", 0)).sum()
                feitos.append(f); sofridos.append(s)
            df_min = pd.DataFrame([feitos, sofridos, np.array(feitos)+np.array(sofridos)], 
                                 columns=["0-15","16-30","31-45","46-60","61-75","76-90"], 
                                 index=["Gols Feitos", "Gols Sofridos", "Total Gols"])
            st.dataframe(df_min.astype(int), use_container_width=True)

    st.divider()
    st.subheader("🎯 Frequência de Mercados")
    for p in ['FT', 'HT', 'ST']:
        st.write(f"### Mercados {p}")
        cp1, cp2 = st.columns(2)
        with cp1:
            st.write(f"**{m_sel}**")
            st.dataframe(calcular_probabilidades_mercado(df_m, p).style.format({"% Batido": "{:.1f}%"}).background_gradient(cmap="RdYlGn", vmin=0, vmax=100), use_container_width=True, hide_index=True)
        with cp2:
            st.write(f"**{v_sel}**")
            st.dataframe(calcular_probabilidades_mercado(df_v, p).style.format({"% Batido": "{:.1f}%"}).background_gradient(cmap="RdYlGn", vmin=0, vmax=100), use_container_width=True, hide_index=True)

# --- CARREGAMENTO DE DADOS COM CACHE ---
@st.cache_data(ttl=3600)  # Cache de 1 hora
def carregar_dados():
    # Tenta local primeiro, se falhar vai para o GitHub
    path_local = "dados_25_26.parquet"
    url_github = "https://github.com/lucianofmacedo2-ctrl/BancaMasterLuciano/raw/main/dados_25_26.parquet"
    
    try:
        if os.path.exists(path_local):
            return pd.read_parquet(path_local)
        else:
            # Baixa do GitHub e lê os bytes
            response = requests.get(url_github)
            return pd.read_parquet(BytesIO(response.content))
    except Exception as e:
        return f"Erro crítico: {e}"

# Execução
df_principal = carregar_dados()

if isinstance(df_principal, str):
    st.error(df_principal)
    st.info("O arquivo 'dados_25_26.parquet' não foi encontrado. Verifique se o nome no GitHub está exatamente igual.")
else:
    mostrar_scout(df_principal)
