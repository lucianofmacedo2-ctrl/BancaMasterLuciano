import streamlit as st
import pandas as pd
import numpy as np

# --- DICIONÁRIO DE REGRAS DE OBJETIVOS ---
REGRAS_LIGAS = {
    "BRAZIL 1": {"alvos": {"Libertadores": [1, 6], "Sul-Americana": [7, 12], "Rebaixamento": [17, 20]}},
    "BRAZIL 2": {"alvos": {"Acesso": [1, 4], "Rebaixamento": [17, 20]}},
    "PORTUGAL 3": {"alvos": {"Acesso": [1, 2], "Playoff Acesso": [3, 4], "Rebaixamento": [7, 10]}},
    "ENGLAND 1": {"alvos": {"Champions League": [1, 4], "Europa League": [5, 5], "Rebaixamento": [18, 20]}},
}

# --- FUNÇÕES DE CÁLCULO ---
def get_objetivo_txt(liga, pos):
    liga_clean = str(liga).upper().strip()
    if liga_clean not in REGRAS_LIGAS: return "⚪ Meio"
    regras = REGRAS_LIGAS[liga_clean]["alvos"]
    for obj, faixa in regras.items():
        if faixa[0] <= pos <= faixa[1]:
            return f"{'🔴' if 'Rebaixamento' in obj else '🟢'} {obj}"
    return "⚪ Meio"

