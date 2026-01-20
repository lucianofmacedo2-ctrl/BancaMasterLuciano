import streamlit as st
import pandas as pd
from database import carregar_apostas

def mostrar_dashboard():
    st.title("📊 Desempenho Geral")
    df = carregar_apostas()
    
    if df.empty:
        st.info("Registre apostas para visualizar o dashboard.")
        return

    # Filtra apenas resolvidas
    df_res = df[df['resultado'] != 'Aberto'].copy()
    
    lucro = df_res['lucro_prejuizo'].sum()
    roi = (lucro / df_res['stake'].sum()) * 100 if not df_res.empty else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Lucro Total", f"R$ {lucro:.2f}", delta=f"{lucro:.2f}")
    c2.metric("ROI %", f"{roi:.2f}%")
    c3.metric("Entradas", len(df_res))

    if not df_res.empty:
        df_res['acumulado'] = df_res['lucro_prejuizo'].cumsum()
        st.line_chart(df_res['acumulado'])
