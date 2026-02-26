import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client

# --- CONFIGURAÇÃO SUPABASE ---
URL = "https://suhpdrqviuzrvygyhxhl.supabase.co"
KEY = "sb_publishable_pM5xDBpqZzo7h5SQqiFcfQ_ixbbydIB"
supabase = create_client(URL, KEY)

# --- FUNÇÕES DE CARREGAMENTO (SISTEMA 2) ---
def carregar_aux_2(tipo, filtro_pais=None):
    try:
        # Usa tabela auxiliar do sistema 2
        query = supabase.table("config_auxiliares_2").select("*").eq("tipo", tipo)
        if filtro_pais and filtro_pais != "-":
            query = query.eq("pais_vinculo", filtro_pais.strip().upper())
        res = query.execute()
        return sorted(res.data, key=lambda x: x['nome'])
    except: 
        return []

def carregar_operadores_2():
    try:
        # Usa tabela de operadores do sistema 2
        res = supabase.table("operadores_2").select("*").execute()
        return sorted(res.data, key=lambda x: x['nome'])
    except:
        return []

def carregar_paises_2():
    try:
        # Paises baseados na tabela auxiliar do sistema 2
        res = supabase.table("config_auxiliares_2").select("pais_vinculo").eq("tipo", "LIGA").execute()
        paises = set([str(item['pais_vinculo']).strip().upper() for item in res.data if item.get('pais_vinculo')])
        return sorted(list(paises))
    except:
        return []

