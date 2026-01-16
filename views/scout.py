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
    m_sel = c3.selectbox("Mandante (Casa)", times)
    v_sel = c4.selectbox("Visitante (Fora)", [t for t in times if t != m_sel])

    # Filtros e conversão de data para garantir que a Forma funcione
    df['data'] = pd.to_datetime(df['data'], errors='coerce')
    df_m = df[(df['mandante'] == m_sel) & (df['divisao'] == liga)].sort_values('data', ascending=False)
    df_v = df[(df['visitante'] == v_sel) & (df['divisao'] == liga)].sort_values('data', ascending=False)

    st.subheader("📊 Médias Detalhadas")

    def calcular_medias(data, is_home):
        if data.empty: return {k: 0 for k in ["Gols FT", "Gols HT", "Cantos", "Finalizações", "Chutes", "Cartões"]}
        if is_home:
            return {
                "Gols FT": data['gols_mandante_ft'].mean(),
                "Gols HT": data['gols_mandante_ht'].mean(),
                "Cantos": data['mandante_cantos'].mean(),
                "Finalizações": data['mandante_finalizacoes'].mean(),
                "Chutes": data['mandante_chute_ao_gol'].mean(),
                "Cartões": data['mandante_cartao_amarelo'].mean()
            }
        else:
            return {
                "Gols FT": data['gols_visitante_ft'].mean(),
                "Gols HT": data['gols_visitante_ht'].mean(),
                "Cantos": data['visitante_cantos'].mean(),
                "Finalizações": data['visitante_finalizacoes'].mean(),
                "Chutes": data['visitante_chute_ao_gol'].mean(),
                "Cartões": data['visitante_cartao_amarelo'].mean()
            }

    stats_m = calcular_medias(df_m, True)
    stats_v = calcular_medias(df_v, False)
    
    df_final = pd.DataFrame({
        "Estatística": stats_m.keys(),
        f"{m_sel} (Casa)": stats_m.values(),
        f"{v_sel} (Fora)": stats_v.values()
    }).set_index("Estatística")

    # CENTRALIZAÇÃO DA TABELA E FONTE BRANCA
    st.markdown("""
        <style>
            div[data-testid="stTable"] td { text-align: center !important; vertical-align: middle !important; }
            div[data-testid="stTable"] th { text-align: center !important; }
        </style>
    """, unsafe_allow_html=True)
    
    st.table(df_final.style.format(precision=2))

    # --- SEÇÃO DA FORMA (REVISADA) ---
    st.divider()
    st.subheader("📈 Forma Recente (Últimos 5 Jogos)")
    col_f1, col_f2 = st.columns(2)
    
    with col_f1:
        st.write(f"**{m_sel}** em Casa")
        # Garante que estamos pegando apenas jogos onde ele foi mandante
        u5_casa = df_m.head(5)
        if not u5_casa.empty:
            for _, r in u5_casa.iterrows():
                res = "✅" if r['gols_mandante_ft'] > r['gols_visitante_ft'] else ("🟧" if r['gols_mandante_ft'] == r['gols_visitante_ft'] else "❌")
                data_str = r['data'].strftime('%d/%m') if pd.notnull(r['data']) else "S/D"
                st.write(f"{res} {data_str} vs {r['visitante']} ({int(r['gols_mandante_ft'])} - {int(r['gols_visitante_ft'])})")
        else: st.info("Sem dados.")

    with col_f2:
        st.write(f"**{v_sel}** Fora")
        # Garante que estamos pegando apenas jogos onde ele foi visitante
        u5_fora = df_v.head(5)
        if not u5_fora.empty:
            for _, r in u5_fora.iterrows():
                res = "✅" if r['gols_visitante_ft'] > r['gols_mandante_ft'] else ("🟧" if r['gols_visitante_ft'] == r['gols_mandante_ft'] else "❌")
                data_str = r['data'].strftime('%d/%m') if pd.notnull(r['data']) else "S/D"
                st.write(f"{res} {data_str} @ {r['mandante']} ({int(r['gols_mandante_ft'])} - {int(r['gols_visitante_ft'])})")
        else: st.info("Sem dados.")
