import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats as sp_stats

# --- DICIONÁRIO DE REGRAS DE OBJETIVOS (Expandido) ---
REGRAS_LIGAS = {
    "BRAZIL 1": {"alvos": {"Libertadores": [1, 6], "Sul-Americana": [7, 12], "Rebaixamento": [17, 20]}},
    "BRAZIL 2": {"alvos": {"Acesso": [1, 4], "Rebaixamento": [17, 20]}},
    "PORTUGAL 3": {"alvos": {"Acesso": [1, 2], "Playoff Acesso": [3, 4], "Rebaixamento": [7, 10]}},
    "ENGLAND 1": {"alvos": {"Champions League": [1, 4], "Europa League": [5, 5], "Rebaixamento": [18, 20]}},
    "SPAIN 1": {"alvos": {"Champions League": [1, 4], "Europa League": [5, 6], "Rebaixamento": [18, 20]}},
    "ITALY 1": {"alvos": {"Champions League": [1, 4], "Europa League": [5, 6], "Rebaixamento": [18, 20]}},
    "GERMANY 1": {"alvos": {"Champions League": [1, 4], "Europa League": [5, 5], "Rebaixamento": [16, 18]}},
}

# --- FUNÇÕES DE APOIO ---
def get_objetivo_txt(liga, pos):
    liga_clean = str(liga).upper().strip()
    if liga_clean not in REGRAS_LIGAS: return "⚪ Meio de Tabela"
    regras = REGRAS_LIGAS[liga_clean]["alvos"]
    for obj, faixa in regras.items():
        if faixa[0] <= pos <= faixa[1]:
            emoji = "🔴" if "Rebaixamento" in obj else "🟢"
            return f"{emoji} {obj}"
    return "⚪ Meio de Tabela"

def calcular_estatisticas_completas(series):
    if len(series) == 0: return {k: 0 for k in ["Média", "Mediana", "Moda", "DP", "CV%", "0.5+", "1.5+", "2.5+", "3.5+"]}
    return {
        "Média": series.mean(),
        "Mediana": series.median(),
        "Moda": series.mode().iloc[0] if not series.mode().empty else series.mean(),
        "DP": series.std(),
        "CV%": (series.std() / series.mean() * 100) if series.mean() != 0 else 0,
        "0.5+": (series > 0.5).mean() * 100,
        "1.5+": (series > 1.5).mean() * 100,
        "2.5+": (series > 2.5).mean() * 100,
        "3.5+": (series > 3.5).mean() * 100,
    }

def render_stat_row(label, val_h, val_v):
    col1, col2, col3 = st.columns([1, 2, 1])
    vh, vv = float(val_h or 0), float(val_v or 0)
    total = vh + vv
    perc = vh / total if total > 0 else 0.5
    with col1: st.markdown(f"<p style='text-align:right;font-weight:bold;font-size:18px;margin:0;'>{vh:.2f}</p>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<p style='text-align:center;font-size:12px;color:gray;margin:0;'>{label}</p>", unsafe_allow_html=True)
        st.progress(max(0.0, min(1.0, perc)))
    with col3: st.markdown(f"<p style='text-align:left;font-weight:bold;font-size:18px;margin:0;'>{vv:.2f}</p>", unsafe_allow_html=True)

