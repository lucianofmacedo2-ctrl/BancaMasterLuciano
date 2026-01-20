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
        # Tradução dos dias para o gráfico
        dias_pt = {
            'Monday': 'Seg', 'Tuesday': 'Ter', 'Wednesday': 'Qua', 
            'Thursday': 'Qui', 'Friday': 'Sex', 'Saturday': 'Sáb', 'Sunday': 'Dom'
        }
        df_ap['Dia_Semana'] = df_ap['Data'].dt.day_name().map(dias_pt)
        
    return df_ap, df_ba

def mostrar_dashboard():
    st.title("📊 Dashboard de Performance")

    df_ap, df_ba = carregar_dados()

    if df_ba.empty:
        st.warning("⚠️ Nenhuma banca cadastrada. Vá até 'Bancas' para começar.")
        return

    # --- FILTRO POR BANCA (PRESERVADO) ---
    bancas_lista = ["Todas"] + df_ba["Nome da Banca"].tolist()
    banca_sel = st.selectbox("📊 Analisar Banca:", bancas_lista)

    # Filtragem dos dados conforme seleção
    if banca_sel != "Todas":
        df_ap_filtrado = df_ap[df_ap['Banca'] == banca_sel].copy()
        saldo_inicial = df_ba[df_ba["Nome da Banca"] == banca_sel]["Saldo Inicial"].iloc[0]
    else:
        df_ap_filtrado = df_ap.copy()
        saldo_inicial = df_ba["Saldo Inicial"].sum()

    if df_ap_filtrado.empty:
        st.info(f"Nenhuma aposta registrada para a banca: {banca_sel}")
        return

    # --- MÉTRICAS PRINCIPAIS ---
    lucro_total = df_ap_filtrado['Resultado'].sum()
    saldo_atual = saldo_inicial + lucro_total
    roi = (lucro_total / df_ap_filtrado['Stake'].sum() * 100) if df_ap_filtrado['Stake'].sum() > 0 else 0
    win_rate = (len(df_ap_filtrado[df_ap_filtrado['Status'].isin(['Green', 'Meio Green'])]) / len(df_ap_filtrado) * 100)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Saldo Atual", f"R$ {saldo_atual:.2f}", delta=f"{lucro_total:.2f}")
    c2.metric("ROI %", f"{roi:.2f}%")
    c3.metric("Taxa de Win", f"{win_rate:.1f}%")
    c4.metric("Qtd. Apostas", len(df_ap_filtrado))

    st.divider()

    # --- GRÁFICOS DE EVOLUÇÃO E MÉTODO ---
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.subheader("📈 Evolução do Patrimônio")
        df_evolucao = df_ap_filtrado.sort_values('Data').copy()
        df_evolucao['Lucro_Acumulado'] = df_evolucao['Resultado'].cumsum()
        df_evolucao['Banca_Total'] = saldo_inicial + df_evolucao['Lucro_Acumulado']
        fig_evol = px.line(df_evolucao, x='Data', y='Banca_Total', title="Crescimento da Banca", line_shape='spline')
        st.plotly_chart(fig_evol, use_container_width=True)

    with col_g2:
        st.subheader("🎯 Lucro por Método")
        df_metodo = df_ap_filtrado.groupby('Metodo')['Resultado'].sum().reset_index()
        fig_met = px.bar(df_metodo, x='Metodo', y='Resultado', color='Resultado', color_continuous_scale='RdYlGn')
        st.plotly_chart(fig_met, use_container_width=True)

    st.divider()

    # --- ANÁLISE DE DIAS E LIGAS (NOVO) ---
    col_g3, col_g4 = st.columns(2)

    with col_g3:
        st.subheader("📅 Desempenho por Dia da Semana")
        ordem_dias = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
        df_dia = df_ap_filtrado.groupby('Dia_Semana')['Resultado'].sum().reindex(ordem_dias).reset_index()
        fig_dia = px.bar(df_dia, x='Dia_Semana', y='Resultado', color='Resultado', color_continuous_scale='RdYlGn')
        st.plotly_chart(fig_dia, use_container_width=True)

    with col_g4:
        st.subheader("🏟️ Top 10 Ligas (Lucratividade)")
        df_liga = df_ap_filtrado.groupby('Liga')['Resultado'].sum().sort_values(ascending=False).head(10).reset_index()
        fig_liga = px.pie(df_liga, values=df_liga['Resultado'].clip(lower=0), names='Liga', hole=.4)
        st.plotly_chart(fig_liga, use_container_width=True)

    # --- ALERTA DE PERFORMANCE ---
    df_liga_full = df_ap_filtrado.groupby('Liga')['Resultado'].sum().sort_values().reset_index()
    pior_liga = df_liga_full.iloc[0]
    if pior_liga['Resultado'] < 0:
        st.error(f"⚠️ **Fuga de Capital:** Na liga **{pior_liga['Liga']}**, seu prejuízo acumulado é de R$ {pior_liga['Resultado']:.2f}. Avalie seu método nesta liga.")
