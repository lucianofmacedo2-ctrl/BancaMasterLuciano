import streamlit as st
import pandas as pd
import os
import plotly.express as px
from supabase import create_client

# --- CONFIGURAÇÃO SUPABASE ---
URL = "https://suhpdrqviuzrvygyhxhl.supabase.co"
KEY = "sb_publishable_pM5xDBpqZzo7h5SQqiFcfQ_ixbbydIB"
supabase = create_client(URL, KEY)

PATH_BANCAS = "data/bancas_cadastradas.csv"

def carregar_dados():
    try:
        response = supabase.table("apostas").select("*").execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            # Padroniza nomes para o restante do código
            df['Data'] = pd.to_datetime(df['data'])
            df['Resultado_Financeiro'] = df['lucro']
            df['Status'] = df['resultado']
            df['Banca'] = df['banca_id']
            df['Metodo'] = df['metodo']
            df['Stake'] = df['stake']
            
            dias_pt = {'Monday': 'Seg', 'Tuesday': 'Ter', 'Wednesday': 'Qua', 
                       'Thursday': 'Qui', 'Friday': 'Sex', 'Saturday': 'Sáb', 'Sunday': 'Dom'}
            df['Dia_Semana'] = df['Data'].dt.day_name().map(dias_pt)
            return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
    return pd.DataFrame()

def mostrar_dashboard():
    st.title("📊 Dashboard Cloud")
    
    df_ap = carregar_dados()
    if os.path.exists(PATH_BANCAS):
        df_ba = pd.read_csv(PATH_BANCAS)
    else:
        st.warning("Cadastre uma banca primeiro.")
        return

    if df_ap.empty:
        st.info("Nenhuma aposta encontrada no Supabase.")
        return

    # Filtros
    bancas_lista = ["Todas"] + df_ba["Nome da Banca"].tolist()
    banca_sel = st.selectbox("Filtrar Banca:", bancas_lista)

    if banca_sel != "Todas":
        df_f = df_ap[df_ap['Banca'] == banca_sel].copy()
        saldo_ini = df_ba[df_ba["Nome da Banca"] == banca_sel]["Saldo Inicial"].iloc[0]
    else:
        df_f = df_ap.copy()
        saldo_ini = df_ba["Saldo Inicial"].sum()

    # Métricas
    lucro_t = df_f['Resultado_Financeiro'].sum()
    win_r = (len(df_f[df_f['Status'].str.contains('Green', na=False)]) / len(df_f) * 100) if len(df_f)>0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Saldo Atual", f"R$ {saldo_ini + lucro_t:.2f}")
    c2.metric("Lucro Total", f"R$ {lucro_t:.2f}")
    c3.metric("Win Rate", f"{win_r:.1f}%")

    st.divider()
    
    # Gráfico de Evolução
    df_evol = df_f.sort_values('Data')
    df_evol['Acumulado'] = saldo_ini + df_evol['Resultado_Financeiro'].cumsum()
    st.plotly_chart(px.line(df_evol, x='Data', y='Acumulado', title="Evolução da Banca"), use_container_width=True)

    # Gráfico de Métodos
    df_met = df_f.groupby('Metodo')['Resultado_Financeiro'].sum().reset_index()
    st.plotly_chart(px.bar(df_met, x='Metodo', y='Resultado_Financeiro', color='Resultado_Financeiro', color_continuous_scale='RdYlGn'), use_container_width=True)
