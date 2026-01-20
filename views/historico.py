import streamlit as st
import pandas as pd
import os

PATH_APOSTAS = "data/historico_apostas.csv"

def mostrar_historico():
    st.title("📂 Histórico e Atualização")

    if not os.path.exists(PATH_APOSTAS):
        st.info("Nenhuma aposta registrada ainda.")
        return

    df = pd.read_csv(PATH_APOSTAS)
    
    # Se existirem apostas antigas sem ID, preenchemos com 'Antiga'
    if "ID" not in df.columns:
        df.insert(0, "ID", "Antiga")

    st.subheader("Lista Geral de Apostas")
    st.dataframe(df, use_container_width=True)

    st.divider()

    # --- SISTEMA DE ATUALIZAÇÃO ---
    st.subheader("🔄 Atualizar Resultado da Aposta")
    
    # Criar coluna temporária para identificar com clareza no Selectbox
    df['Descricao_Busca'] = df['ID'].astype(str) + " | " + df['Jogo'] + " | " + df['Mercado']
    
    escolha = st.selectbox("Selecione qual aposta deseja atualizar:", df['Descricao_Busca'].tolist())

    if escolha:
        # Localiza o índice da aposta
        idx = df[df['Descricao_Busca'] == escolha].index[0]
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Pega o status atual para vir pré-selecionado
            status_atual = df.at[idx, 'Status']
            lista_status = ["Aberta", "Green", "Meio Green", "Red", "Meio Red", "Devolvida"]
            try:
                idx_status = lista_status.index(status_atual)
            except:
                idx_status = 0
                
            novo_status = st.selectbox("Novo Status", lista_status, index=idx_status)
        
        with col2:
            nova_odd = st.number_input("Odd Final", value=float(df.at[idx, 'Odd']), step=0.01)
            
        with col3:
            nova_stake = st.number_input("Stake Utilizada", value=float(df.at[idx, 'Stake']), step=1.0)

        if st.button("Salvar Alterações"):
            # Recálculo Matemático Profissional
            resultado_fin = 0.0
            if novo_status == "Green": 
                resultado_fin = nova_stake * (nova_odd - 1)
            elif novo_status == "Meio Green": 
                resultado_fin = (nova_stake * (nova_odd - 1)) / 2
            elif novo_status == "Red": 
                resultado_fin = -nova_stake
            elif novo_status == "Meio Red": 
                resultado_fin = -nova_stake / 2
            elif novo_status == "Devolvida":
                resultado_fin = 0.0
            
            # Aplica no DataFrame
            df.at[idx, 'Status'] = novo_status
            df.at[idx, 'Odd'] = nova_odd
            df.at[idx, 'Stake'] = nova_stake
            df.at[idx, 'Resultado'] = resultado_fin
            
            # Remove coluna auxiliar e salva
            df_final = df.drop(columns=['Descricao_Busca'])
            df_final.to_csv(PATH_APOSTAS, index=False)
            
            st.success("Aposta atualizada com sucesso!")
            st.rerun()

    # --- EXCLUSÃO ---
    with st.expander("🗑️ Zona de Exclusão"):
        if st.button("❌ Remover esta aposta permanentemente"):
            df_excluir = df[df['Descricao_Busca'] != escolha]
            df_excluir = df_excluir.drop(columns=['Descricao_Busca'])
            df_excluir.to_csv(PATH_APOSTAS, index=False)
            st.warning("Aposta excluída.")
            st.rerun()
