import streamlit as st
import pandas as pd
import os

def mostrar_bancas():
    st.title("🏦 Gestão de Bancas")
    
    # Simulação de armazenamento (pode usar o database.py para salvar)
    if 'bancas' not in st.session_state:
        st.session_state.bancas = {"Principal": 1000.0, "Alavancagem": 200.0}

    c1, c2 = st.columns(2)
    nome_banca = c1.selectbox("Selecionar Banca", list(st.session_state.bancas.keys()))
    novo_valor = c2.number_input("Ajustar Saldo", value=st.session_state.bancas[nome_banca])

    if st.button("Salvar Alteração"):
        st.session_state.bancas[nome_banca] = novo_valor
        st.success("Saldo atualizado!")

    st.divider()
    st.subheader("Resumo")
    for b, v in st.session_state.bancas.items():
        st.metric(b, f"R$ {v:,.2f}")
