import streamlit as st
import pandas as pd
import os
from supabase import create_client

# --- CONFIGURAÇÃO SUPABASE ---
URL = "https://suhpdrqviuzrvygyhxhl.supabase.co"
KEY = "sb_publishable_pM5xDBpqZzo7h5SQqiFcfQ_ixbbydIB"
supabase = create_client(URL, KEY)

# Caminho local para backup
CAMINHO_BANCAS_LOCAL = "data/bancas_cadastradas.csv"

def mostrar_bancas():
    st.title("🏦 Gestão de Bancas")
    st.markdown("Cadastre e gerencie múltiplas bancas na nuvem para evitar perda de dados.")

    # --- 1. CADASTRO DE NOVA BANCA (Preservando seu Layout) ---
    with st.expander("➕ Cadastrar Nova Banca", expanded=True):
        with st.form("form_nova_banca", clear_on_submit=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            nome = col1.text_input("Nome da Banca (Ex: Banca de Alavancagem)")
            saldo = col2.number_input("Saldo Inicial", min_value=0.0, step=10.0, format="%.2f")
            moeda = col3.selectbox("Moeda", ["R$", "US$", "€"])
            
            submit = st.form_submit_button("Criar Banca na Nuvem")

            if submit:
                if nome:
                    try:
                        # Verifica se já existe no Supabase
                        check = supabase.table("bancas").select("nome").eq("nome", nome).execute()
                        if len(check.data) == 0:
                            # Salva no Supabase (Note que usei 'moeda' também, certifique-se que criou essa coluna ou o Supabase ignorará)
                            dados_nuvem = {
                                "nome": nome, 
                                "saldo_inicial": float(saldo),
                                # "moeda": moeda  # Descomente se criou a coluna 'moeda' no SQL
                            }
                            supabase.table("bancas").insert(dados_nuvem).execute()
                            
                            # Sincroniza Local (Backup)
                            if not os.path.exists("data"): os.makedirs("data")
                            df_local = pd.read_csv(CAMINHO_BANCAS_LOCAL) if os.path.exists(CAMINHO_BANCAS_LOCAL) else pd.DataFrame()
                            nova_linha = pd.DataFrame({"Nome da Banca": [nome], "Saldo Inicial": [saldo], "Moeda": [moeda]})
                            df_local = pd.concat([df_local, nova_linha], ignore_index=True)
                            df_local.to_csv(CAMINHO_BANCAS_LOCAL, index=False)
                            
                            st.success(f"Banca '{nome}' criada com sucesso!")
                            st.rerun()
                        else:
                            st.error("Já existe uma banca com esse nome no Supabase.")
                    except Exception as e:
                        st.error(f"Erro ao conectar com Supabase: {e}")
                else:
                    st.warning("Por favor, dê um nome à banca.")

    st.divider()

    # --- 2. LISTAGEM E EXCLUSÃO (Lendo da Nuvem) ---
    st.subheader("📋 Bancas Ativas (Sincronizadas)")
    
    try:
        res = supabase.table("bancas").select("*").execute()
        df_nuvem = pd.DataFrame(res.data)
        
        if df_nuvem.empty:
            st.info("Nenhuma banca cadastrada ainda.")
        else:
            # Exibição estilizada como você tinha antes
            st.dataframe(
                df_nuvem[['nome', 'saldo_inicial']].rename(columns={"nome": "Nome da Banca", "saldo_inicial": "Saldo Inicial"}),
                use_container_width=True,
                hide_index=True
            )

            # Área de Exclusão
            with st.expander("🗑️ Excluir uma Banca"):
                banca_para_excluir = st.selectbox("Selecione a banca para remover", df_nuvem["nome"].tolist())
                confirmar_exclusao = st.button("Confirmar Exclusão Definitiva", type="primary")

                if confirmar_exclusao:
                    try:
                        supabase.table("bancas").delete().eq("nome", banca_para_excluir).execute()
                        # Limpa local também
                        if os.path.exists(CAMINHO_BANCAS_LOCAL):
                            df_l = pd.read_csv(CAMINHO_BANCAS_LOCAL)
                            df_l = df_l[df_l["Nome da Banca"] != banca_para_excluir]
                            df_l.to_csv(CAMINHO_BANCAS_LOCAL, index=False)
                        
                        st.success(f"Banca '{banca_para_excluir}' removida!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao deletar: {e}")

            # --- 3. RESUMO VISUAL (Preservando sua funcionalidade) ---
            st.divider()
            st.subheader("💰 Resumo Total")
            total_bancas = len(df_nuvem)
            soma_saldos = df_nuvem["saldo_inicial"].sum()
            
            c1, c2 = st.columns(2)
            c1.metric("Total de Bancas", total_bancas)
            c2.metric("Capital Inicial Total", f"R$ {soma_saldos:,.2f}")

    except Exception as e:
        st.error(f"Erro ao carregar bancas: {e}")
