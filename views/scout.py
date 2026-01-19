import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats

def mostrar_scout(df):
    st.title("🔎 Scout Estatístico Avançado")
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
    m_sel = c3.selectbox("Mandante (Casa)", times)
    v_sel = c4.selectbox("Visitante (Fora)", [t for t in times if t != m_sel])

    # --- 2. FORMA (ABAS) ---
    tab_geral, tab_especifica = st.tabs(["📊 Últimos 10 Geral", "🏠 Forma Local (Casa/Fora)"])
    
    with tab_geral:
        # (Código de forma geral mantido conforme funcionalidade anterior)
        st.write("Exibindo últimos 10 jogos gerais...")
        # ... (lógica dos 10 jogos)

    with tab_especifica:
        st.subheader(f"Desempenho Específico")
        f3, f4 = st.columns(2)
        df_m_casa = df_filt[df_filt['mandande'] == m_sel].sort_values('data', ascending=False).head(10)
        df_v_fora = df_filt[df_filt['visitante'] == v_sel].sort_values('data', ascending=False).head(10)
        # ... (exibição da lista de jogos)

    # --- 3. ESTATÍSTICAS DETALHADAS (MÉDIAS, MEDIANAS, ETC) ---
    st.divider()
    st.subheader("📊 Análise Estatística Profissional")
    st.caption("Baseado no Mandante jogando em Casa e Visitante jogando Fora")

    def get_col(palavra):
        for c in df_filt.columns:
            if palavra in c.lower(): return c
        return None

    # Mapeamento das colunas solicitadas
    metrics_map = {
        "Gols HT": (get_col("gols_mandante_ht"), get_col("gols_visitante_ht")),
        "Gols FT": (get_col("gols_mandante_ft"), get_col("gols_visitante_ft")),
        "Cantos": (get_col("cantos_mandante"), get_col("cantos_visitante")),
        "Chutes Gol": (get_col("chutes_gol_mandante"), get_col("chutes_gol_visitante")),
        "Chutes Fora": (get_col("chutes_fora_mandante"), get_col("chutes_fora_visitante"))
    }

    def calcular_metricas_completas(dados):
        if dados.empty: return {}
        try:
            media = dados.mean()
            mediana = dados.median()
            moda = stats.mode(dados, keepdims=True).mode[0] if not dados.empty else 0
            desvio = dados.std()
            cv = (desvio / media) * 100 if media > 0 else 0
            return {
                "Média": media,
                "Mediana": mediana,
                "Moda": moda,
                "Desvio P.": desvio,
                "CV (%)": cv
            }
        except:
            return {"Média": 0, "Mediana": 0, "Moda": 0, "Desvio P.": 0, "CV (%)": 0}

    # Processamento para Mandante (CASA) e Visitante (FORA)
    # Mandante: Feito (col_m), Sofrido (col_v)
    # Visitante: Feito (col_v), Sofrido (col_m)
    
    for label, (col_m, col_v) in metrics_map.items():
        if col_m and col_v:
            st.write(f"#### {label}")
            col_res1, col_res2 = st.columns(2)
            
            with col_res1:
                st.markdown(f"**{m_sel} (Em Casa)**")
                m_feitos = calcular_metricas_completas(df_m_casa[col_m])
                m_sofridos = calcular_metricas_completas(df_m_casa[col_v])
                
                df_m_table = pd.DataFrame([m_feitos, m_sofridos], index=["Feitos", "Sofridos"])
                st.dataframe(df_m_table.style.format(precision=2), use_container_width=True)

            with col_res2:
                st.markdown(f"**{v_sel} (Fora)**")
                v_feitos = calcular_metricas_completas(df_v_fora[col_v])
                v_sofridos = calcular_metricas_completas(df_v_fora[col_m])
                
                df_v_table = pd.DataFrame([v_feitos, v_sofridos], index=["Feitos", "Sofridos"])
                st.dataframe(df_v_table.style.format(precision=2), use_container_width=True)
            st.divider()
