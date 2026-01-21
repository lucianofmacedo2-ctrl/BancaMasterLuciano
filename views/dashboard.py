import streamlit as st
import pandas as pd
import plotly.express as px
from supabase import create_client

# --- CONFIGURAÇÃO SUPABASE ---
URL = "https://suhpdrqviuzrvygyhxhl.supabase.co"
KEY = "sb_publishable_pM5xDBpqZzo7h5SQqiFcfQ_ixbbydIB"
supabase = create_client(URL, KEY)

def carregar_tudo():
    try:
        # Puxa tudo da nuvem
        res_a = supabase.table("apostas").select("*").execute()
        res_b = supabase.table("bancas").select("*").execute()
        return pd.DataFrame(res_a.data), pd.DataFrame(res_b.data)
    except:
        return pd.DataFrame(), pd.DataFrame()

def mostrar_dashboard():
    st.title("📊 Dashboard de Performance")
    df_ap, df_ba = carregar_tudo()

    if df_ba.empty:
        st.warning("Cadastre uma banca para ver os gráficos.")
        return

    # Filtro de Banca (Mantendo sua lógica de "Todas")
    banca_sel = st.selectbox("Filtrar por Banca", ["Todas"] + df_ba["nome"].tolist())

    if banca_sel != "Todas":
        df_f = df_ap[df_ap['banca_nome'] == banca_sel].copy()
        s_ini = df_ba[df_ba["nome"] == banca_sel]["saldo_inicial"].iloc[0]
    else:
        df_f = df_ap.copy()
        s_ini = df_ba["saldo_inicial"].sum()

    # --- MÉTRICAS (Igual ao seu visual anterior) ---
    lucro_total = df_f['lucro'].sum() if not df_f.empty else 0
    win_rate = (len(df_f[df_f['status'].str.contains('Green', na=False)]) / len(df_f) * 100) if not df_f.empty else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Saldo Atualizado", f"R$ {s_ini + lucro_total:.2f}")
    c2.metric("Lucro Líquido", f"R$ {lucro_total:.2f}")
    c3.metric("Win Rate", f"{win_rate:.1f}%")

    if not df_f.empty:
        st.divider()
        # Gráfico de Evolução (Eixo X = Data, Eixo Y = Lucro Acumulado)
        df_f['data'] = pd.to_datetime(df_f['data'])
        df_ev = df_f.sort_values('data')
        df_ev['Evolução'] = s_ini + df_ev['lucro'].cumsum()
        
        st.plotly_chart(px.line(df_ev, x='data', y='Evolução', title="Curva de Patrimônio"), use_container_width=True)

        # Gráfico de Métodos (Qual estratégia dá mais lucro?)
        df_met = df_f.groupby('metodo')['lucro'].sum().reset_index()
        st.plotly_chart(px.bar(df_met, x='metodo', y='lucro', color='lucro', title="Lucro por Método"), use_container_width=True)
    else:
        st.info("Aguardando registros de apostas para gerar gráficos.")
