import streamlit as st
import pandas as pd
import numpy as np

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
    m_sel = c3.selectbox("Mandante (Casa)", times)
    v_sel = c4.selectbox("Visitante (Fora)", [t for t in times if t != m_sel])

    # Bases específicas
    df_m_casa = df_filt[df_filt['mandande'] == m_sel].sort_values('data', ascending=False)
    df_v_fora = df_filt[df_filt['visitante'] == v_sel].sort_values('data', ascending=False)
    
    # --- NOVO: BUSCA DE JOGOS GERAIS (CASA + FORA) ---
    df_m_geral = df_filt[(df_filt['mandande'] == m_sel) | (df_filt['visitante'] == m_sel)].sort_values('data', ascending=False).head(10)
    df_v_geral = df_filt[(df_filt['mandande'] == v_sel) | (df_filt['visitante'] == v_sel)].sort_values('data', ascending=False).head(10)

    # --- 2. FORMA (ÚLTIMOS 10 JOGOS GERAIS) ---
    st.divider()
    st.subheader("📈 Forma Geral (Últimos 10 Jogos - Casa & Fora)")
    f1, f2 = st.columns(2)
    
    for col, time, dados in [(f1, m_sel, df_m_geral), (f2, v_sel, df_v_geral)]:
        with col:
            st.write(f"**{time}**")
            for _, r in dados.iterrows():
                is_home = r['mandande'] == time
                gm, gv = r['gols_mandante_ft'], r['gols_visitante_ft']
                
                # Lógica de Resultado
                if gm == gv: res = "🟧"
                elif (is_home and gm > gv) or (not is_home and gv > gm): res = "✅"
                else: res = "❌"
                
                oponente = r['visitante'] if is_home else r['mandande']
                local = "(C)" if is_home else "(F)"
                st.write(f"{res} {r['data'].strftime('%d/%m')} {local} vs {oponente} ({int(gm)}-{int(gv)})")

    # --- 3. ESTATÍSTICAS DETALHADAS (FEITAS VS SOFRIDAS) ---
    st.divider()
    st.subheader("📊 Estatísticas: Feitas vs Sofridas")
    
    # Mapeamento: (Coluna se for mandante, Coluna se for visitante)
    metrics = {
        "Gols HT": ("gols_mandante_ht", "gols_visitante_ht"),
        "Gols FT": ("gols_mandante_ft", "gols_visitante_ft"),
        "Cantos": ("cantos_mandante", "cantos_visitante"),
        "Chutes ao Gol": ("chutes_gol_mandante", "chutes_gol_visitante"),
        "Finalizações": ("finalizacoes_totais_mandante", "finalizacoes_totais_visitante")
    }

    def calc_stats_avancada(time, df_completo):
        res = {}
        # Jogos em casa para o time
        df_casa = df_completo[df_completo['mandande'] == time]
        # Jogos fora para o time
        df_fora = df_completo[df_completo['visitante'] == time]
        
        for nome, (col_m, col_v) in metrics.items():
            # Feitos: Mandante em casa + Visitante fora
            feitos = pd.concat([df_casa[col_m], df_fora[col_v]])
            # Sofridos: Visitante jogando na casa dele + Mandante jogando fora
            sofridos = pd.concat([df_casa[col_v], df_fora[col_m]])
            
            res[f"{nome} (Feito)"] = feitos.mean()
            res[f"{nome} (Sofrido)"] = sofridos.mean()
        return res

    stats_m = calc_stats_avancada(m_sel, df_filt)
    stats_v = calc_stats_avancada(v_sel, df_filt)

    # Tabela comparativa
    df_comparativo = pd.DataFrame({
        "Métrica": stats_m.keys(),
        f"{m_sel} (Média)": stats_m.values(),
        f"{v_sel} (Média)": stats_v.values()
    }).set_index("Métrica")

    st.table(df_comparativo.style.format(precision=2))
