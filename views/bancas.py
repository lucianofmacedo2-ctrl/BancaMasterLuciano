import streamlit as st
import pandas as pd
import os

# --- PERSISTÊNCIA DE DADOS ---
# Caminho do arquivo onde as bancas serão salvas
CAMINHO_BANCAS = "data/bancas_cadastradas.csv"

def carregar_bancas():
    if os.path.exists(CAMINHO_BANCAS):
        return pd.read_csv(CAMINHO_BANCAS)
    return pd.DataFrame(columns=["Nome da Banca", "Saldo Inicial", "Moeda"])

def salvar_bancas(df):
    if not os.path.exists("data"):
        os.makedirs("data")
    df.to_csv(CAMINHO_BANCAS, index=False)

# --- INTERFACE ---
def mostrar_bancas():
    st.title("🏦 Gestão de Bancas")
    st.markdown("Cadastre e gerencie múltiplas bancas para diferentes estratégias.")

    # Carregar dados existentes
    df_bancas = carregar_bancas()

    # --- 1. CADASTRO DE NOVA BANCA ---
    with st.expander("➕ Cadastrar Nova Banca", expanded=True):
        with st.form("form_nova_banca", clear_on_submit=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            nome = col1.text_input("Nome da Banca (Ex: Banca de Alavancagem)")
            saldo = col2.number_input("Saldo Inicial", min_value=0.0, step=10.0, format="%.2f")
            moeda = col3.selectbox("Moeda", ["R$", "US$", "€"])
            
            submit = st.form_submit_button("Criar Banca")

            if submit:
                if nome:
                    if nome not in df_bancas["Nome da Banca"].values:
                        nova_linha = pd.DataFrame({"Nome da Banca": [nome], "Saldo Inicial": [saldo], "Moeda": [moeda]})
                        df_bancas = pd.concat([df_bancas, nova_linha], ignore_index=True)
                        salvar_bancas(df_bancas)
                        st.success(f"Banca '{nome}' criada com sucesso!")
                        st.rerun()
                    else:
                        st.error("Já existe uma banca com esse nome.")
                else:
                    st.warning("Por favor, dê um nome à banca.")

    st.divider()

    # --- 2. LISTAGEM E EXCLUSÃO ---
    st.subheader("📋 Bancas Ativas")
    
    if df_bancas.empty:
        st.info("Nenhuma banca cadastrada ainda.")
    else:
        # Tabela centralizada visualmente
        st.dataframe(
            df_bancas.style.format({"Saldo Inicial": "{:.2f}"}).set_properties(**{'text-align': 'center'}),
            use_container_width=True,
            hide_index=True
        )

        # --- ÁREA DE EXCLUSÃO ---
        with st.expander("🗑️ Excluir uma Banca"):
            banca_para_excluir = st.selectbox("Selecione a banca para remover", df_bancas["Nome da Banca"].tolist())
            confirmar_exclusao = st.button("Confirmar Exclusão Definitiva", type="primary")

            if confirmar_exclusao:
                df_bancas = df_bancas[df_bancas["Nome da Banca"] != banca_para_excluir]
                salvar_bancas(df_bancas)
                st.success(f"Banca '{banca_para_excluir}' removida!")
                st.rerun()

# --- RESUMO VISUAL ---
    if not df_bancas.empty:
        st.divider()
        st.subheader("💰 Resumo Total")
        total_bancas = len(df_bancas)
        soma_saldos = df_bancas["Saldo Inicial"].sum()
        
        c1, c2 = st.columns(2)
        c1.metric("Total de Bancas", total_bancas)
        c2.metric("Capital Inicial Total", f"R$ {soma_saldos:,.2f}")
