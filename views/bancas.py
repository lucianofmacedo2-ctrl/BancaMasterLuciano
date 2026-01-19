import streamlit as st
import pandas as pd
from database import carregar_bancas, salvar_banca

def mostrar_bancas():
    st.title("🏦 Gestão de Bancas")
    
    # Formulário para nova banca
    with st.expander("➕ Adicionar Nova Banca"):
        with st.form("form_banca"):
            nome = st.text_input("Nome da Banca (Ex: Bet365, PunterPlace)")
            saldo = st.number_input("Saldo Inicial", min_value=0.0, step=10.0)
            if st.form_submit_button("Criar Banca"):
                if nome:
                    salvar_banca({'nome': nome, 'saldo_inicial': saldo, 'saldo_atual': saldo})
                    st.success("Banca criada!")
                    st.rerun()

    # Exibição das bancas
    df_bancas = carregar_bancas()
    if not df_bancas.empty:
        for _, banca in df_bancas.iterrows():
            st.metric(banca['nome'], f"R$ {banca['saldo_atual']:.2f}")
    else:
        st.info("Nenhuma banca cadastrada.")
