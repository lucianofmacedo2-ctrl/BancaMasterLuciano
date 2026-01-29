import streamlit as st
import pandas as pd
import numpy as np
import os
import requests
from io import BytesIO

# --- DICIONÁRIO DE REGRAS COMPLETO (Preservado) ---
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
        gm, gv = row.get('Gols_Mandante_FT', 0), row.get('Gols_Visitante_FT', 0)
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
    c_gm, c_gv, c_tg = f'Gols_Mandante_{periodo}', f'Gols_Visitante_{periodo}', f'Total_Gols_{periodo}'
    if c_gm not in temp_df.columns: return pd.DataFrame()
    def perc(cond): return (len(temp_df[cond]) / n) * 100
    mercados = [
        {"Mercado": f"0,5 {periodo}", "% Batido": perc(temp_df[c_tg] >= 0.5)},
        {"Mercado": f"1,5 {periodo}", "% Batido": perc(temp_df[c_tg] >= 1.5)},
        {"Mercado": f"2,5 {periodo}", "% Batido": perc(temp_df[c_tg] >= 2.5)},
        {"Mercado": f"BTTS {periodo}", "% Batido": perc((temp_df[c_gm] > 0) & (temp_df[c_gv] > 0))},
    ]
    return pd.DataFrame(mercados)

def filtrar_por_n(df, n):
    if n == "Todos": return df
    return df.head(int(n))

def mostrar_scout(df):
    st.markdown("<style>.golden-container { border: 2px solid #FFD700; border-radius: 10px; padding: 15px; background-color: rgba(255, 215, 0, 0.05); margin-bottom: 20px;}</style>", unsafe_allow_html=True)
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

    # Médias de Gols Seguras
    gm_m = np.where(df_m['Mandante']==m_sel, df_m.get('Gols_Mandante_FT', 0), df_m.get('Gols_Visitante_FT', 0)).mean()
    gm_v = np.where(df_v['Mandante']==v_sel, df_v.get('Gols_Mandante_FT', 0), df_v.get('Gols_Visitante_FT', 0)).mean()
    
    # Mantendo placeholders para estatísticas que não existem no parquet (Cantos/Chutes)
    ct_m, ct_v = 0.0, 0.0 

    tab_geral = calcular_tabela_classificacao(df_s)
    ci1, ci2 = st.columns(2)
    for col, t_name in zip([ci1, ci2], [m_sel, v_sel]):
        with col:
            pos_list = tab_geral[tab_geral['Time'] == t_name].index.tolist()
            pos = pos_list[0]+1 if pos_list else 0
            st.info(f"**{t_name}** | 🏆 {pos}º Lugar - {get_objetivo_txt(liga_sel, pos)}")

    with st.container(border=True):
        st.subheader("🔥 Médias de Volume")
        render_stat_row("GOLS MARCADOS FT", gm_m, gm_v)
        render_stat_row("ESCANTEIOS (S/ Dados)", ct_m, ct_v)

    t1, t2, t3, t4 = st.tabs(["🕒 Forma", "⚔️ H2H", "📊 Detalhes", "⏰ Minutos"])
    
    with t1:
        cf1, cf2 = st.columns(2)
        for col, t_name, d_h in zip([cf1, cf2], [m_sel, v_sel], [df_m, df_v]):
            with col:
                st.write(f"**Últimos de {t_name}**")
                for _, r in d_h.iterrows():
                    eh_m = (r['Mandante'] == t_name)
                    gm_r, gv_r = r.get('Gols_Mandante_FT', 0), r.get('Gols_Visitante_FT', 0)
                    res = "✅" if (eh_m and gm_r > gv_r) or (not eh_m and gv_r > gm_r) else ("🟧" if gm_r == gv_r else "❌")
                    st.write(f"{res} {r['Data'].strftime('%d/%m')} vs {r['Visitante'] if eh_m else r['Mandante']} ({int(gm_r)}x{int(gv_r)})")

    with t2:
        df_h2h = df[((df['Mandante'] == m_sel) & (df['Visitante'] == v_sel)) | ((df['Mandante'] == v_sel) & (df['Visitante'] == m_sel))].sort_values('Data', ascending=False).head(10)
        st.dataframe(df_h2h[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], use_container_width=True, hide_index=True)

    with t3:
        st.write("**Gols FT**")
        ca, cb = st.columns(2)
        with ca: st.dataframe(calcular_stats_completas(df_m.get('Gols_Mandante_FT', 0), df_m.get('Gols_Visitante_FT', 0)), use_container_width=True)
        with cb: st.dataframe(calcular_stats_completas(df_v.get('Gols_Visitante_FT', 0), df_v.get('Gols_Mandante_FT', 0)), use_container_width=True)

    with t4:
        st.warning("Dados de minutos de gol não disponíveis neste arquivo.")

    st.divider()
    st.subheader("🎯 Frequência de Mercados")
    for p in ['HT', 'FT']:
        st.write(f"### Mercados {p}")
        cp1, cp2 = st.columns(2)
        with cp1: st.dataframe(calcular_probabilidades_mercado(df_m, p), use_container_width=True, hide_index=True)
        with cp2: st.dataframe(calcular_probabilidades_mercado(df_v, p), use_container_width=True, hide_index=True)

# --- CARREGAMENTO DE DADOS (CORRIGIDO PARA O SEU LINK) ---
@st.cache_data(ttl=600)
def carregar_dados():
    # Caminho exato que funcionará no seu GitHub
    url_github = "https://github.com/lucianofmacedo2-ctrl/BancaMasterLuciano/raw/main/dados_25_26.parquet"
    
    try:
        # Força o download via requests para garantir que o Streamlit Cloud acesse
        response = requests.get(url_github, timeout=10)
        if response.status_code == 200:
            return pd.read_parquet(BytesIO(response.content))
        else:
            # Se falhar o link, tenta ler o arquivo se ele estiver na mesma pasta
            if os.path.exists("dados_25_26.parquet"):
                return pd.read_parquet("dados_25_26.parquet")
            return f"Erro de Conexão: Status {response.status_code}"
    except Exception as e:
        return f"Erro crítico ao carregar: {e}"

# Execução final
df_principal = carregar_dados()

if isinstance(df_principal, str):
    st.error(df_principal)
    st.info("Dica: Certifique-se de que o arquivo 'dados_25_26.parquet' foi enviado para a raiz do seu repositório no GitHub.")
else:
    mostrar_scout(df_principal)