def calcular_metricas_completas(series, prefixo):
    if len(series) == 0:
        return {f"{prefixo} Média": 0, f"{prefixo} Mediana": 0, f"{prefixo} Moda": 0, f"{prefixo} DP": 0, f"{prefixo} CV%": 0}
    
    return {
        f"{prefixo} Média": series.mean(),
        f"{prefixo} Mediana": series.median(),
        f"{prefixo} Moda": series.mode().iloc[0] if not series.mode().empty else series.mean(),
        f"{prefixo} DP": series.std(),
        f"{prefixo} CV%": (series.std() / series.mean() * 100) if series.mean() != 0 else 0,
        f"{prefixo} 0.5+ (%)": (series > 0.5).mean() * 100,
        f"{prefixo} 1.5+ (%)": (series > 1.5).mean() * 100,
        f"{prefixo} 2.5+ (%)": (series > 2.5).mean() * 100,
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

def extrair_dados_mercado(df_team, team, col_h, col_a):
    feitos = np.where(df_team['Mandante'] == team, df_team[col_h], df_team[col_a])
    sofridos = np.where(df_team['Mandante'] == team, df_team[col_a], df_team[col_h])
    totais = feitos + sofridos
    return pd.Series(feitos), pd.Series(sofridos), pd.Series(totais)

def gerar_tabela_segmentada(df_m, df_v, m_sel, v_sel, col_h, col_a, titulo):
    fm, sm, tm = extrair_dados_mercado(df_m, m_sel, col_h, col_a)
    fv, sv, tv = extrair_dados_mercado(df_v, v_sel, col_h, col_a)
    
    dados = []
    for t_name, f, s, t in [(m_sel, fm, sm, tm), (v_sel, fv, sv, tv)]:
        row = {"Equipe": t_name}
        row.update(calcular_metricas_completas(f, "Feitos"))
        row.update(calcular_metricas_completas(s, "Sofridos"))
        row.update(calcular_metricas_completas(t, "Total"))
        # Adiciona Probabilidade BTTS se for Gols
        if "Gols" in titulo:
            btts = ((f > 0) & (s > 0)).mean() * 100
            row["BTTS Sim (%)"] = btts
        dados.append(row)
    
    st.markdown(f"#### {titulo}")
    st.dataframe(pd.DataFrame(dados).set_index("Equipe").T, use_container_width=True)

def mostrar_scout(df):
    if df.empty: return st.error("CSV vazio")
    
    st.title("🔎 Scout Profissional - Análise Profunda")
    
    # --- FILTROS ---
    df['Liga'] = df['Liga'].astype(str).str.strip().str.upper()
    c1, c2, c3 = st.columns(3)
    liga_sel = c1.selectbox("Liga", sorted(df['Liga'].unique()))
    df_l = df[df['Liga'] == liga_sel].copy()
    temp_sel = c2.selectbox("Temporada", sorted(df_l['Temporada'].unique(), reverse=True))
    mando_sel = c3.selectbox("Filtro de Mando", ["Geral (Todos)", "Casa/Fora Específico"])
    
    df_s = df_l[df_l['Temporada'] == temp_sel].copy()
    times = sorted(df_s['Mandante'].unique())
    m_sel = st.selectbox("Mandante", times)
    v_sel = st.selectbox("Visitante", [t for t in times if t != m_sel])
    
    n_jogos = st.sidebar.slider("Amostragem de Jogos", 5, 50, 10)

    if mando_sel == "Geral (Todos)":
        df_m = df_s[(df_s['Mandante'] == m_sel) | (df_s['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(n_jogos)
        df_v = df_s[(df_s['Mandante'] == v_sel) | (df_s['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(n_jogos)
    else:
        df_m = df_s[df_s['Mandante'] == m_sel].sort_values('Data', ascending=False).head(n_jogos)
        df_v = df_s[df_s['Visitante'] == v_sel].sort_values('Data', ascending=False).head(n_jogos)

    # --- POWER STATS ---
    st.divider()
    if 'Attacks_H' in df.columns:
        render_stat_row("ATAQUES TOTAIS", 
                        np.where(df_m['Mandante']==m_sel, df_m['Attacks_H'], df_m['Attacks_A']).mean(),
                        np.where(df_v['Mandante']==v_sel, df_v['Attacks_H'], df_v['Attacks_A']).mean())
        render_stat_row("ATAQUES PERIGOSOS", 
                        np.where(df_m['Mandante']==m_sel, df_m['DangerousAttacks_H'], df_m['DangerousAttacks_A']).mean(),
                        np.where(df_v['Mandante']==v_sel, df_v['DangerousAttacks_H'], df_v['DangerousAttacks_A']).mean())
    if 'Possession_H' in df.columns:
        render_stat_row("POSSE DE BOLA (%)", 
                        np.where(df_m['Mandante']==m_sel, df_m['Possession_H'], df_m['Possession_A']).mean(),
                        np.where(df_v['Mandante']==v_sel, df_v['Possession_H'], df_v['Possession_A']).mean())

    # --- ABAS ---
    t_forma, t_stats, t_minutos, t_class = st.tabs(["🕒 Forma", "📊 Stats Detalhadas", "⏰ Minutos", "🏆 Tabela"])

    with t_forma:
        c_m, c_v = st.columns(2)
        c_m.write(f"Últimos {n_jogos} - {m_sel}")
        c_m.dataframe(df_m[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], hide_index=True)
        c_v.write(f"Últimos {n_jogos} - {v_sel}")
        c_v.dataframe(df_v[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], hide_index=True)

    with t_stats:
        st.subheader("📊 Tabelas de Estatísticas Segmentadas")
        
        # 1. Gols HT
        gerar_tabela_segmentada(df_m, df_v, m_sel, v_sel, 'Gols_Mandante_HT', 'Gols_Visitante_HT', "⚽ Gols HT (1º Tempo)")
        
        # 2. Gols FT
        gerar_tabela_segmentada(df_m, df_v, m_sel, v_sel, 'Gols_Mandante_FT', 'Gols_Visitante_FT', "⚽ Gols FT (Jogo Completo)")
        
        # 3. Cantos (Corners)
        col_c_h = 'Corners_H' if 'Corners_H' in df.columns else ('Cantos_Mandante_FT' if 'Cantos_Mandante_FT' in df.columns else None)
        col_c_a = 'Corners_A' if 'Corners_A' in df.columns else ('Cantos_Visitante_FT' if 'Cantos_Visitante_FT' in df.columns else None)
        if col_c_h:
            gerar_tabela_segmentada(df_m, df_v, m_sel, v_sel, col_c_h, col_c_a, "🚩 Cantos (Escanteios)")
            
        # 4. Chutes (Shots)
        if 'Shots_H' in df.columns:
            gerar_tabela_segmentada(df_m, df_v, m_sel, v_sel, 'Shots_H', 'Shots_A', "👟 Chutes Totais")

    with t_minutos:
        faixas = ['0-15', '16-30', '31-45+', '46-60', '61-75', '76-90+']
        def calc_min_tab(df_team, team):
            data = []
            for f in faixas:
                if f"{f}_Mandante" in df.columns:
                    f_g = np.where(df_team['Mandante']==team, df_team[f"{f}_Mandante"], df_team[f"{f}_Visitante"]).sum()
                    s_g = np.where(df_team['Mandante']==team, df_team[f"{f}_Visitante"], df_team[f"{f}_Mandante"]).sum()
                    data.append({"Minutos": f, "Feitos": f_g, "Sofridos": s_g, "Total": f_g+s_g})
            return pd.DataFrame(data)
        
        c1, c2 = st.columns(2)
        c1.write(f"Distribuição: {m_sel}"); c1.table(calc_min_tab(df_m, m_sel))
        c2.write(f"Distribuição: {v_sel}"); c2.table(calc_min_tab(df_v, v_sel))

    with t_class:
        # Reconstrução da Tabela de Pontos
        tab_data = {}
        for _, r in df_s.iterrows():
            for t in [r['Mandante'], r['Visitante']]:
                if t not in tab_data: tab_data[t] = {'P':0,'J':0,'V':0,'E':0,'D':0,'GP':0,'GC':0}
            m, v, gm, gv = r['Mandante'], r['Visitante'], r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
            tab_data[m]['J']+=1; tab_data[v]['J']+=1
            tab_data[m]['GP']+=gm; tab_data[m]['GC']+=gv
            tab_data[v]['GP']+=gv; tab_data[v]['GC']+=gm
            if gm > gv: tab_data[m]['P']+=3; tab_data[m]['V']+=1; tab_data[v]['D']+=1
            elif gm == gv: tab_data[m]['P']+=1; tab_data[v]['P']+=1; tab_data[m]['E']+=1; tab_data[v]['E']+=1
            else: tab_data[v]['P']+=3; tab_data[v]['V']+=1; tab_data[m]['D']+=1
        
        df_tab = pd.DataFrame.from_dict(tab_data, orient='index').reset_index().rename(columns={'index':'Time'})
        df_tab['SG'] = df_tab['GP'] - df_tab['GC']
        df_tab = df_tab.sort_values(['P','V','SG'], ascending=False).reset_index(drop=True)
        df_tab.insert(0, 'Pos', range(1, len(df_tab)+1))
        df_tab['Objetivo'] = [get_objetivo_txt(liga_sel, p) for p in df_tab['Pos']]
        st.dataframe(df_tab, use_container_width=True, hide_index=True)
