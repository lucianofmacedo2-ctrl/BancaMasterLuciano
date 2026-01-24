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
                    # Salva no Supabase
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

    # --- 2. LISTAGEM E MOVIMENTAÇÕES ---
    try:
        # Busca Bancas
        res_bancas = supabase.table("bancas").select("*").execute()
        df_b = pd.DataFrame(res_bancas.data)
        
        # Busca Movimentações (Aportes/Saques)
        res_mov = supabase.table("movimentacoes").select("*").execute()
        df_mov = pd.DataFrame(res_mov.data)

        if not df_b.empty:
            # --- CÁLCULO DE SALDO REAL ---
            # Unimos as movimentações para calcular o saldo atualizado de cada banca
            def calcular_saldo_atual(row):
                if df_mov.empty: return row['saldo_inicial']
                movs = df_mov[df_mov['banca_id'] == row['id']]
                aportes = movs[movs['tipo'] == 'Aporte']['valor'].sum()
                saques = movs[movs['tipo'] == 'Saque']['valor'].sum()
                return row['saldo_inicial'] + aportes - saques

            df_b['saldo_atual'] = df_b.apply(calcular_saldo_atual, axis=1)

            st.subheader("📋 Bancas Ativas")
            df_display = df_b[['nome', 'saldo_inicial', 'saldo_atual']].rename(
                columns={"nome": "Nome da Banca", "saldo_inicial": "Saldo Inicial", "saldo_atual": "Saldo Atual (Real)"}
            )
            st.dataframe(df_display, use_container_width=True, hide_index=True)

            # --- NOVO: SEÇÃO DE APORTES E SAQUES ---
            st.subheader("💸 Movimentação Financeira")
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                banca_escolhida = c1.selectbox("Escolha a Banca", df_b["nome"].tolist(), key="sel_mov")
                tipo_mov = c2.selectbox("Operação", ["Aporte", "Saque"])
                valor_mov = c3.number_input("Valor", min_value=0.0, step=50.0)
                
                if c4.button("Registrar", use_container_width=True):
                    id_banca = df_b[df_b['nome'] == banca_escolhida]['id'].values[0]
                    mov_dados = {
                        "banca_id": int(id_banca),
                        "tipo": tipo_mov,
                        "valor": float(valor_mov)
                    }
                    supabase.table("movimentacoes").insert(mov_dados).execute()
                    st.toast(f"{tipo_mov} de R${valor_mov} realizado!")
                    st.rerun()

            # Exclusão (Mantida)
            with st.expander("🗑️ Excluir uma Banca"):
                b_del = st.selectbox("Selecione para remover", df_b["nome"].tolist(), key="del_sel")
                if st.button("Confirmar Exclusão Definitiva", type="primary"):
                    supabase.table("bancas").delete().eq("nome", b_del).execute()
                    st.rerun()

            # --- 3. RESUMO VISUAL NO RODAPÉ ---
            st.divider()
            st.subheader("💰 Resumo Total")
            total_inicial = df_b['saldo_inicial'].sum()
            total_atual = df_b['saldo_atual'].sum()
            lucro_aportes = total_atual - total_inicial

            c1, c2, c3 = st.columns(3)
            c1.metric("Total de Bancas", len(df_b))
            c2.metric("Saldo Inicial Total", f"R$ {total_inicial:,.2f}")
            c3.metric("Saldo Real (Com Aportes)", f"R$ {total_atual:,.2f}", delta=f"{lucro_aportes:,.2f}")
            
    except Exception as e:
        st.info(f"Aguardando cadastro de bancas ou erro de conexão: {e}")
