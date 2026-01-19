import streamlit as st
import pandas as pd
import plotly.express as px
from database import carregar_apostas

def mostrar_dashboard(banca_inicial):
    st.title("📊 Dashboard de Performance")
    df = carregar_apostas()
    
    if df.empty or len(df[df['resultado'] != 'Aberto']) == 0:
        st.warning("Sem dados suficientes para gerar o dashboard.")
        return

    # Cálculos
    df_encerradas = df[df['resultado'] != 'Aberto'].copy()
    lucro_total = df_encerradas['lucro_prejuizo'].sum()
    banca_atual = banca_inicial + lucro_total
    roi = (lucro_total / df_encerradas['stake'].sum()) * 100

    # Métricas Principais
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Banca Atual", f"R$ {banca_atual:.2f}")
    c2.metric("Lucro/Prejuízo", f"R$ {lucro_total:.2f}", delta=f"{lucro_total:.2f}")
    c3.metric("ROI", f"{roi:.2f}%")
    c4.metric("Total Apostas", len(df_encerradas))

    # Gráfico de Evolução
    st.subheader("📈 Evolução do Patrimônio")
    df_encerradas['acumulado'] = banca_inicial + df_encerradas['lucro_prejuizo'].cumsum()
    fig = px.line(df_encerradas, x=df_encerradas.index, y='acumulado', title="Crescimento da Banca")
    st.plotly_chart(fig, use_container_width=True)
