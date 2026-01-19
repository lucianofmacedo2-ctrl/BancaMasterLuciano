import streamlit as st
import pandas as pd
import plotly.express as px
from database import carregar_apostas

def mostrar_dashboard():
    st.title("📊 Dashboard de Performance")

    df = carregar_apostas()
    
    # Remover apostas em aberto para não sujar as métricas de lucro
    df_finalizadas = df[df['resultado'] != "Aberto"].copy()

    if df_finalizadas.empty:
        st.info("Registre e finalize algumas apostas para visualizar as estatísticas.")
        return

    # --- 1. MÉTRICAS PRINCIPAIS ---
    lucro_total = df_finalizadas['lucro_prejuizo'].sum()
    roi = (lucro_total / df_finalizadas['stake'].sum()) * 100 if df_finalizadas['stake'].sum() > 0 else 0
    taxa_acerto = (len(df_finalizadas[df_finalizadas['resultado'].str.contains("Green")]) / len(df_finalizadas)) * 100

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Lucro Total", f"R$ {lucro_total:.2f}", delta=f"{lucro_total:.2f}")
    c2.metric("ROI", f"{roi:.2f}%")
    c3.metric("Taxa de Acerto", f"{taxa_acerto:.1f}%")
    c4.metric("Total de Apostas", len(df_finalizadas))

    st.divider()

    # --- 2. GRÁFICO DE EVOLUÇÃO (LUCRO ACUMULADO) ---
    st.subheader("📈 Evolução da Banca")
    df_finalizadas['data'] = pd.to_datetime(df_finalizadas['data'])
    df_evolucao = df_finalizadas.sort_values('data')
    df_evolucao['lucro_acumulado'] = df_evolucao['lucro_prejuizo'].cumsum()
    
    fig_evolucao = px.line(df_evolucao, x='data', y='lucro_acumulado', 
                          title="Crescimento do Capital",
                          markers=True, line_shape="spline",
                          color_discrete_sequence=["#00ffcc"])
    st.plotly_chart(fig_evolucao, use_container_width=True)

    # --- 3. ANÁLISE POR MERCADO E LIGA ---
    col_graf1, col_graf2 = st.columns(2)

    with col_graf1:
        st.subheader("🎯 Lucro por Mercado")
        lucro_mercado = df_finalizadas.groupby('mercado')['lucro_prejuizo'].sum().reset_index()
        fig_mercado = px.bar(lucro_mercado, x='mercado', y='lucro_prejuizo',
                             color='lucro_prejuizo', color_continuous_scale='RdYlGn')
        st.plotly_chart(fig_mercado, use_container_width=True)

    with col_graf2:
        st.subheader("⚽ Lucro por Liga")
        lucro_liga = df_finalizadas.groupby('liga')['lucro_prejuizo'].sum().reset_index()
        fig_liga = px.bar(lucro_liga, y='liga', x='lucro_prejuizo', orientation='h',
                          color='lucro_prejuizo', color_continuous_scale='RdYlGn')
        st.plotly_chart(fig_liga, use_container_width=True)

    st.divider()

    # --- 4. DISTRIBUIÇÃO DE RESULTADOS ---
    col_graf3, col_graf4 = st.columns(2)

    with col_graf3:
        st.subheader("📉 Distribuição de Resultados")
        fig_pizza = px.pie(df_finalizadas, names='resultado', 
                           color='resultado',
                           color_discrete_map={'Green':'#2ecc71', 'Red':'#e74c3c', 'Void':'#95a5a6', 'Half Green':'#27ae60', 'Half Red':'#c0392b'})
        st.plotly_chart(fig_pizza, use_container_width=True)

    with col_graf4:
        st.subheader("🔄 Performance por Método")
        lucro_metodo = df_finalizadas.groupby('metodo')['lucro_prejuizo'].sum().reset_index()
        fig_metodo = px.bar(lucro_metodo, x='metodo', y='lucro_prejuizo',
                            title="Lucratividade por Estratégia")
        st.plotly_chart(fig_metodo, use_container_width=True)
