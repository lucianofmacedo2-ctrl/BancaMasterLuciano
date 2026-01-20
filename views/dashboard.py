import streamlit as st
import pandas as pd
import plotly.express as px
from database import carregar_apostas

def mostrar_dashboard(banca_inicial):
    st.title("📊 Desempenho Estatístico")
    df = carregar_apostas()
    
    df_res = df[df['resultado'] != 'Aberto'].copy()
    if df_res.empty:
        st.warning("Sem dados suficientes para o gráfico.")
        return

    lucro_total = df_res['lucro_prejuizo'].sum()
    banca_atual = banca_inicial + lucro_total

    c1, c2, c3 = st.columns(3)
    c1.metric("Banca Atual", f"R$ {banca_atual:.2f}")
    c2.metric("Lucro Total", f"R$ {lucro_total:.2f}", delta=f"{lucro_total:.2f}")
    c3.metric("ROI %", f"{(lucro_total / df_res['stake'].sum() * 100):.2f}%")

    st.subheader("📈 Evolução do Patrimônio")
    df_res['acumulado'] = banca_inicial + df_res['lucro_prejuizo'].cumsum()
    fig = px.line(df_res, y='acumulado', title="Crescimento da Banca", markers=True)
    st.plotly_chart(fig, use_container_width=True)
