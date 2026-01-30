import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats as sp_stats

# --- REGRAS DE OBJETIVOS ---
REGRAS_LIGAS = {
    "BRAZIL 1": {"alvos": {"Libertadores": [1, 6], "Sul-Americana": [7, 12], "Rebaixamento": [17, 20]}},
    "BRAZIL 2": {"alvos": {"Acesso": [1, 4], "Rebaixamento": [17, 20]}},
    "PORTUGAL 3": {"alvos": {"Acesso": [1, 2], "Playoff Acesso": [3, 4], "Rebaixamento": [7, 10]}}, # Ajustado p/ grupos menores
    "ENGLAND 1": {"alvos": {"Champions League": [1, 4], "Europa League": [5, 5], "Rebaixamento": [18, 20]}},
}

def get_objetivo_txt(liga, pos):
    liga_clean = str(liga).upper().strip()
    if liga_clean not in REGRAS_LIGAS: return "⚪ Meio"
    regras = REGRAS_LIGAS[liga_clean]["alvos"]
    for obj, faixa in regras.items():
        if faixa[0] <= pos <= faixa[1]:
            return f"{'🔴' if 'Rebaixamento' in obj else '🟢'} {obj}"
    return "⚪ Meio"

def render_stat_row(label, val_h, val_v, total_avg=None):
    col1, col2, col3 = st.columns([1, 2, 1])
    vh, vv = float(val_h or 0), float(val_v or 0)
    total = vh + vv
    perc = vh / total if total > 0 else 0.5
    with col1: st.markdown(f"<p style='text-align:right;font-weight:bold;margin:0;'>{vh:.2f}</p>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<p style='text-align:center;font-size:10px;color:gray;margin:0;'>{label} {'(Total: '+str(round(total_avg,2))+')' if total_avg else ''}</p>", unsafe_allow_html=True)
        st.progress(max(0.0, min(1.0, perc)))
    with col3: st.markdown(f"<p style='text-align:left;font-weight:bold;margin:0;'>{vv:.2f}</p>", unsafe_allow_html=True)

def calcular_estatisticas_avancadas(series):
    if len(series) == 0: return {}
    return {
        "Média": series.mean(),
        "Mediana": series.median(),
        "Moda": series.mode().iloc[0] if not series.mode().empty else series.mean(),
        "Desvio Padrão": series.std(),
        "CV (%)": (series.std() / series.mean() * 100) if series.mean() != 0 else 0,
        "0.5+": (series > 0.5).mean() * 100,
        "1.5+": (series > 1.5).mean() * 100,
        "2.5+": (series > 2.5).mean() * 100,
        "3.5+": (series > 3.5).mean() * 100,
    }

