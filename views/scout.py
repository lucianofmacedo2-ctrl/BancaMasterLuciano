import streamlit as st
import pandas as pd
import numpy as np

def mostrar_scout(df):
    st.title("🔎 Scout Avançado")
    if df.empty:
        st.error("Dados não encontrados no arquivo CSV.")
        return

    # --- 1. FILTROS (Padronizados para minúsculas conforme database.py) ---
    c1, c2 = st.columns(2)
    # A coluna 'Liga' vira 'liga'
    liga_list = sorted(df['liga'].unique()) if 'liga' in df.columns else []
    liga = c1.selectbox("Liga", liga_list)
    
    # A coluna 'Temporada' vira 'temporada'
    temp_list = sorted(df[df['liga'] == liga]['temporada'].unique(), reverse=True) if 'temporada' in df.columns else []
    temp = c2.selectbox("Temporada", temp_list)
    
    df_filt = df[(df['liga'] == liga) & (df['temporada'] == temp)].copy()
    df_filt['data'] = pd.to_datetime(df_filt['data'], errors='coerce')

    # 'Mandande' vira 'mandande'
    times = sorted(df_filt['mandande'].unique()) if 'mandande' in df.columns else []
    c3, c4 = st.columns(2)
    m_sel = c3.selectbox("Mandante (Casa)", times)
    v_sel = c4.selectbox("Visitante (Fora)", [t for t in times if t != m_sel])

    # Bases específicas: Mandante em Casa e Visitante Fora
    df_m = df_filt[df_filt['mandande'] == m_sel].sort_values('data', ascending=False)
    df_v = df_filt[df_filt['visitante'] == v_sel].sort_values('data', ascending=False)

    # --- CSS PARA ALTO CONTRASTE ---
    st.markdown("""
        <style>
            div[data-testid="stTable"] td, div[data-testid="stTable"] th { 
                text-align: center !important; color: white !important; font-size: 1rem !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- 2. % VITÓRIA, EMPATE, DERROTA ---
    st.subheader("🎯 Probabilidades Históricas (Cenário Casa/Fora)")
    def calc_ved(dados, is_home):
        if dados.empty: return 0, 0, 0
        total = len(dados)
        v = len(dados[dados['gols_mandante_ft'] > dados['gols_visitante_ft']]) if is_home else len(dados[dados['gols_visitante_ft'] > dados['gols_mandante_ft']])
        e = len(dados[dados['gols_mandante_ft'] == dados['gols_visitante_ft']])
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
                gm, gv = r['gols_mandante_ft'], r['gols_visitante_ft']
                if is_m: res = "✅" if gm > gv else ("🟧" if gm == gv else "❌")
                else: res = "✅" if gv > gm else ("🟧" if gm == gv else "❌")
                odd = r.get('odd_mandante_ft' if is_m else 'odd_visitante_ft', 'N/A')
                st.write(f"{res} {r['data'].strftime('%d/%m') if pd.notnull(r['data']) else 'S/D'} vs {r['visitante'] if is_m else r['mandande']} ({int(gm)}-{int(gv)}) **@{odd}**")

    # --- 4. MÉTRICAS ESTATÍSTICAS COMPLETAS ---
    st.divider()
    st.subheader("📊 Estatísticas Detalhadas")
    
    cols_analise = {
        "Gols HT": ("total_gols_ht", "total_gols_ht"),
        "Gols FT": ("total_gols_ft", "total_gols_ft"),
        "Cantos": ("cantos_mandante", "cantos_visitante"),
        "Chutes ao Gol": ("chutes_gol_mandante", "chutes_gol_visitante"),
        "Chutes Fora": ("chutes_fora_mandante", "chutes_fora_visitante"),
        "Finalizações": ("finalizacoes_totais_mandante", "finalizacoes_totais_visitante")
    }

    def extrair_stats(dados, col_name):
        if col_name not in dados.columns: return [0]*5
        s = pd.to_numeric(dados[col_name], errors='coerce').dropna()
        if s.empty: return [0]*5
        mean = s.mean()
        std = s.std()
        return [mean, s.median(), s.mode().iloc[0] if not s.mode().empty else 0, (std / mean) if mean != 0 else 0, std]

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
        if col not in dados.columns or dados.empty: return [0]*len(limites)
        return [(len(dados[dados[col] > lim]) / len(dados)) * 100 for lim in limites]

    limites = [0.5, 1.5, 2.5, 3.5]
    over_ht_m = calc_over(df_m, limites, 'total_gols_ht')
    over_ft_m = calc_over(df_m, limites, 'total_gols_ft')
    over_ht_v = calc_over(df_v, limites, 'total_gols_ht')
    over_ft_v = calc_over(df_v, limites, 'total_gols_ft')

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
    
    def get_minutos(dados, time_type):
        cols = [f"{f}_{time_type.lower()}" for f in faixas]
        existentes = [c for c in cols if c in dados.columns]
        if not existentes: return [0]*6
        total = dados[existentes].sum().sum()
        return [(dados[c].sum() / total * 100) if total > 0 else 0 for c in existentes]

    min_m = get_minutos(df_m, "Mandante")
    min_v = get_minutos(df_v, "Visitante")

    df_min = pd.DataFrame({
        "Minutos": faixas,
        f"{m_sel}": [f"{x:.1f}%" for x in min_m],
        f"{v_sel}": [f"{x:.1f}%" for x in min_v]
    }).set_index("Minutos")
    st.table(df_min)
