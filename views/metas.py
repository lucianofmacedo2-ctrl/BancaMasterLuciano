import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from supabase import create_client

# --- CONFIGURAÇÃO SUPABASE ---
URL = "https://suhpdrqviuzrvygyhxhl.supabase.co"
KEY = "sb_publishable_pM5xDBpqZzo7h5SQqiFcfQ_ixbbydIB"
supabase = create_client(URL, KEY)

def mostrar_metas():
    st.title("🎯 Gestão de Metas & Recompensas")

    # --- 1. PROMOÇÃO SEMANAL (CÁLCULO AUTOMÁTICO) ---
    st.subheader("🎁 Progresso da Promoção Semanal")
    st.caption("Considera apostas com Odd >= 2.0 feitas de Segunda a Domingo.")

    try:
        # Calcular início (segunda) e fim (domingo) da semana atual
        hoje = datetime.now().date()
        segunda = hoje - timedelta(days=hoje.weekday())
        domingo = segunda + timedelta(days=6)

        # Buscar apostas da semana no Supabase
        res = supabase.table("apostas").select("stake, odd").gte("data", segunda).lte("data", domingo).execute()
        df_semana = pd.DataFrame(res.data)

        total_apostado = 0.0
        if not df_semana.empty:
            # Filtrar apenas apostas com Odd >= 2.0
            total_apostado = df_semana[df_semana['odd'] >= 2.0]['stake'].sum()

        # Lógica de Recompensas conforme o Print
        recompensa = 0
        proxima_meta = 0
        if total_apostado < 300:
            recompensa = 5 if total_apostado >= 100 else 0
            proxima_meta = 300
        elif total_apostado < 750:
            recompensa = 15
            proxima_meta = 750
        elif total_apostado < 1500:
            recompensa = 50
            proxima_meta = 1500
        else:
            recompensa = 100
            proxima_meta = 0

        # Visualização da Promoção
        col_p1, col_p2 = st.columns(2)
        col_p1.metric("Total Apostado (Semana)", f"R$ {total_apostado:.2f}")
        col_p2.metric("Crédito Garantido", f"R$ {recompensa:.2f}")

        if proxima_meta > 0:
            progresso_promo = min(total_apostado / proxima_meta, 1.0)
            st.progress(progresso_promo)
            st.write(f"Faltam **R$ {proxima_meta - total_apostado:.2f}** para o próximo nível de crédito.")
        else:
            st.success("🔥 Você atingiu o nível máximo de recompensa (R$ 100)!")

    except Exception as e:
        st.error(f"Erro ao calcular promoção: {e}")

    st.divider()

    # --- 2. METAS PESSOAIS ---
    st.subheader("🚀 Minhas Metas Pessoais")
    
    # Form para nova meta
    with st.expander("➕ Cadastrar Nova Meta"):
        with st.form("form_meta"):
            t_meta = st.text_input("Título da Meta (Ex: Lucro para Viagem)")
            v_obj = st.number_input("Valor Objetivo (R$)", min_value=1.0)
            v_ini = st.number_input("Valor Já Conquistado (R$)", min_value=0.0)
            if st.form_submit_button("Salvar Meta"):
                supabase.table("metas_pessoais").insert({
                    "titulo": t_meta, "valor_objetivo": v_obj, "valor_atual": v_ini
                }).execute()
                st.rerun()

    # Listagem de Metas
    res_m = supabase.table("metas_pessoais").select("*").eq("ativa", True).execute()
    metas = res_m.data

    if not metas:
        st.info("Nenhuma meta pessoal cadastrada.")
    else:
        for m in metas:
            porcentagem = min((m['valor_atual'] / m['valor_objetivo']), 1.0)
            
            st.markdown(f"### {m['titulo']}")
            
            # Gráfico de progresso visual (Gauge Chart)
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = m['valor_atual'],
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "Progresso R$"},
                gauge = {
                    'axis': {'range': [None, m['valor_objetivo']]},
                    'bar': {'color': "#00ffcc"},
                    'steps': [{'range': [0, m['valor_objetivo']], 'color': "#2b2b2b"}]
                }
            ))
            fig.update_layout(height=250, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig, use_container_width=True)

            # Botão para atualizar progresso ou excluir
            c_meta1, c_meta2 = st.columns([3, 1])
            novo_v = c_meta1.number_input(f"Adicionar valor a '{m['titulo']}'", min_value=0.0, key=f"upd_{m['id']}")
            if c_meta1.button("Atualizar", key=f"btn_{m['id']}"):
                supabase.table("metas_pessoais").update({"valor_atual": m['valor_atual'] + novo_v}).eq("id", m['id']).execute()
                st.rerun()
            
            if c_meta2.button("🗑️ Excluir", key=f"del_{m['id']}"):
                supabase.table("metas_pessoais").delete().eq("id", m['id']).execute()
                st.rerun()
            st.divider()
