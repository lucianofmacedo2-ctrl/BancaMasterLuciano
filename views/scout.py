import streamlit as st
import pandas as pd

def mostrar_scout(df):
    st.title("🔎 Scout de Times")
    if df.empty:
        st.error("Dados não encontrados.")
        return

    c1, c2 = st.columns(2)
    pais = c1.selectbox("País", sorted(df['pais'].unique()))
    liga = c2.selectbox("Liga", sorted(df[df['pais'] == pais]['divisao'].unique()))
    
    times = sorted(df[df['divisao'] == liga]['mandante'].unique())
    c3, c4 = st.columns(2)
    m_sel = c3.selectbox("Mandante", times)
    v_sel = c4.selectbox("Visitante", [t for t in times if t != m_sel])

    # Filtros Casa/Fora
    df_m = df[(df['mandante'] == m_sel) & (df['divisao'] == liga)]
    df_v = df[(df['visitante'] == v_sel) & (df['divisao'] == liga)]

    st.subheader("📊 Médias Detalhadas (Alto Contraste)")
    def calcular_medias(data, is_home):
        pre = 'mandante_' if is_home else 'visitante_'
        return {
            "Gols FT": data[f'{pre}gols_mandante_ft' if is_home else f'{pre}gols_visitante_ft'].mean(),
            "Gols HT": data[f'{pre}gols_mandante_ht' if is_home else f'{pre}gols_visitante_ht'].mean(),
            "Cantos": data[f'{pre}cantos'].mean(),
            "Finalizações": data[f'{pre}finalizacoes'].mean(),
            "Chutes ao Gol": data[f'{pre}chute_ao_gol'].mean(),
            "Cartões": data[f'{pre}cartao_amarelo'].mean()
        }

    stats_m = calcular_medias(df_m, True)
    stats_v = calcular_medias(df_v, False)
    
    # Exibição em Tabela (Fonte Branca via CSS)
    df_final = pd.DataFrame({f"{m_sel} (Casa)": stats_m, f"{v_sel} (Fora)": stats_v})
    st.table(df_final.style.format(precision=2))

    # FORMA ÚLTIMOS 5 JOGOS
    st.subheader("📈 Forma (Últimos 5)")
    col_f1, col_f2 = st.columns(2)
    col_f1.write(f"**{m_sel} em Casa:**")
    col_f1.dataframe(df_m.head(5)[['data', 'visitante', 'gols_mandante_ft', 'gols_visitante_ft']], hide_index=True)
    col_f2.write(f"**{v_sel} Fora:**")
    col_f2.dataframe(df_v.head(5)[['data', 'mandante', 'gols_mandante_ft', 'gols_visitante_ft']], hide_index=True)