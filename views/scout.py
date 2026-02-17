import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from difflib import get_close_matches

def mostrar_scout(df):
    st.markdown("## 🔎 Painel de Análise Profissional Ultra")
    
    # 1. Ajuste e Limpeza de Colunas
    df.columns = [c.strip() for c in df.columns]

    # --- LÓGICA DE INDEXAÇÃO AUTOMÁTICA ---
    lista_ligas = sorted(df['Liga'].unique())
    idx_liga = 0
    if 'liga_scout' in st.session_state:
        matches_l = get_close_matches(st.session_state.liga_scout, lista_ligas, n=1, cutoff=0.6)
        if matches_l:
            idx_liga = lista_ligas.index(matches_l[0])

    # 2. SELEÇÃO DA LIGA
    liga_sel = st.selectbox("🏆 Escolha a Liga", lista_ligas, index=idx_liga)
    df_l = df[df['Liga'] == liga_sel].copy()

    # Filtro de Temporada Atual para cálculos de posição e força
    if 'Temporada' in df_l.columns:
        temp_atual = df_l['Temporada'].max()
        df_temp = df_l[df_l['Temporada'] == temp_atual].copy()
    else:
        df_temp = df_l.copy()

    # --- TIMES DA LIGA SELECIONADA ---
    lista_times = sorted(df_l['Mandante'].unique())
    
    idx_casa = 0
    if 'time_casa_scout' in st.session_state:
        matches_m = get_close_matches(st.session_state.time_casa_scout, lista_times, n=1, cutoff=0.6)
        if matches_m:
            idx_casa = lista_times.index(matches_m[0])

    m_sel = st.selectbox("🏠 Time da Casa", lista_times, index=idx_casa)
    
    visitantes_disp = [t for t in lista_times if t != m_sel]
    idx_fora = 0
    if 'time_fora_scout' in st.session_state:
        matches_v = get_close_matches(st.session_state.time_fora_scout, visitantes_disp, n=1, cutoff=0.6)
        if matches_v:
            idx_fora = visitantes_disp.index(matches_v[0])

    v_sel = st.selectbox("🚌 Time de Fora", visitantes_disp, index=idx_fora)

    # 4. CONFIGURAÇÃO (Sidebar)
    n_jogos = st.sidebar.slider("Amostragem (Últimos Jogos)", 5, 50, 10)
    mando_only = st.sidebar.checkbox("Analisar apenas Casa/Fora (Split)")

    # --- FUNÇÕES DE APOIO ---
    def extrair_metrica(df_hist, time, col_h, col_a):
        m = df_hist['Mandante'] == time
        v = df_hist['Visitante'] == time
        return pd.concat([df_hist[m][col_h], df_hist[v][col_a]])

    def calcular_tabela(df_input, apenas_mando=None):
        stats = {}
        df_work = df_input.copy()
        for _, r in df_work.iterrows():
            m, v = r['Mandante'], r['Visitante']
            gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
            for t in [m, v]:
                if t not in stats: stats[t] = {'P': 0, 'V': 0, 'SG': 0, 'J': 0}
            
            # Filtro para posição específica (Casa ou Fora)
            if apenas_mando == 'Casa':
                stats[m]['J'] += 1; stats[m]['SG'] += (gm - gv)
                if gm > gv: stats[m]['P'] += 3; stats[m]['V'] += 1
                elif gm == gv: stats[m]['P'] += 1
            elif apenas_mando == 'Fora':
                stats[v]['J'] += 1; stats[v]['SG'] += (gv - gm)
                if gv > gm: stats[v]['P'] += 3; stats[v]['V'] += 1
                elif gm == gv: stats[v]['P'] += 1
            else:
                stats[m]['J'] += 1; stats[v]['J'] += 1
                stats[m]['SG'] += (gm - gv); stats[v]['SG'] += (gv - gm)
                if gm > gv: stats[m]['P'] += 3; stats[m]['V'] += 1
                elif gm == gv: stats[m]['P'] += 1; stats[v]['P'] += 1
                else: stats[v]['P'] += 3; stats[v]['V'] += 1

        tab = pd.DataFrame.from_dict(stats, orient='index').reset_index().rename(columns={'index':'Time'})
        tab['PPG'] = tab['P'] / tab['J'].replace(0, 1)
        tab = tab.sort_values(by=['P', 'V', 'SG'], ascending=False).reset_index(drop=True)
        tab['Pos'] = tab.index + 1
        return tab

    def get_forma_lista(df_hist, time, modo='Geral'):
        if modo == 'Casa': df_f = df_hist[df_hist['Mandante'] == time]
        elif modo == 'Fora': df_f = df_hist[df_hist['Visitante'] == time]
        else: df_f = df_hist[(df_hist['Mandante'] == time) | (df_hist['Visitante'] == time)]
        
        df_f = df_f.sort_values('Data', ascending=False).head(5)
        res = []
        for _, r in df_f.iterrows():
            gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
            if gm == gv: res.append("🟡")
            elif (r['Mandante'] == time and gm > gv) or (r['Visitante'] == time and gv > gm): res.append("🟢")
            else: res.append("🔴")
        return " ".join(res)

    # --- CÁLCULO COEFICIENTE DE FORÇA ---
    def calcular_coeficiente(time, df_liga, posicao='Mandante'):
        # Médias da Competição para o bônus (M)
        avg_comp = {
            'posse': df_liga[['Possession_H', 'Possession_A']].mean().mean(),
            'gols': df_liga['Total_Gols_FT'].mean()
        }
        
        # Filtros
        df_time_geral = df_liga[(df_liga['Mandante'] == time) | (df_liga['Visitante'] == time)]
        if posicao == 'Mandante':
            df_time_split = df_liga[df_liga['Mandante'] == time]
            col_gols_marc, col_gols_sofr = 'Gols_Mandante_FT', 'Gols_Visitante_FT'
            col_odd, col_posse, col_atq, col_datq = 'Odd_Mandante_FT', 'Possession_H', 'Attacks_H', 'DangerousAttacks_H'
            col_shot, col_shot_tg, col_corn = 'Shots_H', 'ShotsOnTarget_H', 'Corners_H'
        else:
            df_time_split = df_liga[df_liga['Visitante'] == time]
            col_gols_marc, col_gols_sofr = 'Gols_Visitante_FT', 'Gols_Mandante_FT'
            col_odd, col_posse, col_atq, col_datq = 'Odd_Visitante_FT', 'Possession_A', 'Attacks_A', 'DangerousAttacks_A'
            col_shot, col_shot_tg, col_corn = 'Shots_A', 'ShotsOnTarget_A', 'Corners_A'

        if df_time_split.empty: return 0.0

        # Cálculos (A até L)
        tab_g = calcular_tabela(df_liga)
        ppg_g = tab_g[tab_g['Time'] == time]['PPG'].values[0] if time in tab_g['Time'].values else 0
        
        tab_s = calcular_tabela(df_liga, apenas_mando='Casa' if posicao=='Mandante' else 'Fora')
        ppg_s = tab_s[tab_s['Time'] == time]['PPG'].values[0] if time in tab_s['Time'].values else 0

        gols_marc_g = extrair_metrica(df_time_geral, time, 'Gols_Mandante_FT', 'Gols_Visitante_FT').mean()
        gols_marc_s = df_time_split[col_gols_marc].mean()
        gols_sofr_g = extrair_metrica(df_time_geral, time, 'Gols_Visitante_FT', 'Gols_Mandante_FT').mean()
        gols_sofr_s = df_time_split[col_gols_sofr].mean()
        
        odd_avg = df_time_split[col_odd].mean()
        posse = df_time_split[col_posse].mean() / 10
        atq = (df_time_split[col_atq].mean() + df_time_split[col_datq].mean()) / 10
        shots = (df_time_split[col_shot].mean() + df_time_split[col_shot_tg].mean())
        corners = df_time_split[col_corn].mean() / 4
        
        # Incidências (L)
        o05ht = (df_time_split['Total_Gols_HT'] > 0.5).mean() * 10
        o15ht = (df_time_split['Total_Gols_HT'] > 1.5).mean() * 5
        o15ft = (df_time_split['Total_Gols_FT'] > 1.5).mean() * 10
        o25ft = (df_time_split['Total_Gols_FT'] > 2.5).mean() * 5
        btts_ht = ((df_time_split['Gols_Mandante_HT']>0) & (df_time_split['Gols_Visitante_HT']>0)).mean() * 2
        btts_ft = ((df_time_split['Gols_Mandante_FT']>0) & (df_time_split['Gols_Visitante_FT']>0)).mean() * 5

        coef = (ppg_g) + (ppg_s * 2) + (gols_marc_g) + (gols_marc_s * 2) - (gols_sofr_g) - (gols_sofr_s * 2)
        coef += posse + atq + shots + corners + (o05ht + o15ht + o15ft + o25ft + btts_ht + btts_ft)
        coef -= (odd_avg if odd_avg < 10 else 0) # Subtração da Odd Média

        # Bônus vs Competição (M)
        if goals_marc_g > avg_comp['gols']: coef += 1
        
        return max(coef, 0)

    # --- RENDERIZAÇÃO DE CARDS ---
    st.divider()
    tab_geral = calcular_tabela(df_temp)
    tab_casa = calcular_tabela(df_temp, 'Casa')
    tab_fora = calcular_tabela(df_temp, 'Fora')

    try:
        def get_info(tab, time): 
            row = tab[tab['Time'] == time]
            return row['Pos'].values[0] if not row.empty else "?"

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"### 🏠 {m_sel}")
            coef_m = calcular_coeficiente(m_sel, df_temp, 'Mandante')
            st.info(f"**Índice de Força: {coef_m:.2f}**")
            cols = st.columns(2)
            cols[0].metric("Pos. Geral", f"{get_info(tab_geral, m_sel)}º")
            cols[1].metric("Pos. Como Mandante", f"{get_info(tab_casa, m_sel)}º")
            cols[0].metric("Forma Geral", get_forma_lista(df_temp, m_sel))
            cols[1].metric("Forma Casa", get_forma_lista(df_temp, m_sel, 'Casa'))

        with c2:
            st.markdown(f"### 🚌 {v_sel}")
            coef_v = calcular_coeficiente(v_sel, df_temp, 'Visitante')
            st.error(f"**Índice de Força: {coef_v:.2f}**")
            cols = st.columns(2)
            cols[0].metric("Pos. Geral", f"{get_info(tab_geral, v_sel)}º")
            cols[1].metric("Pos. Como Visitante", f"{get_info(tab_fora, v_sel)}º")
            cols[0].metric("Forma Geral", get_forma_lista(df_temp, v_sel))
            cols[1].metric("Forma Fora", get_forma_lista(df_temp, v_sel, 'Fora'))
    except Exception as e: st.warning(f"Erro ao carregar cards: {e}")

    # --- 3 & 4 (RADAR E MOMENTUM) - MANTIDOS ---
    # (Inserir aqui as funções criar_radar_normalizado e plot_momentum do código anterior)
    # [RADAR DE ESTILO E MOMENTUM]
    
    # --- 5. ESTATÍSTICAS DETALHADAS (ORGANIZADAS POR BLOCOS) ---
    st.divider()
    st.subheader("📉 Estatísticas de Performance Detalhadas")

    def format_style(val, metric_type):
        if metric_type == 'DP':
            color = 'background-color: #d4edda' if val < 1.0 else '' # Verde para baixa variação
        elif metric_type == 'CV':
            color = 'background-color: #d4edda' if val < 0.2 else ''
        else: color = ''
        return color

    def criar_bloco_tecnico(df_m, df_v, time_m, time_v, titulo, metricas_dict):
        st.markdown(f"#### {titulo}")
        res_m, res_v = [], []
        for label, cols in metricas_dict.items():
            # col_h, col_a
            sm = extrair_metrica(df_m, time_m, cols[0], cols[1])
            sv = extrair_metrica(df_v, time_v, cols[0], cols[1])
            
            def get_row(series, lab):
                series = pd.to_numeric(series, errors='coerce').fillna(0)
                mean = series.mean()
                std = series.std()
                return [lab, mean, series.median(), series.mode().iloc[0] if not series.mode().empty else 0, std, (std/mean if mean!=0 else 0)]
            
            res_m.append(get_row(sm, label))
            res_v.append(get_row(sv, label))
        
        c_a, c_b = st.columns(2)
        cols_name = ['Métrica', 'Média', 'Mediana', 'Moda', 'DP', 'CV']
        with c_a: 
            st.write(f"**{time_m}**")
            st.table(pd.DataFrame(res_m, columns=cols_name).style.format({c: "{:.2f}" for c in cols_name[1:]}))
        with c_b: 
            st.write(f"**{time_v}**")
            st.table(pd.DataFrame(res_v, columns=cols_name).style.format({c: "{:.2f}" for c in cols_name[1:]}))

    # Configuração dos Blocos
    blocos = {
        "⚽ Gols": {
            "Marcados": ('Gols_Mandante_FT', 'Gols_Visitante_FT'),
            "Sofridos": ('Gols_Visitante_FT', 'Gols_Mandante_FT'),
            "Total (M+S)": ('Total_Gols_FT', 'Total_Gols_FT')
        },
        "🚩 Cantos": {
            "Cantos FT Marcados": ('Corners_H', 'Corners_A'),
            "Cantos FT Sofridos": ('Corners_A', 'Corners_H'),
            "Cantos HT Marcados": ('Corners_H_HT', 'Corners_A_HT'),
            "Cantos HT Sofridos": ('Corners_A_HT', 'Corners_H_HT')
        },
        "🎯 Chutes & Finalizações": {
            "Chutes no Gol": ('ShotsOnTarget_H', 'ShotsOnTarget_A'),
            "Finalizações Total": ('Shots_H', 'Shots_A')
        },
        "⚖️ Faltas & Cartões": {
            "Faltas Sofridas": ('Freekicks_H', 'Freekicks_A'),
            "Faltas Cometidas": ('Fouls_H', 'Fouls_A'),
            "Cartões Amarelos": ('Yellow_Cards_H', 'Yellow_Cards_A'),
            "Cartões Vermelhos": ('Red_Cards_H', 'Red_Cards_A')
        },
        "📊 Posse & xG": {
            "Posse de Bola": ('Possession_H', 'Possession_A'),
            "xG (Gols Esperados)": ('xG_Mandante', 'xG_Visitante')
        }
    }

    # Renderiza blocos
    df_m_last = df_l[(df_l['Mandante'] == m_sel) | (df_l['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(n_jogos)
    df_v_last = df_l[(df_l['Mandante'] == v_sel) | (df_l['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(n_jogos)

    for tit, met in blocos.items():
        criar_bloco_tecnico(df_m_last, df_v_last, m_sel, v_sel, tit, met)

    # --- CALCULADORA DE VALOR EXPANDIDA ---
    st.divider()
    st.subheader("💎 Calculadora de Valor e Incidência")
    def calc_inc_exp(df_h):
        df_h = df_h.copy()
        mercados = {
            'Over 0.5 HT': df_h['Total_Gols_HT'] > 0.5,
            'Over 1.5 HT': df_h['Total_Gols_HT'] > 1.5,
            'BTTS HT': (df_h['Gols_Mandante_HT']>0) & (df_h['Gols_Visitante_HT']>0),
            'Over 1.5 FT': df_h['Total_Gols_FT'] > 1.5,
            'Over 2.5 FT': df_h['Total_Gols_FT'] > 2.5,
            'BTTS FT': (df_h['Gols_Mandante_FT']>0) & (df_h['Gols_Visitante_FT']>0),
            'Over 3.5 Cantos HT': df_h['Total_Corners_HT'] > 3.5,
            'Over 4.5 Cantos HT': df_h['Total_Corners_HT'] > 4.5,
            'Over 8.5 Cantos FT': df_h['Total_Corners'] > 8.5,
            'Over 9.5 Cantos FT': df_h['Total_Corners'] > 9.5,
            'Over 10.5 Cantos FT': df_h['Total_Corners'] > 10.5,
        }
        res = []
        for m, cond in mercados.items():
            freq = cond.mean()
            res.append({'Mercado': m, 'Freq': f"{freq*100:.1f}%", 'Odd Justa': f"{1/freq:.2f}" if freq > 0 else "N/A"})
        return pd.DataFrame(res)

    ci1, ci2 = st.columns(2)
    with ci1: st.write(f"**Mercados {m_sel}**"); st.table(calc_inc_exp(df_m_last))
    with ci2: st.write(f"**Mercados {v_sel}**"); st.table(calc_inc_exp(df_v_last))

    # --- HISTÓRICO DETALHADO EXPANDIDO ---
    st.divider()
    st.markdown("### 📝 Histórico Detalhado (Últimos 10 Jogos)")
    
    def preparar_h_exp(df_h, time, modo='Geral'):
        if modo == 'Casa': df_f = df_h[df_h['Mandante'] == time]
        elif modo == 'Fora': df_f = df_h[df_h['Visitante'] == time]
        else: df_f = df_h[(df_h['Mandante']==time)|(df_h['Visitante']==time)]
        
        df_f = df_f.sort_values('Data', ascending=False).head(10)
        res = []
        for _, r in df_f.iterrows():
            res.append({
                'Data': r['Data'],
                'Mando': "Casa" if r['Mandante']==time else "Fora",
                'Oponente': r['Visitante'] if r['Mandante']==time else r['Mandante'],
                'FT': f"{int(r['Gols_Mandante_FT'])}x{int(r['Gols_Visitante_FT'])}",
                'HT': f"{int(r['Gols_Mandante_HT'])}x{int(r['Gols_Visitante_HT'])}",
                'Cantos HT': f"{int(r['Total_Corners_HT'])}",
                'Cantos FT': f"{int(r['Total_Corners'])}",
                'xG': f"{r['xG_Mandante']:.1f}-{r['xG_Visitante']:.1f}",
                'Odd H': r['Odd_Mandante_FT'], 'Odd D': r['Odd_Empate_FT'], 'Odd A': r['Odd_Visitante_FT']
            })
        return pd.DataFrame(res)

    st.write(f"**Últimos 10 Jogos Gerais: {m_sel}**")
    st.table(preparar_h_exp(df_l, m_sel, 'Geral'))
    
    st.write(f"**Últimos 10 Jogos Casa vs Casa: {m_sel}**")
    st.table(preparar_h_exp(df_l, m_sel, 'Casa'))

    st.write(f"**Últimos 10 Jogos Gerais: {v_sel}**")
    st.table(preparar_h_exp(df_l, v_sel, 'Geral'))
    
    st.write(f"**Últimos 10 Jogos Fora vs Fora: {v_sel}**")
    st.table(preparar_h_exp(df_l, v_sel, 'Fora'))
