import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase import create_client

# --- CONFIGURAÇÃO SUPABASE ---
URL = "https://suhpdrqviuzrvygyhxhl.supabase.co"
KEY = "sb_publishable_pM5xDBpqZzo7h5SQqiFcfQ_ixbbydIB"
supabase = create_client(URL, KEY)

def carregar_dados_financeiros():
    try:
        # Busca apostas e bancas do Sistema 2
        res_a = supabase.table("apostas_2").select("stake, odd, lucro, data").execute()
        res_b = supabase.table("bancas_2").select("saldo_inicial").execute()
        
        df_ap = pd.DataFrame(res_a.data)
        df_ba = pd.DataFrame(res_b.data)
        
        lucro_total = df_ap['lucro'].sum() if not df_ap.empty else 0
        saldo_inicial_total = df_ba['saldo_inicial'].sum() if not df_ba.empty else 0
        
        return df_ap, (saldo_inicial_total + lucro_total)
    except:
        return pd.DataFrame(), 0.0

def mostrar_metas():
    st.title("🎯 Gestão de Metas & Recompensas - Sistema 2")

    # 1. CARREGAR SALDO ATUALIZADO
    df_apostas, saldo_atualizado = carregar_dados_financeiros()

    # --- BLOCO 1: PROMOÇÃO SEMANAL (AUTOMÁTICO) ---
    st.subheader("🎁 Progresso da Promoção Semanal (S2)")
    
    hoje = datetime.now().date()
    segunda = hoje - timedelta(days=hoje.weekday())
    domingo = segunda + timedelta(days=6)

    total_promo = 0.0
    if not df_apostas.empty:
        # Converte data para filtrar a semana
        df_apostas['data_dt'] = pd.to_datetime(df_apostas['data']).dt.date
        filtro_semana = df_apostas[
            (df_apostas['data_dt'] >= segunda) & 
            (df_apostas['data_dt'] <= domingo) & 
            (df_apostas['odd'] >= 2.0)
        ]
        total_promo = filtro_semana['stake'].sum()

    # Faixas da Promoção
    recompensa = 0
    proxima = 0
    if total_promo < 100: 
        recompensa, proxima = 0, 100
    elif total_promo < 300: 
        recompensa, proxima = 5, 300
    elif total_promo < 750: 
        recompensa, proxima = 15, 750
    elif total_promo < 1500: 
        recompensa, proxima = 50, 1500
    else: 
        recompensa, proxima = 100, 0

    c_p1, c_p2 = st.columns(2)
    c_p1.metric("Volume Semanal (Odd 2+)", f"R$ {total_promo:.2f}")
    c_p2.metric("Crédito a Receber", f"R$ {recompensa:.2f}")
    
    if proxima > 0:
        st.progress(min(total_promo / proxima, 1.0))
        st.caption(f"Faltam R$ {proxima - total_promo:.2f} para o próximo nível no Sistema 2.")

    st.divider()

    # --- BLOCO 2: METAS PESSOAIS ---
    st.subheader("🚀 Minhas Metas de Patrimônio (S2)")
    st.info(f"💰 Seu Saldo Atual em Banca (S2): **R$ {saldo_atualizado:.2f}**")

    # Criar Meta
    with st.expander("➕ Definir Novo Objetivo Financeiro - S2"):
        with st.form("nova_meta_2"):
            titulo = st.text_input("Nome da Meta (Ex: Dobrar a Banca)")
            objetivo = st.number_input("Valor Alvo (R$)", min_value=1.0, value=500.0)
            if st.form_submit_button("Cadastrar Meta no Sistema 2"):
                # Salvando na tabela específica do sistema 2
                supabase.table("metas_pessoais_2").insert({
                    "titulo": titulo, 
                    "valor_objetivo": objetivo,
                    "ativa": True
                }).execute()
                st.rerun()

    # Mostrar Metas
    try:
        res_m = supabase.table("metas_pessoais_2").select("*").eq("ativa", True).execute()
        for m in res_m.data:
            st.write(f"#### {m['titulo']}")
            
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = saldo_atualizado,
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [None, m['valor_objetivo']]},
                    'bar': {'color': "#00ffcc"},
                    'steps': [{'range': [0, m['valor_objetivo']], 'color': "#1a1a1a"}],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': m['valor_objetivo']
                    }
                }
            ))
            fig.update_layout(height=250, margin=dict(l=30, r=30, t=30, b=30))
            st.plotly_chart(fig, use_container_width=True, key=f"gauge_meta_2_{m['id']}")

            if st.button(f"Remover {m['titulo']}", key=f"del_meta_2_{m['id']}"):
                supabase.table("metas_pessoais_2").delete().eq("id", m['id']).execute()
                st.rerun()
    except:
        st.warning("Tabela 'metas_pessoais_2' não encontrada. Certifique-se de criá-la no Supabase se desejar usar metas independentes para o Sistema 2.")

if __name__ == "__main__":
    mostrar_metas()