def mostrar_scout(df):
    if df.empty: return st.error("Base vazia")
    
    st.title("🔎 Scout Avançado Profissional")

    # --- FILTROS ---
    df['Liga'] = df['Liga'].astype(str).str.strip().str.upper()
    ligas = sorted(df['Liga'].unique())
    
    col_f1, col_f2, col_f3 = st.columns(3)
    liga_sel = col_f1.selectbox("Liga", ligas)
    df_l = df[df['Liga'] == liga_sel].copy()
    
    temp_sel = col_f2.selectbox("Temporada", sorted(df_l['Temporada'].unique(), reverse=True))
    df_s = df_l[df_l['Temporada'] == temp_sel].copy()
    
    filtro_mando = col_f3.selectbox("Mando de Campo", ["Geral", "Casa/Fora Específico"])

    times = sorted(df_s['Mandante'].unique())
    m_sel = st.selectbox("Mandante", times)
    v_sel = st.selectbox("Visitante", [t for t in times if t != m_sel])

    # --- LÓGICA DE FILTRAGEM DE JOGOS ---
    if filtro_mando == "Geral":
        df_m = df_s[(df_s['Mandante'] == m_sel) | (df_s['Visitante'] == m_sel)].sort_values('Data', ascending=False)
        df_v = df_s[(df_s['Mandante'] == v_sel) | (df_s['Visitante'] == v_sel)].sort_values('Data', ascending=False)
    else:
        df_m = df_s[df_s['Mandante'] == m_sel].sort_values('Data', ascending=False)
        df_v = df_s[df_s['Visitante'] == v_sel].sort_values('Data', ascending=False)

    n_jogos = st.sidebar.slider("Quantidade de jogos", 5, 20, 10)
    df_m = df_m.head(n_jogos)
    df_v = df_v.head(n_jogos)

    # --- BARRAS DE DESEMPENHO EXPANDIDAS ---
    st.subheader("🚀 Power Stats (Médias)")
    
    # Dados de Gols e xG
    render_stat_row("GOLS MARCADOS", 
                   np.where(df_m['Mandante']==m_sel, df_m['Gols_Mandante_FT'], df_m['Gols_Visitante_FT']).mean(),
                   np.where(df_v['Mandante']==v_sel, df_v['Gols_Mandante_FT'], df_v['Gols_Visitante_FT']).mean())
    
    # Dados de Pressão (Aproveitando os novos dados do CSV)
    if 'Attacks_H' in df.columns:
        att_m = np.where(df_m['Mandante']==m_sel, df_m['Attacks_H'], df_m['Attacks_A']).mean()
        att_v = np.where(df_v['Mandante']==v_sel, df_v['Attacks_H'], df_v['Attacks_A']).mean()
        render_stat_row("ATAQUES TOTAIS", att_m, att_v)

        datt_m = np.where(df_m['Mandante']==m_sel, df_m['DangerousAttacks_H'], df_m['DangerousAttacks_A']).mean()
        datt_v = np.where(df_v['Mandante']==v_sel, df_v['DangerousAttacks_H'], df_v['DangerousAttacks_A']).mean()
        render_stat_row("ATAQUES PERIGOSOS", datt_m, datt_v)

    # --- ABAS DETALHADAS ---
    t_forma, t_stats, t_min, t_class = st.tabs(["🕒 Forma", "📊 Stats Profissionais", "⏰ Tabela de Minutos", "🏆 Classificação"])

    with t_forma:
        c1, c2 = st.columns(2)
        c1.write(f"Últimos de {m_sel}")
        c1.dataframe(df_m[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], hide_index=True)
        c2.write(f"Últimos de {v_sel}")
        c2.dataframe(df_v[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], hide_index=True)

    with t_stats:
        st.subheader("Análise Matemática de Gols (FT)")
        def get_metrics(df_team, team, is_home):
            marc = np.where(df_team['Mandante']==team, df_team['Gols_Mandante_FT'], df_team['Gols_Visitante_FT'])
            sofr = np.where(df_team['Mandante']==team, df_team['Gols_Visitante_FT'], df_team['Gols_Mandante_FT'])
            total = marc + sofr
            
            res = {}
            for label, data in [("Feitos", marc), ("Sofridos", sofr), ("Total", total)]:
                m = calcular_estatisticas_avancadas(pd.Series(data))
                for k, v in m.items(): res[f"{label}_{k}"] = v
            return res

        metrics_m = get_metrics(df_m, m_sel, True)
        metrics_v = get_metrics(df_v, v_sel, False)
        st.write("Mandante vs Visitante (Comparativo Técnico)")
        st.table(pd.DataFrame([metrics_m, metrics_v], index=[m_sel, v_sel]).T)

    with t_min:
        st.subheader("Distribuição de Gols por Faixa de Tempo")
        faixas = ['0-15', '16-30', '31-45+', '46-60', '61-75', '76-90+']
        
        def build_min_tab(df_team, team):
            data_rows = []
            for f in faixas:
                col_m = f"{f}_Mandante" if f"{f}_Mandante" in df.columns else None
                col_v = f"{f}_Visitante" if f"{f}_Visitante" in df.columns else None
                if col_m and col_v:
                    feitos = np.where(df_team['Mandante']==team, df_team[col_m], df_team[col_v]).sum()
                    sofridos = np.where(df_team['Mandante']==team, df_team[col_v], df_team[col_m]).sum()
                    data_rows.append({"Minutos": f, "Gols Feitos": feitos, "Gols Sofridos": sofridos, "Total": feitos+sofridos})
            return pd.DataFrame(data_rows)

        cm, cv = st.columns(2)
        cm.write(m_sel); cm.table(build_min_tab(df_m, m_sel))
        cv.write(v_sel); cv.table(build_min_tab(df_v, v_sel))

    with t_class:
        # Lógica de Classificação Reintegrada
        stats_tab = {}
        for _, r in df_s.iterrows():
            for t in [r['Mandante'], r['Visitante']]:
                if t not in stats_tab: stats_tab[t] = {'P':0, 'J':0, 'V':0, 'GP':0, 'GC':0}
            stats_tab[r['Mandante']]['J'] += 1; stats_tab[r['Visitante']]['J'] += 1
            stats_tab[r['Mandante']]['GP'] += r['Gols_Mandante_FT']; stats_tab[r['Mandante']]['GC'] += r['Gols_Visitante_FT']
            stats_tab[r['Visitante']]['GP'] += r['Gols_Visitante_FT']; stats_tab[r['Visitante']]['GC'] += r['Gols_Mandante_FT']
            if r['Gols_Mandante_FT'] > r['Gols_Visitante_FT']: stats_tab[r['Mandante']]['P'] += 3; stats_tab[r['Mandante']]['V'] += 1
            elif r['Gols_Mandante_FT'] == r['Gols_Visitante_FT']: stats_tab[r['Mandante']]['P'] += 1; stats_tab[r['Visitante']]['P'] += 1
            else: stats_tab[r['Visitante']]['P'] += 3; stats_tab[r['Visitante']]['V'] += 1
        
        df_t = pd.DataFrame.from_dict(stats_tab, orient='index').reset_index().rename(columns={'index':'Time'})
        df_t['SG'] = df_t['GP'] - df_t['GC']
        df_t = df_t.sort_values(['P', 'V', 'SG'], ascending=False).reset_index(drop=True)
        df_t.insert(0, 'Pos', range(1, len(df_t)+1))
        df_t['Objetivo'] = [get_objetivo_txt(liga_sel, p) for p in df_t['Pos']]
        st.dataframe(df_t, use_container_width=True, hide_index=True)
