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
        res = supabase.table("apostas").select("*").execute()
        return pd.DataFrame(res.data)
    except Exception as e:
        st.error(f"Erro ao conectar com Supabase: {e}")
        return pd.DataFrame()

def mostrar_historico():
    st.title("📜 Histórico de Apostas")
    
    df = carregar_dados()

    if df.empty:
        st.info("Nenhuma aposta encontrada.")
        return

    # --- 1. RESOLVER APOSTAS ABERTAS ---
    st.subheader("🔄 Atualizar Resultado da Aposta")
    
    # Criamos a coluna de busca garantindo que os nomes batam com o seu Supabase
    # Usamos .get() ou nomes em minúsculo para evitar o KeyError
    df['Busca'] = (
        df['id'].astype(str) + " | " + 
        df['mandante'].fillna('') + " x " + df['visitante'].fillna('') + " | " + 
        df['mercado'].fillna('')
    )
    
    # Filtramos apenas as que o status é 'Aberta'
    df_abertas = df[df['status'] == "Aberta"]

    if not df_abertas.empty:
        with st.expander("Atualizar status de apostas pendentes", expanded=True):
            escolha = st.selectbox("Selecione a aposta:", df_abertas['Busca'].tolist())
            novo_status = st.selectbox("Resultado:", ["Green", "Meio Green", "Red", "Meio Red", "Devolvida"])
            
            if st.button("Confirmar Resultado"):
                id_sel = escolha.split(" | ")[0]
                
                # Localizamos os dados para recalcular o lucro
                dados_aposta = df[df['id'].astype(str) == id_sel].iloc[0]
                stake = float(dados_aposta['stake'])
                odd = float(dados_aposta['odd'])
                
                lucro_final = 0.0
                if novo_status == "Green": lucro_final = stake * (odd - 1)
                elif novo_status == "Meio Green": lucro_final = (stake * (odd - 1)) / 2
                elif novo_status == "Red": lucro_final = -stake
                elif novo_status == "Meio Red": lucro_final = -stake / 2

                try:
                    supabase.table("apostas").update({
                        "status": novo_status,
                        "lucro": lucro_final
                    }).eq("id", id_sel).execute()
                    
                    st.success(f"Aposta {id_sel} atualizada!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar no banco: {e}")
    else:
        st.write("✅ Não há apostas abertas para atualizar.")

    st.divider()

    # --- 2. LISTA GERAL (Visual da sua imagem) ---
    st.subheader("Lista Geral de Apostas")
    
    # Reordenando colunas para o layout da sua tabela
    colunas_exibir = [
        'id', 'data', 'liga', 'mandante', 'visitante', 'mercado', 
        'linha', 'metodo', 'stake', 'odd', 'status', 'lucro', 'banca_nome', 'obs'
    ]
    
    # Garantimos que apenas colunas existentes sejam exibidas
    df_final = df[[c for c in colunas_exibir if c in df.columns]]
    
    st.dataframe(
        df_final.sort_values(by='data', ascending=False),
        use_container_width=True,
        hide_index=True
    )

    # --- 3. EXCLUIR REGISTRO ---
    with st.expander("🗑️ Deletar Registro"):
        item_deletar = st.selectbox("Selecione o registro para apagar:", df['Busca'].tolist(), key="del")
        if st.button("Excluir Permanentemente", type="primary"):
            id_del = item_deletar.split(" | ")[0]
            supabase.table("apostas").delete().eq("id", id_del).execute()
            st.warning("Registro removido com sucesso.")
            time.sleep(1)
            st.rerun()
