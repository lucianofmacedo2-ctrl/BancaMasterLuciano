import streamlit as st
import pandas as pd
import plotly.express as px
from database import carregar_apostas

def mostrar_dashboard(banca_inicial):
    st.title("📊 Desempenho da Banca")
    df = carregar_apostas()
    
    df_res = df[df['resultado'] != 'Aberto'].copy()
    if df_res.empty:
        st.warning("Sem dados para dashboard.")
        return

    lucro = df_res['lucro_prejuizo'].sum()
    st.metric("Banca Atual", f"R$ {banca_inicial + lucro:.2f}", delta=f"{lucro:.2f}")

    df_res['acumulado'] = banca_inicial + df_res['lucro_prejuizo'].cumsum()
    fig = px.line(df_res, y='acumulado', title="Crescimento do Patrimônio", markers=True)
    st.plotly_chart(fig, use_container_width=True)
