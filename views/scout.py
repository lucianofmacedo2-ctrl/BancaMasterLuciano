import streamlit as st
import pandas as pd
import numpy as np

# --- DICIONÁRIO DE REGRAS ---
REGRAS_LIGAS = {
    "BRAZIL 1": {"times": 20, "rodadas": 38, "alvos": {"Libertadores": [1, 6], "Rebaixamento": [17, 20]}},
    "PORTUGAL 3": {"times": 20, "rodadas": 26, "alvos": {"Acesso": [1, 2]}},
    "ENGLAND 1": {"times": 20, "rodadas": 38, "alvos": {"Champions League": [1, 4]}},
}

def render_stat_row(label, val_home, val_away):
    col1, col2, col3 = st.columns([1, 2, 1])
    v_h = float(val_home) if pd.notnull(val_home) else 0.0
    v_a = float(val_away) if pd.notnull(val_away) else 0.0
    total = abs(v_h) + abs(v_a)
    p_home = (v_h / total) if total > 0 else 0.5
    with col1: st.markdown(f"<p style='text-align: right; font-size: 18px; font-weight: bold; margin:0;'>{v_h:.2f}</p>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<p style='text-align: center; font-size: 11px; color: gray; margin:0;'>{label}</p>", unsafe_allow_html=True)
        st.progress(max(0.0, min(1.0, float(p_home))))
    with col3: st.markdown(f"<p style='text-align: left; font-size: 18px; font-weight: bold; margin:0;'>{v_a:.2f}</p>", unsafe_allow_html=True)

def mostrar_scout(df):
    st.title("🔎 Scout Profissional")

    if df.empty:
        st.warning("Nenhum dado encontrado no CSV.")
        return

    # Forçar detecção de todas as ligas
    df['Liga'] = df['Liga'].astype(str).str.strip()
    listagem_ligas = sorted(df['Liga'].unique().tolist())

    # Barra lateral de diagnóstico para conferir se Portugal 3 entrou
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔎 Detalhes do Arquivo")
    st.sidebar.write(f"Ligas detectadas: {len(listagem_ligas)}")
    
    if "PORTUGAL 3" in listagem_ligas:
        st.sidebar.success("✅ PORTUGAL 3 disponível!")
    else:
        st.sidebar.error("❌ PORTUGAL 3 não encontrada no CSV.")

    c1, c2 = st.columns(2)
    liga_sel = c1.selectbox("Selecione a Liga", listagem_ligas)
    
    df_liga = df[df['Liga'] == liga_sel].copy()
    temps = sorted(df_liga['Temporada'].astype(str).unique().tolist(), reverse=True)
    temp_sel = c2.selectbox("Temporada", temps)
    
    df_s = df_liga[df_liga['Temporada'].astype(str) == temp_sel].copy()
    df_s['Data'] = pd.to_datetime(df_s['Data'], errors='coerce')
    
    times = sorted(df_s['Mandante'].unique().tolist())
    
    if len(times) < 2:
        st.info("Selecione uma liga com jogos registrados.")
        return

    m_sel = st.selectbox("Time Mandante", times)
    v_sel = st.selectbox("Time Visitante", [t for t in times if t != m_sel])

    # Filtragem de Formas
    df_m = df_s[(df_s['Mandante'] == m_sel) | (df_s['Visitante'] == m_sel)].sort_values('Data', ascending=False).head(10)
    df_v = df_s[(df_s['Mandante'] == v_sel) | (df_s['Visitante'] == v_sel)].sort_values('Data', ascending=False).head(10)

    st.divider()
    st.subheader(f"📊 {m_sel} vs {v_sel}")

    # Médias de Gols
    avg_m = np.where(df_m['Mandante'] == m_sel, df_m['Gols_Mandante_FT'], df_m['Gols_Visitante_FT']).mean()
    avg_v = np.where(df_v['Mandante'] == v_sel, df_v['Gols_Mandante_FT'], df_v['Gols_Visitante_FT']).mean()
    render_stat_row("MÉDIA GOLS MARCADOS", avg_m, avg_v)

    # Abas
    t1, t2, t3 = st.tabs(["🕒 Últimos Jogos", "⚔️ Confrontos Diretos", "📊 Estatísticas"])
    
    with t1:
        col_m, col_v = st.columns(2)
        col_m.write(f"Últimos 10 de {m_sel}")
        col_m.dataframe(df_m[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], hide_index=True)
        col_v.write(f"Últimos 10 de {v_sel}")
        col_v.dataframe(df_v[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], hide_index=True)

    with t2:
        h2h = df[((df['Mandante'] == m_sel) & (df['Visitante'] == v_sel)) | ((df['Mandante'] == v_sel) & (df['Visitante'] == m_sel))].sort_values('Data', ascending=False)
        if not h2h.empty:
            st.dataframe(h2h[['Data', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante']], use_container_width=True, hide_index=True)
        else:
            st.write("Nenhum confronto direto recente.")

    with t3:
        st.table(df_m[['Gols_Mandante_FT', 'Gols_Visitante_FT', 'Total_Gols_FT']].describe().T)