# --- FUNÇÃO PRINCIPAL ---
def mostrar_scout(df):
    if df.empty:
        st.error("Base de dados não carregada.")
        return

    st.title("🔎 Scout Profissional de Elite")

    # Filtros Iniciais
    df['Liga'] = df['Liga'].astype(str).str.strip().str.upper()
    ligas = sorted(df['Liga'].unique())
    
    c1, c2, c3 = st.columns(3)
    liga_sel = c1.selectbox("Selecione a Liga", ligas)
    df_l = df[df['Liga'] == liga_sel].copy()
    
    temp_sel = c2.selectbox("Temporada", sorted(df_l['Temporada'].unique(), reverse=True))
    df_s = df_l[df_l['Temporada'] == temp_sel].copy()
    
    mando_sel = c3.selectbox("Mando de Campo", ["Geral (Todos os Jogos)", "Específico (Casa/Fora)"])

    times = sorted(df_s['Mandante'].unique())
    m_sel = st.selectbox("Equipe Mandante", times)
    v_sel = st.selectbox("Equipe Visitante", [t for t in times if t != m_sel])

    n_jogos = st.sidebar.slider("Últimos Jogos para Análise", 5, 50, 10)

    # Lógica de Filtragem de Jogos (REINTEGRADA)
    if mando_sel == "Geral (Todos os Jogos)":
        df_m = df_s[(df_s['Mandante'] == m_sel) | (df_s['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(n_jogos)
        df_v = df_s[(df_s['Mandante'] == v_sel) | (df_s['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(n_jogos)
    else:
        df_m = df_s[df_s['Mandante'] == m_sel].sort_values('Data', ascending=False).head(n_jogos)
        df_v = df_s[df_s['Visitante'] == v_sel].sort_values('Data', ascending=False).head(n_jogos)

    # --- SEÇÃO DE POWER STATS (Métricas do Novo CSV) ---
    st.markdown("### ⚡ Power Stats (Médias)")
    
    # Ataques e Pressão
    if 'Attacks_H' in df.columns:
        att_m = np.where(df_m['Mandante']==m_sel, df_m['Attacks_H'], df_m['Attacks_A']).mean()
        att_v = np.where(df_v['Mandante']==v_sel, df_v['Attacks_H'], df_v['Attacks_A']).mean()
        render_stat_row("ATAQUES TOTAIS", att_m, att_v)

        datt_m = np.where(df_m['Mandante']==m_sel, df_m['DangerousAttacks_H'], df_m['DangerousAttacks_A']).mean()
        datt_v = np.where(df_v['Mandante']==v_sel, df_v['DangerousAttacks_H'], df_v['DangerousAttacks_A']).mean()
        render_stat_row("ATAQUES PERIGOSOS", datt_m, datt_v)

    # Chutes e Posse
    if 'Shots_H' in df.columns:
        sh_m = np.where(df_m['Mandante']==m_sel, df_m['Shots_H'], df_m['Shots_A']).mean()
        sh_v = np.where(df_v['Mandante']==v_sel, df_v['Shots_H'], df_v['Shots_A']).mean()
        render_stat_row("CHUTES TOTAIS", sh_m, sh_v)

        poss_m = np.where(df_m['Mandante']==m_sel, df_m['Possession_H'], df_m['Possession_A']).mean()
        poss_v = np.where(df_v['Mandante']==v_sel, df_v['Possession_H'], df_v['Possession_A']).mean()
        render_stat_row("POSSE DE BOLA (%)", poss_m, poss_v)

    # --- ABAS DE ANÁLISE PROFUNDA ---
    t_forma, t_h2h, t_stats_ft, t_stats_ht, t_minutos, t_classificacao = st.tabs([
        "🕒 Forma", "⚔️ H2H", "📊 Stats FT", "⏱️ Stats HT", "⏰ Tabela Minutos", "🏆 Classificação"
    ])

    with t_forma:
        col1, col2 = st.columns(2)
        col1.subheader(f"Últimos de {m_sel}")
        col1.dataframe(df_m[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], hide_index=True)
        col2.subheader(f"Últimos de {v_sel}")
        col2.dataframe(df_v[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], hide_index=True)

    with t_h2h:
        h2h = df_s[((df_s['Mandante'] == m_sel) & (df_s['Visitante'] == v_sel)) | 
                  ((df_s['Mandante'] == v_sel) & (df_s['Visitante'] == m_sel))].sort_values('Data', ascending=False)
        st.dataframe(h2h[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], use_container_width=True, hide_index=True)

    with t_stats_ft:
        st.subheader("📊 Estatísticas Detalhadas - Final do Jogo (FT)")
        
        def processar_mercados(df_team, team):
            # Gols
            marc = np.where(df_team['Mandante']==team, df_team['Gols_Mandante_FT'], df_team['Gols_Visitante_FT'])
            sofr = np.where(df_team['Mandante']==team, df_team['Gols_Visitante_FT'], df_team['Gols_Mandante_FT'])
            # Cantos
            c_m = np.where(df_team['Mandante']==team, df_team.get('Corners_H', 0), df_team.get('Corners_A', 0))
            # BTTS
            btts = ((df_team['Gols_Mandante_FT'] > 0) & (df_team['Gols_Visitante_FT'] > 0)).mean() * 100
            
            res = {}
            for label, data in [("Gols Feitos", marc), ("Gols Sofridos", sofr), ("Gols Totais", marc+sofr), ("Cantos", c_m)]:
                calc = calcular_estatisticas_completas(pd.Series(data))
                for k, v in calc.items(): res[f"{label}_{k}"] = v
            res["BTTS_Sim (%)"] = btts
            return res

        s_m = processar_mercados(df_m, m_sel)
        s_v = processar_mercados(df_v, v_sel)
        st.table(pd.DataFrame([s_m, s_v], index=[m_sel, v_sel]).T)

    with t_stats_ht:
        st.subheader("⏱️ Estatísticas Detalhadas - Primeiro Tempo (HT)")
        def processar_ht(df_team, team):
            marc = np.where(df_team['Mandante']==team, df_team['Gols_Mandante_HT'], df_team['Gols_Visitante_HT'])
            sofr = np.where(df_team['Mandante']==team, df_team['Gols_Visitante_HT'], df_team['Gols_Mandante_HT'])
            res = {}
            for label, data in [("Gols HT Feitos", marc), ("Gols HT Sofridos", sofr), ("Total HT", marc+sofr)]:
                calc = calcular_estatisticas_completas(pd.Series(data))
                for k, v in calc.items(): res[f"{label}_{k}"] = v
            return res
        st.table(pd.DataFrame([processar_ht(df_m, m_sel), processar_ht(df_v, v_sel)], index=[m_sel, v_sel]).T)

    with t_minutos:
        st.subheader("⏰ Tabela Detalhada de Gols por Minutos")
        faixas = ['0-15', '16-30', '31-45+', '46-60', '61-75', '76-90+']
        
        def tab_minutos(df_team, team):
            linhas = []
            for f in faixas:
                col_h = f"{f}_Mandante"
                col_a = f"{f}_Visitante"
                if col_h in df.columns and col_a in df.columns:
                    f_g = np.where(df_team['Mandante']==team, df_team[col_h], df_team[col_a]).sum()
                    s_g = np.where(df_team['Mandante']==team, df_team[col_a], df_team[col_h]).sum()
                    linhas.append({"Faixa": f, "Feitos": f_g, "Sofridos": s_g, "Total": f_g + s_g})
            return pd.DataFrame(linhas)

        cmin1, cmin2 = st.columns(2)
        cmin1.write(f"Minutos: {m_sel}")
        cmin1.table(tab_minutos(df_m, m_sel))
        cmin2.write(f"Minutos: {v_sel}")
        cmin2.table(tab_minutos(df_v, v_sel))

    with t_classificacao:
        st.subheader(f"🏆 Classificação - {liga_sel} ({temp_sel})")
        # Lógica de Classificação completa
        stats_c = {}
        for _, r in df_s.iterrows():
            for t in [r['Mandante'], r['Visitante']]:
                if t not in stats_c: stats_c[t] = {'P':0, 'J':0, 'V':0, 'E':0, 'D':0, 'GP':0, 'GC':0}
            stats_c[r['Mandante']]['J'] += 1; stats_c[r['Visitante']]['J'] += 1
            stats_c[r['Mandante']]['GP'] += r['Gols_Mandante_FT']; stats_c[r['Mandante']]['GC'] += r['Gols_Visitante_FT']
            stats_c[r['Visitante']]['GP'] += r['Gols_Visitante_FT']; stats_c[r['Visitante']]['GC'] += r['Gols_Mandante_FT']
            if r['Gols_Mandante_FT'] > r['Gols_Visitante_FT']: stats_c[r['Mandante']]['P'] += 3; stats_c[r['Mandante']]['V'] += 1
            elif r['Gols_Mandante_FT'] == r['Gols_Visitante_FT']: stats_c[r['Mandante']]['P'] += 1; stats_c[r['Visitante']]['P'] += 1
            else: stats_c[r['Visitante']]['P'] += 3; stats_c[r['Visitante']]['V'] += 1
        
        df_tab = pd.DataFrame.from_dict(stats_c, orient='index').reset_index().rename(columns={'index':'Time'})
        df_tab['SG'] = df_tab['GP'] - df_tab['GC']
        df_tab = df_tab.sort_values(['P', 'V', 'SG'], ascending=False).reset_index(drop=True)
        df_tab.insert(0, 'Pos', range(1, len(df_tab)+1))
        df_tab['Objetivo'] = [get_objetivo_txt(liga_sel, p) for p in df_tab['Pos']]
        st.dataframe(df_tab, use_container_width=True, hide_index=True)