def mostrar_registro(df_csv):
    st.title("📝 Registro de Aposta - Sistema 2")
    
    # 1. SEÇÃO: CONFIGURAÇÕES (CADASTRO E EXCLUSÃO)
    st.subheader("⚙️ Configurações (S2)")
    tab_cad, tab_exc = st.tabs(["➕ Adicionar Novo", "🗑️ Excluir Existente"])
    
    with tab_cad:
        col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
        with col_c1:
            tipo_novo = st.selectbox("Tipo", ["LIGA", "MERCADO", "METODO", "OPERADOR"], key="tipo_cad_2")
        with col_c2:
            nome_novo = st.text_input("Nome (Ex: COLOMBIA 1)", key="nome_cad_2").strip().upper()
        with col_c3:
            pais_v = st.text_input("País Vinculado (Ex: COLOMBIA)", key="pais_cad_2").strip().upper() if tipo_novo == "LIGA" else None
        
        if st.button("➕ Confirmar Cadastro S2"):
            if nome_novo:
                try:
                    if tipo_novo == "OPERADOR":
                        supabase.table("operadores_2").insert({"nome": nome_novo}).execute()
                    else:
                        payload = {"nome": nome_novo, "tipo": tipo_novo, "pais_vinculo": pais_v if pais_v else None}
                        supabase.table("config_auxiliares_2").insert(payload).execute()
                    st.success(f"{tipo_novo} cadastrado com sucesso no Sistema 2!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e: st.error(f"Erro: {e}")
            else: st.warning("Preencha o nome!")

    with tab_exc:
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            tipo_exc = st.selectbox("Categoria para Excluir", ["LIGA", "MERCADO", "METODO", "OPERADOR"], key="tipo_exc_2")
        with col_e2:
            if tipo_exc == "OPERADOR":
                itens = carregar_operadores_2()
                opcoes_exc = [item['nome'] for item in itens]
            else:
                itens = carregar_aux_2(tipo_exc)
                opcoes_exc = [f"{item['nome']} ({item.get('pais_vinculo') or 'Global'})" for item in itens]
            item_sel_exc = st.selectbox("Selecione para excluir", opcoes_exc if opcoes_exc else ["-"], key="item_del_2")
        
        if st.button("🗑️ Excluir Selecionado S2", type="primary"):
            if item_sel_exc != "-":
                try:
                    nome_real = item_sel_exc.split(" (")[0] if " (" in item_sel_exc else item_sel_exc
                    if tipo_exc == "OPERADOR":
                        supabase.table("operadores_2").delete().eq("nome", nome_real).execute()
                    else:
                        supabase.table("config_auxiliares_2").delete().eq("nome", nome_real).eq("tipo", tipo_exc).execute()
                    st.success("Excluído com sucesso no Sistema 2!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

    st.markdown("---")

    # 2. SEÇÃO: REGISTRO INDIVIDUAL (MANUAL)
    st.subheader("🎯 Registro Individual (S2)")
    
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        fora_da_base = st.checkbox("🚩 Jogo fora da Base (S2)", key="fora_base_2")
    with c_m2:
        aposta_dupla = st.checkbox("👯 Combinada (S2)", key="dupla_2")

    # Carregamento das listas S2
    lista_paises = carregar_paises_2()
    lista_mercados = [item['nome'] for item in carregar_aux_2("MERCADO")]
    lista_metodos = [item['nome'] for item in carregar_aux_2("METODO")]
    lista_operadores = [item['nome'] for item in carregar_operadores_2()]

    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        data_m = st.date_input("Data da Aposta", datetime.now(), key="data_reg_2")
    with col_p2:
        pais_selecionado = st.selectbox("País", ["-"] + lista_paises, key="pais_reg_2")
    with col_p3:
        ligas_filtradas = carregar_aux_2("LIGA", filtro_pais=pais_selecionado) if pais_selecionado != "-" else []
        nomes_ligas = [item['nome'] for item in ligas_filtradas]
        liga_selecionada = st.selectbox("Liga", nomes_ligas if nomes_ligas else ["-"], key="liga_reg_2")

    times_mandantes = []
    times_visitantes = []
    
    if not fora_da_base and liga_selecionada != "-":
        df_filtrado = df_csv[df_csv['Liga'] == liga_selecionada]
        if not df_filtrado.empty:
            times_mandantes = sorted(df_filtrado['Mandante'].unique().tolist())
            times_visitantes = sorted(df_filtrado['Visitante'].unique().tolist())

    with st.form("form_registro_manual_2", clear_on_submit=True):
        l2_c1, l2_c2, l2_c3 = st.columns(3)
        with l2_c1: 
            if fora_da_base:
                mandante_m = st.text_input("Mandante")
            else:
                mandante_m = st.selectbox("Mandante", ["-"] + times_mandantes)
        with l2_c2: 
            if fora_da_base:
                visitante_m = st.text_input("Visitante")
            else:
                visitante_m = st.selectbox("Visitante", ["-"] + times_visitantes)
        with l2_c3: entrada_m = st.text_input("Entrada", placeholder="Ex: 25'")

        if aposta_dupla:
            l3_c1, l3_c2 = st.columns(2)
            with l3_c1: mercado_m = st.selectbox("Mercado 1", lista_mercados if lista_mercados else ["-"])
            with l3_c2: linha_m = st.text_input("Seleção 1")
            
            l3_c3, l3_c4 = st.columns(2)
            with l3_c3: mercado_2 = st.selectbox("Mercado 2", lista_mercados if lista_mercados else ["-"])
            with l3_c4: linha_2 = st.text_input("Seleção 2")
        else:
            l3_c1, l3_c2 = st.columns(2)
            with l3_c1: mercado_m = st.selectbox("Mercado", lista_mercados if lista_mercados else ["-"])
            with l3_c2: linha_m = st.text_input("Linha")
            mercado_2, linha_2 = None, None

        l4_c1, l4_c2, l4_c3 = st.columns(3)
        with l4_c1: metodo_m = st.selectbox("Método", lista_metodos if lista_metodos else ["-"])
        with l4_c2: stake_m = st.number_input("Valor (R$)", min_value=0.0, step=1.0, format="%.2f")
        with l4_c3: odd_m = st.number_input("Odd Total", min_value=1.01, step=0.01, format="%.2f")

        l5_c1, l5_c2, l5_c3 = st.columns(3)
        with l5_c1: operador_m = st.selectbox("Operador", lista_operadores if lista_operadores else ["-"])
        try:
            res_b = supabase.table("bancas_2").select("nome").execute()
            lista_bancas = [str
