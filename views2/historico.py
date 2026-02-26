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
        # Forçamos a busca sem cache na tabela do Sistema 2
        res = supabase.table("apostas_2").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            # Limpa espaços em branco
            for col in df.select_dtypes(['object']).columns:
                df[col] = df[col].astype(str).str.strip()
            # Garante que a coluna data seja datetime para o filtro funcionar
            df['data'] = pd.to_datetime(df['data']).dt.date
        return df
    except Exception as e:
        st.error(f"Erro ao conectar com Supabase (Sistema 2): {e}")
        return pd.DataFrame()

def mostrar_historico():
    st.title("📜 Histórico de Apostas - Sistema 2")
    
    df = carregar_dados()

    if df.empty:
        st.info("Nenhuma aposta encontrada no banco de dados do Sistema 2.")
        return

    # --- FUNÇÕES AUXILIARES ---
    def eh_dupla(row):
        """Verifica se a linha possui uma segunda seleção válida"""
        m2 = str(row.get('mercado_2', 'None'))
        return m2 != "None" and m2 != "nan" and m2 != ""

    def formatar_mercado_v2(row):
        """Formata o nome do mercado para exibição em listas e tabelas"""
        m1 = f"{row.get('mercado', '?')} ({row.get('linha', '?')})"
        if eh_dupla(row):
            return f"DUPLA: {m1} + {row.get('mercado_2')} ({row.get('linha_2')})"
        return m1

    # Criamos a coluna de busca para os selects de Update e Delete
    df['Busca'] = (
        df['id'].astype(str) + " | " + 
        df['mandante'].fillna('?') + " x " + df['visitante'].fillna('?') + " | " + 
        df.apply(formatar_mercado_v2, axis=1) + " | " + 
        df['data'].astype(str)
    )

    # --- 1. RESOLVER APOSTAS ABERTAS ---
    st.subheader("🔄 Atualizar Resultado da Aposta")
    
    # Filtro inteligente para apostas com status 'Aberta'
    df_abertas = df[df['status'].str.lower() == "aberta"]

    if not df_abertas.empty:
        with st.expander(f"📝 {len(df_abertas)} apostas pendentes encontradas", expanded=True):
            escolha = st.selectbox("Selecione a aposta para dar o resultado:", df_abertas['Busca'].tolist(), key="sel_pendente_2")
            
            id_sel = escolha.split(" | ")[0]
            # Localizamos os dados da linha selecionada
            dados_aposta = df[df['id'].astype(str) == id_sel].iloc[0]
            
            is_dupla = eh_dupla(dados_aposta)

            # LÓGICA PARA APOSTA DUPLA
            if is_dupla:
                st.info(f"📍 **Aposta Combinada detectada.**")
                c_sel1, c_sel2 = st.columns(2)
                
                with c_sel1:
                    st.markdown(f"**Seleção 1:**\n{dados_aposta['mercado']} - {dados_aposta['linha']}")
                    res_sel1 = st.selectbox("Resultado Sel. 1", ["Green", "Red", "Devolvida"], key="res_1_sys2")
                
                with c_sel2:
                    st.markdown(f"**Seleção 2:**\n{dados_aposta['mercado_2']} - {dados_aposta['linha_2']}")
                    res_sel2 = st.selectbox("Resultado Sel. 2", ["Green", "Red", "Devolvida"], key="res_2_sys2")

                # Definição automática do status do bilhete
                if res_sel1 == "Green" and res_sel2 == "Green":
                    status_final = "Green"
                elif res_sel1 == "Red" or res_sel2 == "Red":
                    status_final = "Red"
                elif res_sel1 == "Devolvida" and res_sel2 == "Devolvida":
                    status_final = "Devolvida"
                else:
                    status_final = "Green" if (res_sel1 == "Green" or res_sel2 == "Green") else "Devolvida"

                st.warning(f"O status final do bilhete será: **{status_final}**")
                st1_save, st2_save = res_sel1, res_sel2

            # LÓGICA PARA APOSTA SIMPLES
            else:
                status_final = st.selectbox("Resultado Final:", ["Green", "Meio Green", "Red", "Meio Red", "Devolvida"], key="res_simples_sys2")
                st1_save, st2_save = None, None

            if st.button("Confirmar Resultado", use_container_width=True, key="btn_confirmar_res_2"):
                stake = float(dados_aposta['stake'])
                odd = float(dados_aposta['odd'])
                
                # Recálculo do Lucro
                lucro_final = 0.0
                if status_final == "Green": lucro_final = stake * (odd - 1)
                elif status_final == "Meio Green": lucro_final = (stake * (odd - 1)) / 2
                elif status_final == "Red": lucro_final = -stake
                elif status_final == "Meio Red": lucro_final = -stake / 2

                try:
                    payload = {
                        "status": status_final,
                        "lucro": float(lucro_final),
                        "status_1": st1_save,
                        "status_2": st2_save
                    }
                    supabase.table("apostas_2").update(payload).eq("id", id_sel).execute()
                    
                    st.success(f"✅ Aposta {id_sel} atualizada com sucesso no Sistema 2!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao atualizar no banco: {e}")
    else:
        st.info("✅ Todas as apostas estão resolvidas.")

    st.divider()

    # --- 2. LISTA GERAL COM FILTRO ---
    st.subheader("📋 Lista Geral de Registros")
    
    col_f1, col_f2 = st.columns([1, 2])
    with col_f1:
        data_filtro = st.date_input("📅 Filtrar por dia específica", value=None, key="filtro_data_hist_2")
    
    # Criamos a coluna visual para a tabela
    df['Mercado/Linha'] = df.apply(formatar_mercado_v2, axis=1)

    colunas_exibir = [
        'id', 'data', 'liga', 'mandante', 'visitante', 'Mercado/Linha', 
        'status_1', 'status_2', 'status', 'lucro', 'banca_nome', 'operador'
    ]
    
    cols_existentes = [c for c in colunas_exibir if c in df.columns]
    
    df_filtrado = df.copy()
    if data_filtro:
        df_filtrado = df_filtrado[df_filtrado['data'] == data_filtro]

    df_exibicao = df_filtrado[cols_existentes].sort_values(by=['data', 'id'], ascending=[False, False])
    
    st.dataframe(
        df_exibicao,
        use_container_width=True,
        hide_index=True
    )

    # --- 3. EXCLUIR REGISTRO ---
    st.markdown("---")
    with st.expander("🗑️ Área de Exclusão"):
        item_deletar = st.selectbox("Selecione o registro para apagar:", df['Busca'].tolist(), key="del_box_2")
        if st.button("Excluir Permanentemente", type="primary", key="btn_excluir_hist_2"):
            try:
                id_del = item_deletar.split(" | ")[0]
                supabase.table("apostas_2").delete().eq("id", id_del).execute()
                st.success("Registro removido com sucesso do Sistema 2.")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao deletar: {e}")

if __name__ == "__main__":
    mostrar_historico()
