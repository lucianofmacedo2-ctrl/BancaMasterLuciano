import streamlit as st
import pandas as pd
from supabase import create_client
import time

# --- CONFIGURAÇÃO SUPABASE ---
URL = "https://suhpdrqviuzrvygyhxhl.supabase.co"
KEY = "sb_publishable_pM5xDBpqZzo7h5SQqiFcfQ_ixbbydIB"
supabase = create_client(URL, KEY)

def carregar_dados():
    try:
        # Busca todas as apostas do Supabase
        res = supabase.table("apostas").select("*").execute()
        df = pd.DataFrame(res.data)
        return df
    except Exception as e:
        st.error(f"Erro ao carregar histórico: {e}")
        return pd.DataFrame()

def mostrar_historico():
    st.title("📜 Histórico de Apostas")
    
    df = carregar_dados()

    if df.empty:
        st.info("Nenhuma aposta encontrada no histórico.")
        return

    # --- PARTE 1: ATUALIZAÇÃO DE STATUS ---
    st.subheader("🔄 Atualizar Resultado da Aposta")
    
    # Criando uma descrição amigável para o selectbox usando as novas colunas
    # mandante vs visitante | mercado
    df['Descricao_Busca'] = (
        df['id'].astype(str) + " | " + 
        df['mandante'] + " x " + df['visitante'] + " | " + 
        df['mercado']
    )
    
    apostas_abertas = df[df['status'] == "Aberta"]

    if not apostas_abertas.empty:
        with st.expander("Clique aqui para resolver apostas em aberto"):
            escolha = st.selectbox("Selecione a aposta:", apostas_abertas['Descricao_Busca'].tolist())
            novo_status = st.selectbox("Novo Status:", ["Green", "Meio Green", "Red", "Meio Red", "Devolvida"])
            
            if st.button("Confirmar Atualização"):
                id_aposta = int(escolha.split(" | ")[0])
                
                # Pegar dados da aposta para recalcular o lucro
                aposta_info = df[df['id'] == id_aposta].iloc[0]
                stake = aposta_info['stake']
                odd = aposta_info['odd']
                
                # Cálculo do novo lucro
                lucro_novo = 0.0
                if novo_status == "Green": lucro_novo = stake * (odd - 1)
                elif novo_status == "Meio Green": lucro_novo = (stake * (odd - 1)) / 2
                elif novo_status == "Red": lucro_novo = -stake
                elif novo_status == "Meio Red": lucro_novo = -stake / 2

                try:
                    # Atualiza no Supabase
                    supabase.table("apostas").update({
                        "status": novo_status,
                        "lucro": float(lucro_novo)
                    }).eq("id", id_aposta).execute()
                    
                    st.success(f"Aposta {id_aposta} atualizada para {novo_status}!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar: {e}")
    else:
        st.write("✅ Todas as apostas estão resolvidas.")

    st.divider()

    # --- PARTE 2: TABELA GERAL ---
    st.subheader("📋 Todas as Entradas")
    
    # Selecionando e renomeando colunas para ficar bonito na tabela
    df_exibicao = df[[
        'data', 'banca_nome', 'liga', 'mandante', 'visitante', 
        'mercado', 'linha', 'metodo', 'stake', 'odd', 'status', 'lucro'
    ]].copy()
    
    # Formatação visual
    st.dataframe(
        df_exibicao.sort_values(by='data', ascending=False),
        use_container_width=True,
        hide_index=True
    )

    # --- PARTE 3: EXCLUSÃO ---
    with st.expander("🗑️ Excluir Registro"):
        id_deletar = st.selectbox("Selecione o ID para deletar permanentemente:", df['Descricao_Busca'].tolist())
        if st.button("Remover Aposta", type="primary"):
            id_real = int(id_deletar.split(" | ")[0])
            supabase.table("apostas").delete().eq("id", id_real).execute()
            st.warning(f"Registro {id_real} removido.")
            st.rerun()
