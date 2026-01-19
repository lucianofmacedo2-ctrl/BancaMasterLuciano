import streamlit as st
import pandas as pd
from datetime import datetime

def mostrar_scout(df):
    st.title("🔎 Scout de Times")
    if df.empty:
        st.error("Dados não encontrados.")
        return

    # --- 1. FILTROS ---
    c1, c2 = st.columns(2)
    liga = c1.selectbox("Liga", sorted(df['liga'].unique()))
    temp = c2.selectbox("Temporada", sorted(df[df['liga'] == liga]['temporada'].unique(), reverse=True))
    
    df_filt = df[(df['liga'] == liga) & (df['temporada'] == temp)].copy()
    df_filt['data'] = pd.to_datetime(df_filt['data'], errors='coerce')

    times = sorted(df_filt['mandande'].unique())
    c3, c4 = st.columns(2)
    m_sel = c3.selectbox("Mandante", times)
    v_sel = c4.selectbox("Visitante", [t for t in times if t != m_sel])

    # --- 2. ANÁLISE DE FORMA (CASA/FORA E GERAL) ---
    st.divider()
    
    # Abas para organizar as duas visões que você quer
    tab_geral, tab_especifica = st.tabs(["📊 Últimos 10 Jogos (Geral)", "🏠 Últimos 5 (Casa vs Fora)"])

    with tab_geral:
        st.subheader("Forma Geral (Casa & Fora)")
        f1, f2 = st.columns(2)
        df_m_geral = df_filt[(df_filt['mandande'] == m_sel) | (df_filt['visitante'] == m_sel)].sort_values('data', ascending=False).head(10)
        df_v_geral = df_filt[(df_filt['mandande'] == v_sel) | (df_filt['visitante'] == v_sel)].sort_values('data', ascending=False).head(10)
        
        for col, time, dados in [(f1, m_sel, df_m_geral), (f2, v_sel, df_v_geral)]:
            with col:
                st.write(f"**{time}**")
                for _, r in dados.iterrows():
                    is_home = r['mandande'] == time
                    gm, gv = r['gols_mandante_ft'], r['gols_visitante_ft']
                    if gm == gv: res = "🟧"
                    elif (is_home and gm > gv) or (not is_home and gv > gm): res = "✅"
                    else: res = "❌"
                    oponente = r['visitante'] if is_home else r['mandande']
                    st.write(f"{res} {r['data'].strftime('%d/%m')} {'(C)' if is_home else '(F)'} vs {oponente} ({int(gm)}-{int(gv)})")

    with tab_especifica:
        st.subheader("Filtro Específico")
        f3, f4 = st.columns(2)
        df_m_casa = df_filt[df_filt['mandande'] == m_sel].sort_values('data', ascending=False).head(5)
        df_v_fora = df_filt[df_filt['visitante'] == v_sel].sort_values('data', ascending=False).head(5)
        
        with f3:
            st.write(f"**{m_sel} em Casa**")
            for _, r in df_m_casa.iterrows():
                res = "✅" if r['gols_mandante_ft'] > r['gols_visitante_ft'] else ("🟧" if r['gols_mandante_ft'] == r['gols_visitante_ft'] else "❌")
                st.write(f"{res} {r['data'].strftime('%d/%m')} vs {r['visitante']} ({int(r['gols_mandante_ft'])}-{int(r['gols_visitante_ft'])})")
        with f4:
            st.write(f"**{v_sel} Fora**")
            for _, r in df_v_fora.iterrows():
                res = "✅" if r['gols_visitante_ft'] > r['gols_mandante_ft'] else ("🟧" if r['gols_mandante_ft'] == r['gols_visitante_ft'] else "❌")
                st.write(f"{res} {r['data'].strftime('%d/%m')} vs {r['mandande']} ({int(r['gols_mandante_ft'])}-{int(r['gols_visitante_ft'])})")

    # --- 3. ESTATÍSTICAS DETALHADAS (TRATAMENTO DE ERROS) ---
    st.divider()
    st.subheader("📊 Médias: Feitas vs Sofridas")

    # Mapeamento dinâmico para evitar KeyError
    # Buscamos o nome da coluna que contenha as palavras-chave
    def get_col(palavra):
        for c in df_filt.columns:
            if palavra in c: return c
        return None

    metrics = {
        "Gols HT": (get_col("gols_mandante_ht"), get_col("gols_visitante_ht")),
        "Gols FT": (get_col("gols_mandante_ft"), get_col("gols_visitante_ft")),
        "Cantos": (get_col("cantos_mandante"), get_col("cantos_visitante")),
        "Chutes Gol": (get_col("chutes_gol_mandante"), get_col("chutes_gol_visitante")),
        "Finalizações": (get_col("finalizacoes_totais_mandante"), get_col("finalizacoes_totais_visitante"))
    }

    def calc_stats_avancada(time, df_completo):
        res = {}
        df_casa = df_completo[df_completo['mandande'] == time]
        df_fora = df_completo[df_completo['visitante'] == time]
        
        for nome, (col_m, col_v) in metrics.items():
            if col_m and col_v:
                feitos = pd.concat([df_casa[col_m], df_fora[col_v]])
                sofridos = pd.concat([df_casa[col_v], df_fora[col_m]])
                res[f"{nome} (Feitos)"] = feitos.mean()
                res[f"{nome} (Sofridos)"] = sofridos.mean()
        return res

    stats_m = calc_stats_avancada(m_sel, df_filt)
    stats_v = calc_stats_avancada(v_sel, df_filt)

    if stats_m and stats_v:
        df_comp = pd.DataFrame({
            f"{m_sel}": stats_m,
            f"{v_sel}": stats_v
        })
        st.table(df_comp.style.format(precision=2))
    else:
        st.warning("Algumas colunas de estatísticas não foram encontradas no CSV.")
