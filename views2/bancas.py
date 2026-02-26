import streamlit as st
import pandas as pd
import os
from supabase import create_client

# --- CONFIGURAÇÃO SUPABASE ---
URL = "https://suhpdrqviuzrvygyhxhl.supabase.co"
KEY = "sb_publishable_pM5xDBpqZzo7h5SQqiFcfQ_ixbbydIB"
supabase = create_client(URL, KEY)

# Alterado para evitar conflito com o backup local do Sistema 1
CAMINHO_BANCAS_LOCAL = "data/bancas_cadastradas_2.csv"

def mostrar_bancas():
    st.title("🏦 Gestão de Bancas - Sistema 2")
    st.markdown("Gerencie múltiplas bancas com sincronização em nuvem.")

    # --- 1. CADASTRO ---
    with st.expander("➕ Cadastrar Nova Banca", expanded=False): 
        with st.form("form_nova_banca_2", clear_on_submit=True):
            col1, col2, col3 = st.columns([2, 1, 1])
            nome = col1.text_input("Nome da Banca")
            saldo = col2.number_input("Saldo Inicial", min_value=0.0, step=10.0, format="%.2f")
            moeda = col3.selectbox("Moeda", ["R$", "US$", "€"])
            
            submit = st.form_submit_button("Criar Banca")

            if submit and nome:
                try:
                    # Salva no Supabase - TABELA 2
                    dados = {"nome": nome, "saldo_inicial": float(saldo)}
                    supabase.table("bancas_2").insert(dados).execute()
                    
                    # Backup local - ARQUIVO 2
                    if not os.path.exists("data"): os.makedirs("data")
                    df_local = pd.read_csv(CAMINHO_BANCAS_LOCAL) if os.path.exists(CAMINHO_BANCAS_LOCAL) else pd.DataFrame()
                    nova = pd.DataFrame([{"Nome da Banca": nome, "Saldo Inicial": saldo, "Moeda": moeda}])
                    pd.concat([df_local, nova], ignore_index=True).to_csv(CAMINHO_BANCAS_LOCAL, index=False)
                    
                    st.success(f"Banca '{nome}' criada no Sistema 2!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")

    st.divider()

    # --- 2. LISTAGEM E MOVIMENTAÇÕES ---
    try:
        # Busca Bancas - TABELA 2
        res_bancas = supabase.table("bancas_2").select("*").execute()
        df_b = pd.DataFrame(res_bancas.data)
        
        # Busca Movimentações - TABELA 2
        res_mov = supabase.table("movimentacoes_2").select("*").execute()
        df_mov = pd.DataFrame(res_mov.data)

        if not df_b.empty:
            # --- CÁLCULO DE SALDO REAL ---
            def calcular_saldo_atual(row):
                saldo_calculado = float(row['saldo_inicial'])
                
                # 1. Somar Aportes e subtrair Saques - DADOS DA TABELA 2
                if not df_mov.empty:
                    movs = df_mov[df_mov['banca_id'] == row['id']]
                    aportes = pd.to_numeric(movs[movs['tipo'] == 'Aporte']['valor']).sum()
                    saques = pd.to_numeric(movs[movs['tipo'] == 'Saque']['valor']).sum()
                    saldo_calculado += (aportes - saques)
                
                return saldo_calculado

            df_b['saldo_atual'] = df_b.apply(calcular_saldo_atual, axis=1)

            st.subheader("📋 Bancas Ativas (Sistema 2)")
            df_display = df_b[['nome', 'saldo_inicial', 'saldo_atual']].copy()
            df_display.columns = ["Nome da Banca", "Saldo Inicial", "Saldo Atual (Real)"]
            
            # Formatação para exibir como dinheiro
            st.dataframe(df_display.style.format({
                "Saldo Inicial": "R$ {:.2f}",
                "Saldo Atual (Real)": "R$ {:.2f}"
            }), use_container_width=True, hide_index=True)

            # --- SEÇÃO DE APORTES E SAQUES ---
            st.subheader("💸 Movimentação Financeira")
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
                banca_escolhida = c1.selectbox("Escolha a Banca", df_b["nome"].tolist(), key="sel_mov_2")
                tipo_mov = c2.selectbox("Operação", ["Aporte", "Saque"], key="op_mov_2")
                valor_mov = c3.number_input("Valor", min_value=0.0, step=50.0, key="val_mov_2")
                
                if c4.button("Registrar", use_container_width=True, key="btn_mov_2"):
                    # Localiza o ID da banca pelo nome
                    banca_row = df_b[df_b['nome'] == banca_escolhida].iloc[0]
                    id_banca = banca_row['id']
                    
                    mov_dados = {
                        "banca_id": int(id_banca),
                        "tipo": tipo_mov,
                        "valor": float(valor_mov)
                    }
                    
                    # Inserindo na MOVIMENTACOES_2
                    supabase.table("movimentacoes_2").insert(mov_dados).execute()
                    st.toast(f"{tipo_mov} de R${valor_mov} realizado com sucesso!")
                    st.rerun()

            # Exclusão - TABELA 2
            with st.expander("🗑️ Excluir uma Banca"):
                b_del = st.selectbox("Selecione para remover", df_b["nome"].tolist(), key="del_sel_2")
                if st.button("Confirmar Exclusão Definitiva", type="primary", key="btn_del_2"):
                    supabase.table("bancas_2").delete().eq("nome", b_del).execute()
                    st.rerun()

            # --- 3. RESUMO VISUAL NO RODAPÉ ---
            st.divider()
            st.subheader("💰 Resumo Total")
            total_inicial = df_b['saldo_inicial'].sum()
            total_atual = df_b['saldo_atual'].sum()
            diferenca = total_atual - total_inicial

            c1, c2, c3 = st.columns(3)
            c1.metric("Total de Bancas", len(df_b))
            c2.metric("Saldo Inicial Total", f"R$ {total_inicial:,.2f}")
            c3.metric("Saldo Real (Geral)", f"R$ {total_atual:,.2f}", delta=f"R$ {diferenca:,.2f}")
            
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")

if __name__ == "__main__":
    mostrar_bancas()
