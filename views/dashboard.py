import streamlit as st
import pandas as pd
import os
import plotly.express as px

# --- CAMINHOS ---
PATH_APOSTAS = "data/historico_apostas.csv"
PATH_BANCAS = "data/bancas_cadastradas.csv"

def carregar_dados():
    df_ap = pd.read_csv(PATH_APOSTAS) if os.path.exists(PATH_APOSTAS) else pd.DataFrame()
    df_ba = pd.read_csv(PATH_BANCAS) if os.path.exists(PATH_BANCAS) else pd.DataFrame()
    if not df_ap.empty:
        df_ap['Data'] = pd.to_datetime(df_ap['Data'])
    return df_ap, df_ba

def mostrar_dashboard():
    st.title("📊 Dashboard de Performance")

    df_ap, df_ba = carregar_dados()

    if df_ba.empty:
        st.warning("⚠️ Nenhuma banca cadastrada. Vá até 'Bancas' para começar.")
        return

    # --- FILTRO POR BANCA NO DASHBOARD ---
    bancas_lista = ["Todas"] + df_ba["Nome da Banca"].tolist()
    banca_sel = st.selectbox("📊 Analisar Banca:", bancas_lista)

    # Filtragem dos dados
    if banca_sel != "Todas":
        df_ap = df_ap[df_ap['Banca'] == banca_sel]
        saldo_inicial = df_ba[df_ba["Nome da Banca"] == banca_sel]["Saldo Inicial"].iloc[0]
    else:
        saldo_inicial = df_ba["Saldo Inicial"].sum()

    if df_ap.empty:
        st.info(f"Nenhuma aposta registrada para a banca: {banca_sel}")
        return

    # --- MÉTRICAS PRINCIPAIS ---
    lucro_total = df_ap['Resultado'].sum()
    saldo_atual = saldo_inicial + lucro_total
    roi = (lucro_total / df_ap['Stake'].sum() * 100) if df_ap['Stake'].sum() > 0 else 0
    win_rate = (len(df_ap[df_ap['Status'].isin(['Green', 'Meio Green'])]) / len(df_ap) * 100)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Saldo Atual", f"R$ {saldo_atual:.2f}", delta=f"{lucro_total:.2f}")
    c2.metric("ROI %", f"{roi:.2f}%")
    c3.metric("Taxa de Win", f"{win_rate:.1f}%")
    c4.metric("Qtd. Apostas", len(df_ap))

    st.divider()

    # --- GRÁFICOS ---
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("📈 Evolução do Patrimônio")
        # Criar linha do tempo de lucro acumulado
        df_evolucao = df_ap.sort_values('Data').copy()
        df_evolucao['Lucro_Acumulado'] = df_evolucao['Resultado'].cumsum()
        df_evolucao['Banca_Total'] = saldo_inicial + df_evolucao['Lucro_Acumulado']
        
        fig_evol = px.line(df_evolucao, x='Data', y='Banca_Total', 
                           title="Crescimento da Banca", labels={'Banca_Total': 'Saldo (R$)'},
                           line_shape='spline', render_mode='svg')
        st.plotly_chart(fig_evol, use_container_width=True)

    with col_g2:
        st.subheader("🎯 Performance por Método")
        df_metodo = df_ap.groupby('Metodo')['Resultado'].sum().reset_index()
        fig_met = px.bar(df_metodo, x='Metodo', y='Resultado', 
                         color='Resultado', color_continuous_scale='RdYlGn',
                         title="Lucro/Prejuízo por Método")
        st.plotly_chart(fig_met, use_container_width=True)

    st.divider()

    # --- ANÁLISE DE MERCADOS ---
    col_g3, col_g4 = st.columns(2)

    with col_g3:
        st.subheader("🏟️ Lucro por Liga")
        df_liga = df_ap.groupby('Liga')['Resultado'].sum().sort_values(ascending=False).head(10).reset_index()
        fig_liga = px.pie(df_liga, values='Resultado', names='Liga', title="Top 10 Ligas Lucrativas", hole=.4)
        st.plotly_chart(fig_liga, use_container_width=True)

    with col_g4:
        st.subheader("📉 Distribuição de Status")
        status_counts = df_ap['Status'].value_counts().reset_index()
        fig_status = px.bar(status_counts, x='Status', y='count', color='Status',
                            title="Frequência de Resultados")
        st.plotly_chart(fig_status, use_container_width=True)
