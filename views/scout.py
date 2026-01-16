import streamlit as st
import pandas as pd

def mostrar_scout(df):
    st.title("🔎 Scout de Times")
    if df.empty:
        st.error("Dados não encontrados.")
        return

    # --- LÓGICA DE RANKING (EM TEMPO REAL) ---
    def calcular_classificacao(dados, filtro=None):
        stats = {}
        for _, r in dados.iterrows():
            m, v = r['mandante'], r['visitante']
            gm, gv = r['gols_mandante_ft'], r['gols_visitante_ft']
            
            for time in [m, v]:
                if time not in stats: stats[time] = {'pts': 0, 'j': 0}
            
            # Filtro para Ranking Casa ou Fora
            if filtro == 'casa' and m in stats:
                stats[m]['j'] += 1
                if gm > gv: stats[m]['pts'] += 3
                elif gm == gv: stats[m]['pts'] += 1
            elif filtro == 'fora' and v in stats:
                stats[v]['j'] += 1
                if gv > gm: stats[v]['pts'] += 3
                elif gm == gv: stats[v]['pts'] += 1
            elif filtro is None:
                stats[m]['j'] += 1; stats[v]['j'] += 1
                if gm > gv: stats[m]['pts'] += 3
                elif gv > gm: stats[v]['pts'] += 3
                else: stats[m]['pts'] += 1; stats[v]['pts'] += 1

        df_rank = pd.DataFrame.from_dict(stats, orient='index')
        df_rank = df_rank[df_rank['j'] > 0] # Remove times sem jogos no filtro
        df_rank = df_rank.sort_values(by=['pts'], ascending=False)
        df_rank['pos'] = range(1, len(df_rank) + 1)
        return df_rank['pos'].to_dict()

    # --- SELEÇÃO DE TIMES ---
    c1, c2 = st.columns(2)
    pais = c1.selectbox("País", sorted(df['pais'].unique()))
    liga = c2.selectbox("Liga", sorted(df[df['pais'] == pais]['divisao'].unique()))
    
    df_liga = df[df['divisao'] == liga].copy()
    rank_geral = calcular_classificacao(df_liga)
    rank_casa = calcular_classificacao(df_liga, 'casa')
    rank_fora = calcular_classificacao(df_liga, 'fora')

    times = sorted(df_liga['mandante'].unique())
    c3, c4 = st.columns(2)
    m_sel = c3.selectbox("Mandante (Casa)", times)
    v_sel = c4.selectbox("Visitante (Fora)", [t for t in times if t != m_sel])

    # --- CARDS DE POSIÇÃO ---
    st.markdown("### 🏆 Classificação")
    cp1, cp2 = st.columns(2)
    
    with cp1: # Mandante
        st.markdown(f"**{m_sel}**")
        col1, col2 = st.columns(2)
        col1.metric("Posição Geral", f"{rank_geral.get(m_sel, 'N/A')}º")
        col2.metric("Como Mandante", f"{rank_casa.get(m_sel, 'N/A')}º")

    with cp2: # Visitante
        st.markdown(f"**{v_sel}**")
        col1, col2 = st.columns(2)
        col1.metric("Posição Geral", f"{rank_geral.get(v_sel, 'N/A')}º")
        col2.metric("Como Visitante", f"{rank_fora.get(v_sel, 'N/A')}º")

    # --- MÉDIAS DETALHADAS ---
    st.divider()
    df_m = df_liga[df_liga['mandante'] == m_sel].sort_values('data', ascending=False)
    df_v = df_liga[df_liga['visitante'] == v_sel].sort_values('data', ascending=False)

    def calcular_medias(data, is_home):
        if data.empty: return {k: 0 for k in ["Gols FT", "Gols HT", "Cantos", "Chutes", "Cartões"]}
        pre = 'mandante_' if is_home else 'visitante_'
        return {
            "Gols FT": data[f'gols_{pre}ft'].mean(),
            "Gols HT": data[f'gols_{pre}ht'].mean(),
            "Cantos": data[f'{pre}cantos'].mean(),
            "Chutes": data[f'{pre}chute_ao_gol'].mean(),
            "Cartões": data[f'{pre}cartao_amarelo'].mean()
        }

    stats_m = calcular_medias(df_m, True)
    stats_v = calcular_medias(df_v, False)
    
    df_tab = pd.DataFrame({"Estatística": stats_m.keys(), f"{m_sel} (Casa)": stats_m.values(), f"{v_sel} (Fora)": stats_v.values()}).set_index("Estatística")

    st.markdown("<style>div[data-testid='stTable'] td { text-align: center !important; }</style>", unsafe_allow_html=True)
    st.table(df_tab.style.format(precision=2))

    # --- FORMA RECENTE ---
    st.subheader("📈 Forma Recente (Últimos 5 Jogos)")
    cf1, cf2 = st.columns(2)
    
    for col, time, data_f, is_m in [(cf1, m_sel, df_m, True), (cf2, v_sel, df_v, False)]:
        with col:
            st.write(f"**{time}** {'em Casa' if is_m else 'Fora'}")
            for _, r in data_f.head(5).iterrows():
                gm, gv = r['gols_mandante_ft'], r['gols_visitante_ft']
                if is_m: res = "✅" if gm > gv else ("🟧" if gm == gv else "❌")
                else: res = "✅" if gv > gm else ("🟧" if gm == gv else "❌")
                st.write(f"{res} {r['data'].strftime('%d/%m')} vs {r['visitante'] if is_m else r['mandante']} ({int(gm)} - {int(gv)})")
