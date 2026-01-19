import streamlit as st
import pandas as pd
from database import carregar_bancas, salvar_banca

def mostrar_bancas():
    st.title("🏦 Gestão de Bancas")
    
    # Formulário para nova banca
    with st.expander("➕ Adicionar Nova Banca", expanded=False):
        with st.form("form_banca", clear_on_submit=True):
            nome = st.text_input("Nome da Banca (Ex: Bet365, PunterPlace)")
            saldo = st.number_input("Saldo Inicial (R$)", min_value=0.0, step=10.0)
            if st.form_submit_button("Criar Banca"):
                if nome:
                    salvar_banca({'nome': nome, 'saldo_inicial': saldo, 'saldo_atual': saldo})
                    st.success(f"Banca {nome} criada com sucesso!")
                    st.rerun()
                else:
                    st.error("Dê um nome para a banca.")

    # Exibição das bancas existentes
    st.subheader("Suas Bancas")
    df_bancas = carregar_bancas()
    if not df_bancas.empty:
        # Layout em colunas para as bancas
        cols = st.columns(3)
        for i, (index, banca) in enumerate(df_bancas.iterrows()):
            with cols[i % 3]:
                st.metric(banca['nome'], f"R$ {banca['saldo_atual']:.2f}", delta_color="normal")
    else:
        st.info("Nenhuma banca cadastrada ainda.")
