import streamlit as st
import pandas as pd
import numpy as np

def mostrar_scout(df):
    st.title("🔎 Scout Avançado")
    if df.empty:
        st.error("Dados não encontrados.")
        return

    # --- 1. FILTROS (LIGA -> TEMPORADA -> MANDANTE/VISITANTE) ---
    c1, c2 = st.columns(2)
    liga = c1.selectbox("Liga", sorted(df['Liga'].unique()))
    temp = c2.selectbox("Temporada", sorted(df[df['Liga'] == liga]['Temporada'].unique(), reverse=True))
    
    df_filt = df[(df['Liga'] == liga) & (df['Temporada'] == temp)].copy()
    df_filt['Data'] = pd.to_datetime(df_filt['Data'], errors='coerce')

    times = sorted(df_filt['Mandande'].unique())
    c3, c4 = st.columns(2)
    m_sel = c3.selectbox("Mandante (Casa)", times)
    v_sel = c4.selectbox("Visitante (Fora)", [t for t in times if t != m_sel])

    # Bases específicas: Mandante em Casa e Visitante Fora
    df_m = df_filt[df_filt['Mandande'] == m_sel].sort_values('Data', ascending=False)
    df_v = df_filt[df_filt['Visitante'] == v_sel].sort_values('Data', ascending=False)

    # --- CSS PARA ALTO CONTRASTE ---
    st.markdown("""
        <style>
            div[data-testid="stTable"] td, div[data-testid="stTable"] th { 
                text-align: center !important; color: white !important; font-size: 1rem !important;
            }
            .stMetricLabel p { color: white !important; font-weight: bold !important; }
        </style>
    """, unsafe_allow_html=True)

    # --- 2. % VITÓRIA, EMPATE, DERROTA ---
    st.subheader("🎯 Probabilidades Históricas (Cenário Casa/Fora)")
    def calc_ved(dados, is_home):
        if dados.empty: return 0, 0, 0
        total = len(dados)
        v = len(dados[dados['Gols_Mandante_FT'] > dados['Gols_Visitante_FT']]) if is_home else len(dados[dados['Gols_Visitante_FT'] > dados['Gols_Mandante_FT']])
        e = len(dados[dados['Gols_Mandante_FT'] == dados['Gols_Visitante_FT']])
        d = total - v - e
        return (v/total)*100, (e/total)*100, (d/total)*100

    v_m, e_m, d_m = calc_ved(df_m, True)
    v_v, e_v, d_v = calc_ved(df_v, False)

    col_v1, col_v2 = st.columns(2)
    col_v1.write(f"**{m_sel} (Casa):** ✅ {v_m:.1f}% | 🟧 {e_m:.1f}% | ❌ {d_m:.1f}%")
    col_v2.write(f"**{v_sel} (Fora):** ✅ {v_v:.1f}% | 🟧 {e_v:.1f}% | ❌ {d_v:.1f}%")

    # --- 3. FORMA RECENTE ---
    st.divider()
    st.subheader("📈 Forma (Últimos 5 Jogos no Cenário)")
    f1, f2 = st.columns(2)
    for col, time, dados, is_m in [(f1, m_sel, df_m, True), (f2, v_sel, df_v, False)]:
        with col:
            st.write(f"**{time}**")
            for _, r in dados.head(5).iterrows():
                gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
                if is_m: res = "✅" if gm > gv else ("🟧" if gm == gv else "❌")
                else: res = "✅" if gv > gm else ("🟧" if gm == gv else "❌")
                odd = r.get('Odd_Mandante_FT' if is_m else 'Odd_Visitante_FT', 'N/A')
                st.write(f"{res} {r['Data'].strftime('%d/%m') if pd.notnull(r['Data']) else 'S/D'} vs {r['Visitante'] if is_m else r['Mandande']} ({int(gm)}-{int(gv)}) **@{odd}**")

    # --- 4. MÉTRICAS ESTATÍSTICAS COMPLETAS ---
    st.divider()
    st.subheader("📊 Estatísticas Detalhadas")
    
    cols_analise = {
        "Gols HT": ("Total_Gols_HT", "Total_Gols_HT"),
        "Gols FT": ("Total_Gols_FT", "Total_Gols_FT"),
        "Cantos": ("Cantos_Mandante", "Cantos_Visitante"),
        "Chutes ao Gol": ("Chutes_Gol_Mandante", "Chutes_Gol_Visitante"),
        "Chutes Fora": ("Chutes_Fora_Mandante", "Chutes_Fora_Visitante"),
        "Finalizações": ("Finalizações_Totais_Mandante", "Finalizações_Totais_Visitante")
    }

    def extrair_stats(dados, col_name):
        s = dados[col_name].replace(0, np.nan).dropna() # Evita erro em modas/cv
        if s.empty: return [0]*6
        mean = s.mean()
        std = s.std()
        return [
            mean, 
            s.median(), 
            s.mode().iloc[0] if not s.mode().empty else 0,
            (std / mean) if mean != 0 else 0, # CV
            std
        ]

    res_m = {k: extrair_stats(df_m, v[0]) for k, v in cols_analise.items()}
    res_v = {k: extrair_stats(df_v, v[1]) for k, v in cols_analise.items()}

    df_estat = pd.DataFrame({
        "Métrica": ["Média", "Mediana", "Moda", "Coef. Var.", "Desv. Padrão"],
        **{f"{m_sel} {k}": res_m[k] for k in cols_analise},
        **{f"{v_sel} {k}": res_v[k] for k in cols_analise}
    }).set_index("Métrica")
    
    st.table(df_estat.style.format(precision=2))

    # --- 5. INCIDÊNCIA DE GOLS (%) ---
    st.divider()
    st.subheader("⚽ Tendência de Gols (Over)")
    
    def calc_over(dados, limites, col):
        if dados.empty: return [0]*len(limites)
        return [(len(dados[dados[col] > lim]) / len(dados)) * 100 for lim in limites]

    limites_ht = [0.5, 1.5, 2.5, 3.5]
    limites_ft = [0.5, 1.5, 2.5, 3.5]

    over_ht_m = calc_over(df_m, limites_ht, 'Total_Gols_HT')
    over_ft_m = calc_over(df_m, limites_ft, 'Total_Gols_FT')
    over_ht_v = calc_over(df_v, limites_ht, 'Total_Gols_HT')
    over_ft_v = calc_over(df_v, limites_ft, 'Total_Gols_FT')

    df_over = pd.DataFrame({
        "Linha": ["+0.5", "+1.5", "+2.5", "+3.5"],
        f"HT {m_sel}": [f"{x:.1f}%" for x in over_ht_m],
        f"FT {m_sel}": [f"{x:.1f}%" for x in over_ft_m],
        f"HT {v_sel}": [f"{x:.1f}%" for x in over_ht_v],
        f"FT {v_sel}": [f"{x:.1f}%" for x in over_ft_v]
    }).set_index("Linha")
    st.table(df_over)

    # --- 6. GOLS POR FAIXA DE MINUTOS ---
    st.divider()
    st.subheader("⏱️ Distribuição de Gols por Minutos")
    faixas = ['0-15', '16-30', '31-45+', '46-60', '61-75', '76-90+']
    
    def get_minutos(dados, sufixo):
        cols = [f"{f}_{sufixo}" for f in faixas]
        existentes = [c for c in cols if c in dados.columns]
        if not existentes: return [0]*6
        total_gols = dados[existentes].sum().sum()
        if total_gols == 0: return [0]*6
        return [(dados[c].sum() / total_gols) * 100 for c in existentes]

    min_m = get_minutos(df_m, "Mandante")
    min_v = get_minutos(df_v, "Visitante")

    df_minutos = pd.DataFrame({
        "Minutos": faixas,
        f"{m_sel} (Gols Feitos)": [f"{x:.1f}%" for x in min_m],
        f"{v_sel} (Gols Feitos)": [f"{x:.1f}%" for x in min_v]
    }).set_index("Minutos")
    st.table(df_minutos)
