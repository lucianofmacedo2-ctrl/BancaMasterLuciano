import streamlit as st
import pandas as pd
import plotly.express as px
from database import carregar_apostas

def mostrar_dashboard(banca_inicial):
    st.title("📊 Análise de Performance")
    df = carregar_apostas()
    
    if df.empty or len(df[df['resultado'] != 'Aberto']) == 0:
        st.warning("Sem dados para exibir o gráfico.")
        return

    df_res = df[df['resultado'] != 'Aberto'].copy()
    lucro = df_res['lucro_prejuizo'].sum()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Banca Atual", f"R$ {banca_inicial + lucro:.2f}")
    c2.metric("Lucro Total", f"R$ {lucro:.2f}", delta=f"{lucro:.2f}")
    c3.metric("ROI %", f"{(lucro / df_res['stake'].sum() * 100):.2f}%")

    st.subheader("📈 Evolução da Banca")
    df_res['acumulado'] = banca_inicial + df_res['lucro_prejuizo'].cumsum()
    fig = px.line(df_res, y='acumulado', title="Crescimento")
    st.plotly_chart(fig, use_container_width=True)
