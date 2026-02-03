import streamlit as st
import pandas as pd
import numpy as np

# --- CONFIGURAÇÃO DE LIGAS (RANKING) ---
REGRAS_LIGAS = {
    "BRAZIL 1": {"alvos": {"Libertadores": [1, 6], "Sul-Americana": [7, 12], "Rebaixamento": [17, 20]}},
    "PORTUGAL 1": {"alvos": {"Champions League": [1, 3], "Rebaixamento": [16, 18]}},
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

def calcular_stats_completas(series):
    if series.empty: return [0]*5
    mean = series.mean()
    median = series.median()
    mode = series.mode().iloc[0] if not series.mode().empty else 0
    std = series.std()
    cv = (std / mean) if mean != 0 else 0
    return [mean, median, mode, std, cv]

def criar_tabela_estatistica(df_t, time, label_prefix):
    # Mapeamento de colunas baseado no seu novo CSV
    mapa = {
        'Gols HT': ('Gols_Mandante_HT', 'Gols_Visitante_HT'),
        'Gols FT': ('Gols_Mandante_FT', 'Gols_Visitante_FT'),
        'Cantos HT': ('Corners_H_HT', 'Corners_A_HT'), # Caso existam no CSV original
        'Cantos FT': ('Corners_H', 'Corners_A'),
        'Chutes': ('Shots_H', 'Shots_A'),
        'Finalizações': ('ShotsOnTarget_H', 'ShotsOnTarget_A'),
        'Cartões': ('Yellow_Cards_H', 'Yellow_Cards_A')
    }
    
    data = []
    for metric, (col_h, col_a) in mapa.items():
        if col_h in df_t.columns:
            series = pd.concat([df_t[df_t['Mandante'] == time][col_h], df_t[df_t['Visitante'] == time][col_a]])
            stats = calcular_stats_completas(series)
            data.append([metric] + stats)
    
    return pd.DataFrame(data, columns=['Indicador', 'Média', 'Mediana', 'Moda', 'DP', 'CV'])

def calcular_incidencia_mercados(df_t, time):
    # Cálculos de Totais
    df_t['Total_FT'] = df_t['Gols_Mandante_FT'] + df_t['Gols_Visitante_FT']
    df_t['Total_HT'] = df_t['Gols_Mandante_HT'] + df_t['Gols_Visitante_HT']
    df_t['Cantos_FT'] = df_t['Corners_H'] + df_t['Corners_A']
    
    df_t['BTTS_FT'] = (df_t['Gols_Mandante_FT'] > 0) & (df_t['Gols_Visitante_FT'] > 0)
    df_t['BTTS_HT'] = (df_t['Gols_Mandante_HT'] > 0) & (df_t['Gols_Visitante_HT'] > 0)

    rows = []
    # Gols
    for m in [0.5, 1.5, 2.5, 3.5]:
        rows.append({'Mercado': f'Over {m} Gols', 'HT': f"{(df_t['Total_HT'] > m).mean()*100:.1f}%", 'FT': f"{(df_t['Total_FT'] > m).mean()*100:.1f}%"})
    
    # Cantos
    for c in [7.5, 8.5, 9.5, 10.5]:
        rows.append({'Mercado': f'Over {c} Cantos', 'HT': '-', 'FT': f"{(df_t['Cantos_FT'] > c).mean()*100:.1f}%"})
    
    rows.append({'Mercado': 'Ambas Marcam', 'HT': f"{df_t['BTTS_HT'].mean()*100:.1f}%", 'FT': f"{df_t['BTTS_FT'].mean()*100:.1f}%"})
    
    return pd.DataFrame(rows)

def render_stat_row(label, val_h, val_v, format_str="{:.2f}"):
    col1, col2, col3 = st.columns([1, 2, 1])
    vh, vv = float(val_h or 0), float(val_v or 0)
    total = vh + vv
    perc = vh / total if total > 0 else 0.5
    with col1: st.markdown(f"<p style='text-align:right;font-weight:bold;font-size:18px;margin:0;'>{format_str.format(vh)}</p>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<p style='text-align:center;font-size:11px;color:gray;margin:0;'>{label}</p>", unsafe_allow_html=True)
        st.progress(max(0.0, min(1.0, perc)))
    with col3: st.markdown(f"<p style='text-align:left;font-weight:bold;font-size:18px;margin:0;'>{format_str.format(vv)}</p>", unsafe_allow_html=True)

# --- VIEW PRINCIPAL ---
def mostrar_scout(df):
    st.title("🔎 Scout Profissional - Master Luciano")
    df.columns = [c.strip() for c in df.columns]
    if 'Data' in df.columns:
        df['Data'] = pd.to_datetime(df['Data'])

    # Filtros
    c1, c2, c3 = st.columns(3)
    liga_sel = c1.selectbox("Liga", sorted(df['Liga'].unique()))
    df_l = df[df['Liga'] == liga_sel].copy()
    temp_sel = c2.selectbox("Temporada", sorted(df_l['Temporada'].unique(), reverse=True))
    mando_sel = c3.selectbox("Mando", ["Geral", "Casa/Fora"])
    
    df_s = df_l[df_l['Temporada'] == temp_sel].copy()
    times = sorted(df_s['Mandante'].unique())
    m_sel = st.selectbox("Mandante", times)
    v_sel = st.selectbox("Visitante", [t for t in times if t != m_sel])
    n_jogos = st.sidebar.slider("Amostragem", 5, 50, 10)

    # Amostragem
    if mando_sel == "Geral":
        df_m = df_s[(df_s['Mandante'] == m_sel) | (df_s['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(n_jogos)
        df_v = df_s[(df_s['Mandante'] == v_sel) | (df_s['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(n_jogos)
    else:
        df_m = df_s[df_s['Mandante'] == m_sel].sort_values('Data', ascending=False).head(n_jogos)
        df_v = df_s[df_s['Visitante'] == v_sel].sort_values('Data', ascending=False).head(n_jogos)

    # Abas
    t_resumo, t_detalhe, t_mercado, t_minutos, t_class = st.tabs(["📊 Resumo", "📉 Stats Detalhadas", "💰 Mercados", "⏰ Minutos", "🏆 Tabela"])

    with t_resumo:
        render_stat_row("xG MÉDIO", df_m['xG_Mandante'].mean(), df_v['xG_Visitante'].mean())
        render_stat_row("PONTOS POR JOGO", df_m['PPG_H_Pre'].mean(), df_v['PPG_A_Pre'].mean())
        render_stat_row("CANTOS FT", df_m['Corners_H'].mean(), df_v['Corners_A'].mean())

    with t_detalhe:
        st.subheader(f"Análise Estatística - {m_sel}")
        st.table(criar_tabela_estatistica(df_m, m_sel, "M"))
        st.subheader(f"Análise Estatística - {v_sel}")
        st.table(criar_tabela_estatistica(df_v, v_sel, "V"))

    with t_mercado:
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.write(f"**Incidência {m_sel}**")
            st.dataframe(calcular_incidencia_mercados(df_m, m_sel), hide_index=True)
        with col_m2:
            st.write(f"**Incidência {v_sel}**")
            st.dataframe(calcular_incidencia_mercados(df_v, v_sel), hide_index=True)

    with t_minutos:
        st.subheader("Gols por Faixa de Minutos (Soma)")
        faixas = ['0-15', '16-30', '31-45+', '46-60', '61-75', '76-90+']
        data_min = []
        for f in faixas:
            m_gols = pd.concat([df_m[df_m['Mandante']==m_sel][f'{f}_Mandante'], df_m[df_m['Visitante']==m_sel][f'{f}_Visitante']]).sum()
            v_gols = pd.concat([df_v[df_v['Mandante']==v_sel][f'{f}_Mandante'], df_v[df_v['Visitante']==v_sel][f'{f}_Visitante']]).sum()
            data_min.append({'Intervalo': f, m_sel: int(m_gols), v_sel: int(v_gols)})
        st.table(pd.DataFrame(data_min))

    with t_class:
        # Lógica de Classificação simplificada para performance
        st.write("Tabela de Classificação da Temporada")
        # (Aqui entra a lógica da tabela que já tínhamos)
