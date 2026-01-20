import streamlit as st
from database import supabase, carregar_bancas

def mostrar_bancas():
    st.title("🏦 Gestão de Bancas")
    
    with st.expander("➕ Criar Nova Banca"):
        nome = st.text_input("Nome da Banca")
        if st.button("Confirmar Criação"):
            supabase.table("bancas").insert({"nome": nome}).execute()
            st.rerun()

    df_b = carregar_bancas()
    if not df_b.empty:
        st.subheader("Bancas Ativas")
        st.dataframe(df_b[['nome']], use_container_width=True)
