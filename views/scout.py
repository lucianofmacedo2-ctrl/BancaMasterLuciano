import streamlit as st
import pandas as pd
import plotly.express as px

def mostrar_scout(df):
    st.title("🔎 Scout Estatístico")

    # Mapeamento dinâmico para evitar KeyError/TypeError
    cols = {c.lower(): c for c in df.columns}
    def get_col(name, default): return cols.get(name.lower(), default)

    c_liga = get_col('Liga', 'Liga')
    c_mand = get_col('Mandande', 'Mandande')
    c_visi = get_col('Visitante', 'Visitante')
    c_data = get_col('Data', 'Data')
    c_gm_ft = get_col('Gols_Mandante_FT', 'Gols_Mandante_FT')
    c_gv_ft = get_col('Gols_Visitante_FT', 'Gols_Visitante_FT')

    # Filtros
    c1, c2 = st.columns(2)
    liga = c1.selectbox("Selecione a Liga", sorted(df[c_liga].unique()))
    df_liga = df[df[c_liga] == liga].copy()
    
    times = sorted(df_liga[c_mand].unique())
    time_m = c1.selectbox("Mandante", times)
    time_v = c2.selectbox("Visitante", [t for t in times if t != time_m])

    # Bases de dados (últimos 10 jogos)
    df_m = df_liga[df_liga[c_mand] == time_m].tail(10)
    df_v = df_liga[df_liga[c_visi] == time_v].tail(10)

    st.divider()

    # Gráficos de Faixa de Minutos
    st.subheader("⏰ Gols por Faixa de Minutos (%)")
    faixas = ["0-15", "16-30", "31-45", "46-60", "61-75", "76-90"]
    
    # Exemplo para Mandante (ajuste os nomes das colunas de faixa conforme seu CSV)
    cols_m = [get_col(f"{f}_Mandante", f"{f}_Mandante") for f in faixas]
    cols_v = [get_col(f"{f}_Visitante", f"{f}_Visitante") for f in faixas]

    c_g1, c_g2 = st.columns(2)
    with c_g1:
        st.write(f"**{time_m} (Casa)**")
        if all(col in df.columns for col in cols_m):
            val_m = df_m[cols_m].mean() * 100
            fig_m = px.bar(x=faixas, y=val_m, labels={'x':'Minutos', 'y':'%'}, color_discrete_sequence=['#0088ff'])
            st.plotly_chart(fig_m, use_container_width=True)

    with c_g2:
        st.write(f"**{time_v} (Fora)**")
        if all(col in df.columns for col in cols_v):
            val_v = df_v[cols_v].mean() * 100
            fig_v = px.bar(x=faixas, y=val_v, labels={'x':'Minutos', 'y':'%'}, color_discrete_sequence=['#ff4444'])
            st.plotly_chart(fig_v, use_container_width=True)

    # Confronto Direto (H2H)
    st.subheader("⚔️ Confronto Direto (H2H)")
    h2h = df[((df[c_mand] == time_m) & (df[c_visi] == time_v)) | 
             ((df[c_mand] == time_v) & (df[c_visi] == time_m))].tail(5)
    
    if not h2h.empty:
        for _, row in h2h.iterrows():
            st.write(f"📅 {row[c_data]} | {row[c_mand]} {int(row[c_gm_ft])} x {int(row[c_gv_ft])} {row[c_visi]}")
    else:
        st.info("Nenhum confronto direto recente encontrado.")
