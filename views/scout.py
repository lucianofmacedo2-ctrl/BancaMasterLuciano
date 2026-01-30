import streamlit as st
import pandas as pd
import numpy as np
import os
import requests
from io import BytesIO

# --- CONFIGURAÇÃO ---
st.set_page_config(page_title="Scout Banca Master", layout="wide")

# --- DICIONÁRIO DE REGRAS (Preservado) ---
REGRAS_LIGAS = {
    "BRAZIL 1": {"times": 20, "rodadas": 38, "alvos": {"Libertadores": [1, 6], "Rebaixamento": [17, 20]}},
    "ENGLAND 1": {"times": 20, "rodadas": 38, "alvos": {"Champions League": [1, 4], "Rebaixamento": [18, 20]}},
    "PORTUGAL 3": {"times": 20, "rodadas": 26, "alvos": {"Acesso": [1, 2]}},
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

    # --- FORÇAR RECONHECIMENTO TOTAL ---
    # Convertemos tudo para string e limpamos espaços para garantir que Portugal 3 apareça
    df['Liga'] = df['Liga'].astype(str).str.strip()
    
    # Criamos a lista de ligas pegando TODOS os valores únicos presentes na coluna
    todas_ligas = sorted(df['Liga'].unique().tolist())
    
    c1, c2 = st.columns(2)
    liga_sel = c1.selectbox("Selecione a Liga", todas_ligas)
    
    # Filtragem por liga selecionada
    df_liga = df[df['Liga'] == liga_sel].copy()
    
    temps = sorted(df_liga['Temporada'].astype(str).unique().tolist(), reverse=True)
    temp_sel = c2.selectbox("Temporada", temps)
    
    df_s = df_liga[df_liga['Temporada'].astype(str) == temp_sel].copy()
    df_s['Data'] = pd.to_datetime(df_s['Data'], errors='coerce')
    
    times = sorted(df_s['Mandante'].unique().tolist())
    m_sel = st.selectbox("Mandante", times)
    v_sel = st.selectbox("Visitante", [t for t in times if t != m_sel])

    n_jogos = st.radio("Quantidade de Jogos", ["5", "10", "Todos"], index=1, horizontal=True)
    
    def get_form(team):
        res = df_s[(df_s['Mandante'] == team) | (df_s['Visitante'] == team)].sort_values('Data', ascending=False)
        return res if n_jogos == "Todos" else res.head(int(n_jogos))

    df_m = get_form(m_sel)
    df_v = get_form(v_sel)

    st.divider()
    st.subheader("📊 Médias de Desempenho (FT)")
    
    render_stat_row("GOLS MARCADOS", 
                    np.where(df_m['Mandante']==m_sel, df_m['Gols_Mandante_FT'], df_m['Gols_Visitante_FT']).mean(),
                    np.where(df_v['Mandante']==v_sel, df_v['Gols_Mandante_FT'], df_v['Gols_Visitante_FT']).mean())
    
    render_stat_row("CANTOS (ESCANTEIOS)", 
                    np.where(df_m['Mandante']==m_sel, df_m.get('Cantos_Mandante_FT', 0), df_m.get('Cantos_Visitante_FT', 0)).mean(),
                    np.where(df_v['Mandante']==v_sel, df_v.get('Cantos_Mandante_FT', 0), df_v.get('Cantos_Visitante_FT', 0)).mean())

    # --- ABAS ---
    t1, t2, t3, t4 = st.tabs(["🕒 Forma", "⚔️ H2H", "📊 Detalhes", "⏰ Minutos"])
    
    with t1:
        c_a, c_b = st.columns(2)
        c_a.dataframe(df_m[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], hide_index=True)
        c_b.dataframe(df_v[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], hide_index=True)

    with t2:
        h2h = df[((df['Mandante'] == m_sel) & (df['Visitante'] == v_sel)) | ((df['Mandante'] == v_sel) & (df['Visitante'] == m_sel))].sort_values('Data', ascending=False)
        st.dataframe(h2h[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], use_container_width=True, hide_index=True)

    with t3:
        def calc_stats(s1):
            return pd.DataFrame({"Média": [s1.mean()], "Máximo": [s1.max()]}, index=["Gols"])
        st.table(calc_stats(df_m['Gols_Mandante_FT']))

    with t4:
        minutos = ['0-15_Mandante', '16-30_Mandante', '31-45+_Mandante', '46-60_Mandante', '61-75_Mandante', '76-90+_Mandante']
        st.bar_chart(df_m[minutos].mean())

# --- CARREGAMENTO DEFINITIVO ---
@st.cache_data(ttl=2)
def carregar_dados():
    url = "https://github.com/lucianofmacedo2-ctrl/BancaMasterLuciano/raw/main/dados_25_26.csv"
    try:
        # IMPORTANTE: Forçamos as colunas de texto para garantir que as ligas novas sejam lidas
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            return pd.read_csv(BytesIO(response.content), dtype={'Liga': str, 'Temporada': str, 'Mandante': str, 'Visitante': str})
    except:
        pass
    if os.path.exists("dados_25_26.csv"):
        return pd.read_csv("dados_25_26.csv", dtype={'Liga': str, 'Temporada': str})
    return None

# Botão de reset na sidebar
if st.sidebar.button("♻️ Recarregar Ligas do CSV"):
    st.cache_data.clear()
    st.rerun()

df_principal = carregar_dados()

if df_principal is not None:
    mostrar_scout(df_principal)
else:
    st.error("Não foi possível ler o arquivo. Verifique se ele está no GitHub.")
