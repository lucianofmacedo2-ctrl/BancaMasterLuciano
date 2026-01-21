import streamlit as st
import pandas as pd
import os
from supabase import create_client

# --- CONFIGURAÇÃO SUPABASE ---
URL = "https://suhpdrqviuzrvygyhxhl.supabase.co"
KEY = "sb_publishable_pM5xDBpqZzo7h5SQqiFcfQ_ixbbydIB"
supabase = create_client(URL, KEY)

CAMINHO_BANCAS_LOCAL = "data/bancas_cadastradas.csv"

def mostrar_bancas():
    st.title("🏦 Gestão de Bancas")
    st.markdown("Gerencie múltiplas bancas com sincronização em nuvem.")

    # --- 1. CADASTRO (Mantendo seu visual original) ---
    with st.expander("➕ Cadastrar Nova Banca", expanded=True):
        with st.form("form_nova_banca", clear_on_submit=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            nome = col1.text_input("Nome da Banca")
            saldo = col2.number_input("Saldo Inicial", min_value=0.0, step=10.0, format="%.2f")
            moeda = col3.selectbox("Moeda", ["R$", "US$", "€"])
            
            submit = st.form_submit_button("Criar Banca")

            if submit and nome:
                try:
                    # Salva no Supabase (Incluindo moeda na obs se não tiver coluna própria)
                    dados = {"nome": nome, "saldo_inicial": float(saldo)}
                    supabase.table("bancas").insert(dados).execute()
                    
                    # Backup local para manter seu CSV histórico
                    if not os.path.exists("data"): os.makedirs("data")
                    df_local = pd.read_csv(CAMINHO_BANCAS_LOCAL) if os.path.exists(CAMINHO_BANCAS_LOCAL) else pd.DataFrame()
                    nova = pd.DataFrame([{"Nome da Banca": nome, "Saldo Inicial": saldo, "Moeda": moeda}])
                    pd.concat([df_local, nova], ignore_index=True).to_csv(CAMINHO_BANCAS_LOCAL, index=False)
                    
                    st.success(f"Banca '{nome}' criada!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    st.divider()

    # --- 2. LISTAGEM (Leitura da Nuvem + Estilização Original) ---
    try:
        res = supabase.table("bancas").select("*").execute()
        df_b = pd.DataFrame(res.data)
        
        if not df_b.empty:
            st.subheader("📋 Bancas Ativas")
            # Estilização que você usava
            df_display = df_b[['nome', 'saldo_inicial']].rename(columns={"nome": "Nome da Banca", "saldo_inicial": "Saldo Inicial"})
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            # Exclusão
            with st.expander("🗑️ Excluir uma Banca"):
                b_del = st.selectbox("Selecione para remover", df_b["nome"].tolist())
                if st.button("Confirmar Exclusão Definitiva", type="primary"):
                    supabase.table("bancas").delete().eq("nome", b_del).execute()
                    st.rerun()

            # --- 3. RESUMO VISUAL NO RODAPÉ ---
            st.divider()
            st.subheader("💰 Resumo Total")
            c1, c2 = st.columns(2)
            c1.metric("Total de Bancas", len(df_b))
            c2.metric("Capital Inicial Total", f"R$ {df_b['saldo_inicial'].sum():,.2f}")
    except:
        st.info("Nenhuma banca cadastrada.")
