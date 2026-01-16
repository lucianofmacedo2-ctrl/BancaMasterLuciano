import streamlit as st
import plotly.express as px
from database import carregar_apostas

def mostrar_dashboard():
    st.title("📊 Dashboard de Performance")
    df = carregar_apostas()
    
    if df.empty:
        st.info("Nenhuma aposta registrada.")
        return

    res = df[df['resultado'] != 'Pendente']
    lucro = res['lucro'].sum()
    roi = (lucro / res['stake'].sum() * 100) if not res.empty else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Lucro Total", f"R$ {lucro:.2f}")
    c2.metric("ROI Geral", f"{roi:.2f}%")
    c3.metric("Entradas", len(res))

    st.subheader("📈 Curva de Lucro")
    res = res.sort_values('data')
    res['acumulado'] = res['lucro'].cumsum()
    fig = px.line(res, x='data', y='acumulado', template="plotly_dark")
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
    st.plotly_chart(fig, use_container_width=True)