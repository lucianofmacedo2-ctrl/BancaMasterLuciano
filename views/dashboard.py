import streamlit as st
import pandas as pd
from database import carregar_apostas

def mostrar_dashboard():
    st.title("📊 Dashboard de Performance")
    
    df_apostas = carregar_apostas()
    
    if df_apostas.empty:
        st.info("Nenhuma aposta registrada para gerar estatísticas.")
        return

    # Métricas Principais
    total_apostas = len(df_apostas)
    lucro_total = df_apostas['lucro_prejuizo'].sum()
    win_rate = (len(df_apostas[df_apostas['lucro_prejuizo'] > 0]) / total_apostas) * 100

    c1, c2, c3 = st.columns(3)
    c1.metric("Total de Entradas", total_apostas)
    c2.metric("Lucro/Prejuízo", f"R$ {lucro_total:.2f}", delta=f"{lucro_total:.2f}")
    c3.metric("Win Rate", f"{win_rate:.1f}%")

    # Gráfico de Lucro por Método
    st.subheader("💰 Lucro por Método / Estratégia")
    if 'metodo' in df_apostas.columns:
        lucro_metodo = df_apostas.groupby('metodo')['lucro_prejuizo'].sum().sort_values()
        st.bar_chart(lucro_metodo)
