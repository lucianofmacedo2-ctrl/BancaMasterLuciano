import streamlit as st
import pandas as pd
import numpy as np
import os
import requests
from io import BytesIO

# --- DICIONÁRIO DE REGRAS COMPLETO ---
REGRAS_LIGAS = {
    "AUSTRALIA 1": {"times": 12, "rodadas": 26, "alvos": {"Playoff Título": [1, 6]}},
    "BRAZIL 1": {"times": 20, "rodadas": 38, "alvos": {"Libertadores": [1, 6], "Rebaixamento": [17, 20]}},
    "ENGLAND 1": {"times": 20, "rodadas": 38, "alvos": {"Champions League": [1, 4], "Rebaixamento": [18, 20]}},
    "ENGLAND 2": {"times": 24, "rodadas": 46, "alvos": {"Acesso": [1, 2], "Playoff": [3, 6]}},
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
    with col1: st.markdown(f"<p style='text-align: right; font-size: 18px; font-weight: bold; margin:0;'>{v_h:.2f}</p>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<p style='text-align: center; font-size: 11px; color: gray; margin:0;'>{label}</p>", unsafe_allow_html=True)
        st.progress(max(0.0, min(1.0, float(p_home))))
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

def mostrar_scout(df):
    st.title("🚀 Scout Profissional - Banca Master")
    
    # Filtros
    ligas = sorted(df['Liga'].unique())
    c1, c2 = st.columns(2)
    liga_sel = c1.selectbox("Liga", ligas)
    temp_sel = c2.selectbox("Temporada", sorted(df[df['Liga'] == liga_sel]['Temporada'].unique(), reverse=True))
    
    df_s = df[(df['Liga'] == liga_sel) & (df['Temporada'] == temp_sel)].copy()
    times = sorted(df_s['Mandante'].unique())
    
    m_sel = st.selectbox("Mandante", times)
    v_sel = st.selectbox("Visitante", [t for t in times if t != m_sel])

    n_jogos = st.radio("Quantidade de Jogos", ["5", "10", "Todos"], index=1, horizontal=True)
    
    def get_form(team):
        res = df_s[(df_s['Mandante'] == team) | (df_s['Visitante'] == team)].sort_values('Data', ascending=False)
        return res if n_jogos == "Todos" else res.head(int(n_jogos))

    df_m = get_form(m_sel)
    df_v = get_form(v_sel)

    # --- MÉTRICAS COM COLUNAS REAIS ---
    st.divider()
    st.subheader("📊 Médias de Desempenho (FT)")
    
    # Gols
    gm_m = np.where(df_m['Mandante']==m_sel, df_m['Gols_Mandante_FT'], df_m['Gols_Visitante_FT']).mean()
    gm_v = np.where(df_v['Mandante']==v_sel, df_v['Gols_Mandante_FT'], df_v['Gols_Visitante_FT']).mean()
    render_stat_row("GOLS MARCADOS", gm_m, gm_v)

    # Cantos (Escanteios)
    ct_m = np.where(df_m['Mandante']==m_sel, df_m.get('Cantos_Mandante_FT', 0), df_m.get('Cantos_Visitante_FT', 0)).mean()
    ct_v = np.where(df_v['Mandante']==v_sel, df_v.get('Cantos_Mandante_FT', 0), df_v.get('Cantos_Visitante_FT', 0)).mean()
    render_stat_row("CANTOS (ESCANTEIOS)", ct_m, ct_v)

    # xG
    xg_m = np.where(df_m['Mandante']==m_sel, df_m.get('xG_Mandante', 0), df_m.get('xG_Visitante', 0)).mean()
    xg_v = np.where(df_v['Mandante']==v_sel, df_v.get('xG_Mandante', 0), df_v.get('xG_Visitante', 0)).mean()
    render_stat_row("EXPECTED GOALS (xG)", xg_m, xg_v)

    # Cartões
    ca_m = np.where(df_m['Mandante']==m_sel, df_m.get('Cartao_Amarelo_Mandante', 0), df_m.get('Cartao_Amarelo_Visitante', 0)).mean()
    ca_v = np.where(df_v['Mandante']==v_sel, df_v.get('Cartao_Amarelo_Mandante', 0), df_v.get('Cartao_Amarelo_Visitante', 0)).mean()
    render_stat_row("CARTÕES AMARELOS", ca_m, ca_v)

    # Abas
    t1, t2, t3 = st.tabs(["🕒 Últimos Jogos", "⚔️ H2H", "🎯 Mercados"])
    with t1:
        col1, col2 = st.columns(2)
        col1.write(f"Histórico {m_sel}")
        col1.dataframe(df_m[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], hide_index=True)
        col2.write(f"Histórico {v_sel}")
        col2.dataframe(df_v[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], hide_index=True)

# --- CARREGAMENTO DO ARQUIVO (SISTEMA DE SEGURANÇA) ---
@st.cache_data(ttl=300)
def carregar_dados():
    # URL RAW Direta do GitHub
    url = "https://github.com/lucianofmacedo2-ctrl/BancaMasterLuciano/raw/main/dados_25_26.csv"
    
    # Tentativa 1: Download Direto
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            return pd.read_csv(BytesIO(response.content))
    except:
        pass

    # Tentativa 2: Ler da pasta raiz (Streamlit Cloud)
    caminhos_possiveis = ["dados_25_26.csv", "views/dados_25_26.csv", "../dados_25_26.csv"]
    for caminho in caminhos_possiveis:
        if os.path.exists(caminho):
            return pd.read_csv(caminho)
    
    return None

# Execução
df_principal = carregar_dados()

if df_principal is not None:
    mostrar_scout(df_principal)
else:
    st.error("❌ ERRO: O ficheiro 'dados_25_26.csv' não foi encontrado.")
    st.info("O sistema tentou baixar do GitHub e procurar nas pastas locais, mas falhou.")
    
    # Fallback: Upload Manual para o utilizador não ficar parado
    uploaded = st.sidebar.file_uploader("Faça upload do arquivo .csv manualmente aqui:", type="csv")
    if uploaded:
        df_manual = pd.read_csv(uploaded)
        mostrar_scout(df_manual)

