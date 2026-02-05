import streamlit as st
import pandas as pd
from supabase import create_client
import time
from datetime import datetime

# --- CONFIGURAÇÃO SUPABASE ---
URL = "https://suhpdrqviuzrvygyhxhl.supabase.co"
KEY = "sb_publishable_pM5xDBpqZzo7h5SQqiFcfQ_ixbbydIB"
supabase = create_client(URL, KEY)

def carregar_dados():
    try:
        # Forçamos a busca sem cache para garantir que aposta nova apareça
        res = supabase.table("apostas").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            # Limpa espaços em branco que podem vir do CSV ou do input
            for col in df.select_dtypes(['object']).columns:
                df[col] = df[col].astype(str).str.strip()
            # Garante que a coluna data seja datetime para o filtro funcionar
            df['data'] = pd.to_datetime(df['data']).dt.date
        return df
    except Exception as e:
        st.error(f"Erro ao conectar com Supabase: {e}")
        return pd.DataFrame()

def mostrar_historico():
    st.title("📜 Histórico de Apostas")
    
    df = carregar_dados()

    if df.empty:
        st.info("Nenhuma aposta encontrada no banco de dados.")
        return

    # Criamos a coluna de busca para os selects de Update e Delete
    df['Busca'] = (
        df['id'].astype(str) + " | " + 
        df['mandante'].fillna('?') + " x " + df['visitante'].fillna('?') + " | " + 
        df['mercado'].fillna('?') + " | " + 
        df['data'].astype(str)
    )

    # --- 1. RESOLVER APOSTAS ABERTAS ---
    st.subheader("🔄 Atualizar Resultado da Aposta")
    
    # Filtro inteligente: ignora se é maiúsculo ou minúsculo
    df_abertas = df[df['status'].str.lower() == "aberta"]

    if not df_abertas.empty:
        with st.expander(f"📝 {len(df_abertas)} apostas pendentes encontradas", expanded=True):
            escolha = st.selectbox("Selecione a aposta para dar o resultado:", df_abertas['Busca'].tolist())
            
            c1, c2 = st.columns(2)
            with c1:
                novo_status = st.selectbox("Resultado Final:", ["Green", "Meio Green", "Red", "Meio Red", "Devolvida"])
            with c2:
                st.write(" ") # Espaçador
                btn_confirmar = st.button("Confirmar Resultado", use_container_width=True)
            
            if btn_confirmar:
                id_sel = escolha.split(" | ")[0]
                
                # Localizamos os dados da linha selecionada para o cálculo
                dados_aposta = df[df['id'].astype(str) == id_sel].iloc[0]
                stake = float(dados_aposta['stake'])
                odd = float(dados_aposta['odd'])
                
                # Recálculo do Lucro
                lucro_final = 0.0
                if novo_status == "Green": lucro_final = stake * (odd - 1)
                elif novo_status == "Meio Green": lucro_final = (stake * (odd - 1)) / 2
                elif novo_status == "Red": lucro_final = -stake
                elif novo_status == "Meio Red": lucro_final = -stake / 2

                try:
                    supabase.table("apostas").update({
                        "status": novo_status,
                        "lucro": float(lucro_final)
                    }).eq("id", id_sel).execute()
                    
                    st.success(f"✅ Aposta {id_sel} atualizada!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar no banco: {e}")
    else:
        st.info("✅ Todas as apostas estão resolvidas.")

    st.divider()

    # --- 2. LISTA GERAL COM FILTRO ---
    st.subheader("📋 Lista Geral de Registros")
    
    # Filtro de Data
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        data_filtro = st.date_input("📅 Filtrar por dia específica", value=None)
    with col_f2:
        st.write("") # Alinhamento visual
        if data_filtro:
            st.info(f"Exibindo apenas apostas de: **{data_filtro.strftime('%d/%m/%Y')}**")

    # Colunas para exibir (Incluído 'operador')
    colunas_exibir = [
        'id', 'data', 'liga', 'mandante', 'visitante', 'mercado', 
        'linha', 'metodo', 'stake', 'odd', 'status', 'lucro', 'banca_nome', 'operador'
    ]
    
    # Exibimos apenas as colunas que existem no banco
    cols_existentes = [c for c in colunas_exibir if c in df.columns]
    
    # Aplicação do filtro de data no DataFrame
    df_filtrado = df.copy()
    if data_filtro:
        df_filtrado = df_filtrado[df_filtrado['data'] == data_filtro]

    # Ordenação: Mais recentes primeiro (Data e ID)
    df_exibicao = df_filtrado[cols_existentes].sort_values(by=['data', 'id'], ascending=[False, False])
    
    # Exibição da Tabela
    st.dataframe(
        df_exibicao,
        use_container_width=True,
        hide_index=True
    )

    # --- 3. EXCLUIR REGISTRO ---
    st.markdown("---")
    with st.expander("🗑️ Área de Exclusão"):
        item_deletar = st.selectbox("Selecione o registro para apagar:", df['Busca'].tolist(), key="del_box")
        if st.button("Excluir Permanentemente", type="primary"):
            try:
                id_del = item_deletar.split(" | ")[0]
                supabase.table("apostas").delete().eq("id", id_del).execute()
                st.success("Registro removido com sucesso.")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao deletar: {e}")
