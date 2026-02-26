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
def carregar_aux_s2(tipo, filtro_pais=None):
    try:
        query = supabase.table("config_auxiliares_2").select("*").eq("tipo", tipo)
        if filtro_pais and filtro_pais != "-":
            query = query.eq("pais_vinculo", filtro_pais.strip().upper())
        res = query.execute()
        return sorted(res.data, key=lambda x: x['nome']) if res.data else []
    except: 
        return []

def carregar_operadores_s2():
    try:
        res = supabase.table("operadores_2").select("*").execute()
        return sorted(res.data, key=lambda x: x['nome']) if res.data else []
    except:
        return []

def carregar_paises_s2():
    try:
        res = supabase.table("config_auxiliares_2").select("pais_vinculo").eq("tipo", "LIGA").execute()
        if res.data:
            paises = set([str(item['pais_vinculo']).strip().upper() for item in res.data if item.get('pais_vinculo')])
            return sorted(list(paises))
        return []
    except:
        return []

def mostrar_registro(df_csv):
    st.title("📝 Registro de Aposta (S2)")
    
    # 1. SEÇÃO: CONFIGURAÇÕES (TABELAS _2)
    st.subheader("⚙️ Configurações do Sistema 2")
    tab_cad, tab_exc = st.tabs(["➕ Adicionar Novo", "🗑️ Excluir Existente"])
    
    with tab_cad:
        col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
        with col_c1:
            tipo_novo = st.selectbox("Tipo", ["LIGA", "MERCADO", "METODO", "OPERADOR"], key="tipo_cad_s2")
        with col_c2:
            nome_novo = st.text_input("Nome", key="nome_cad_s2").strip().upper()
        with col_c3:
            pais_v = st.text_input("País Vinculado", key="pais_cad_s2").strip().upper() if tipo_novo == "LIGA" else None
        
        if st.button("➕ Confirmar Cadastro", key="btn_cad_s2"):
            if nome_novo:
                try:
                    if tipo_novo == "OPERADOR":
                        supabase.table("operadores_2").insert({"nome": nome_novo}).execute()
                    else:
                        payload = {"nome": nome_novo, "tipo": tipo_novo, "pais_vinculo": pais_v if pais_v else None}
                        supabase.table("config_auxiliares_2").insert(payload).execute()
                    st.success(f"{tipo_novo} cadastrado!")
                    time.sleep(1); st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

    with tab_exc:
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            tipo_exc = st.selectbox("Categoria", ["LIGA", "MERCADO", "METODO", "OPERADOR"], key="tipo_exc_s2")
        with col_e2:
            if tipo_exc == "OPERADOR":
                itens = carregar_operadores_s2()
                opcoes_exc = [item['nome'] for item in itens]
            else:
                itens = carregar_aux_s2(tipo_exc)
                opcoes_exc = [f"{item['nome']} ({item.get('pais_vinculo') or 'Global'})" for item in itens]
            item_sel_exc = st.selectbox("Excluir", opcoes_exc if opcoes_exc else ["-"], key="sel_exc_s2")
        
        if st.button("🗑️ Excluir Selecionado", type="primary", key="btn_exc_s2"):
            if item_sel_exc != "-":
                try:
                    nome_real = item_sel_exc.split(" (")[0] if " (" in item_sel_exc else item_sel_exc
                    if tipo_exc == "OPERADOR":
                        supabase.table("operadores_2").delete().eq("nome", nome_real).execute()
                    else:
                        supabase.table("config_auxiliares_2").delete().eq("nome", nome_real).eq("tipo", tipo_exc).execute()
                    st.success("Excluído!"); time.sleep(1); st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

    st.markdown("---")

    # 2. SEÇÃO: REGISTRO INDIVIDUAL
    st.subheader("🎯 Registro Individual (S2)")
    
    c_m1, c_m2 = st.columns(2)
    with c_m1:
        fora_base = st.checkbox("🚩 Jogo fora da Base", key="fora_base_s2")
    with c_m2:
        aposta_dupla = st.checkbox("👯 Aposta Combinada", key="dupla_s2")

    lista_paises = carregar_paises_s2()
    lista_mercados = [item['nome'] for item in carregar_aux_s2("MERCADO")]
    lista_metodos = [item['nome'] for item in carregar_aux_s2("METODO")]
    lista_operadores = [item['nome'] for item in carregar_operadores_s2()]

    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        data_m = st.date_input("Data", datetime.now(), key="data_reg_s2")
    with col_p2:
        pais_sel = st.selectbox("Selecione o País", ["-"] + lista_paises, key="pais_reg_s2")
    with col_p3:
        ligas_filtradas = carregar_aux_s2("LIGA", filtro_pais=pais_sel) if pais_sel != "-" else []
        nomes_ligas = [item['nome'] for item in ligas_filtradas]
        liga_sel = st.selectbox("Liga", nomes_ligas if nomes_ligas else ["-"], key="liga_reg_s2")

    # --- LÓGICA DE EXTRAÇÃO DE TIMES (MENSAGEM AO SISTEMA 1) ---
    lista_times = []
    if not fora_base and liga_sel != "-" and df_csv is not None:
        # 1. Tenta formato do Sistema 1 (Arquivo dados_25_26.csv)
        if 'Liga' in df_csv.columns:
            df_f = df_csv[df_csv['Liga'] == liga_sel]
            if not df_f.empty:
                # Combina mandantes e visitantes para o selectbox
                lista_times = sorted(list(set(df_f['Mandante'].tolist() + df_f['Visitante'].tolist())))
        
        # 2. Se não achou, tenta o formato de Colunas (Ligas_e_Times_Ordenados.csv)
        if not lista_times and liga_sel in df_csv.columns:
            lista_times = sorted(df_csv[liga_sel].dropna().unique().tolist())

    with st.form("form_reg_s2", clear_on_submit=True):
        l2_c1, l2_c2, l2_c3 = st.columns(3)
        with l2_c1:
            mandante = st.text_input("Mandante") if fora_base else st.selectbox("Mandante", ["-"] + lista_times)
        with l2_c2:
            visitante = st.text_input("Visitante") if fora_base else st.selectbox("Visitante", ["-"] + lista_times)
        with l2_c3:
            entrada = st.text_input("Minuto", placeholder="Ex: 25'")

        if aposta_dupla:
            l3_c1, l3_c2 = st.columns(2)
            with l3_c1: merc1 = st.selectbox("Mercado 1", lista_mercados if lista_mercados else ["-"])
            with l3_c2: lin1 = st.text_input("Linha 1")
            l3_c3, l3_c4 = st.columns(2)
            with l3_c3: merc2 = st.selectbox("Mercado 2", lista_mercados if lista_mercados else ["-"])
            with l3_c4: lin2 = st.text_input("Linha 2")
        else:
            l3_c1, l3_c2 = st.columns(2)
            with l3_c1: merc1 = st.selectbox("Mercado", lista_mercados if lista_mercados else ["-"])
            with l3_c2: lin1 = st.text_input("Linha")
            merc2, lin2 = None, None

        l4_c1, l4_c2, l4_c3 = st.columns(3)
        with l4_c1: metodo = st.selectbox("Método", lista_metodos if lista_metodos else ["-"])
        with l4_c2: stake = st.number_input("Valor (R$)", min_value=0.0, step=1.0, format="%.2f")
        with l4_c3: odd = st.number_input("Odd", min_value=1.01, step=0.01, format="%.2f")

        l5_c1, l5_c2, l5_c3 = st.columns(3)
        with l5_c1: operador = st.selectbox("Operador", lista_operadores if lista_operadores else ["-"])
        
        try:
            res_b = supabase.table("bancas_2").select("nome").execute()
            lista_b = [str(b['nome']) for b in res_b.data]
        except: lista_b = []
        
        with l5_c2: banca = st.selectbox("Banca", lista_b if lista_b else ["-"])
        with l5_c3: status = st.selectbox("Status", ["Aberta", "Green", "Meio Green", "Red", "Meio Red", "Devolvida"])

        obs = st.text_input("Observações")

        if st.form_submit_button("🚀 Salvar no Sistema 2"):
            if (not fora_base and (mandante == "-" or visitante == "-")) or (fora_base and (not mandante or not visitante)):
                st.warning("Selecione os times.")
            elif liga_sel == "-":
                st.warning("Selecione a Liga.")
            else:
                lucro = 0.0
                if status == "Green": lucro = stake * (odd - 1)
                elif status == "Meio Green": lucro = (stake * (odd - 1)) / 2
                elif status == "Red": lucro = -stake
                elif status == "Meio Red": lucro = -stake / 2

                d_v2 = {
                    "data": str(data_m), "banca_nome": banca, "liga": liga_sel, "pais": pais_sel,
                    "mandante": mandante, "visitante": visitante, "mercado": merc1,
                    "linha": lin1, "mercado_2": merc2, "linha_2": lin2,
                    "metodo": metodo, "stake": float(stake), "odd": float(odd), 
                    "status": status, "lucro": float(lucro), "obs": obs, 
                    "entrada": entrada, "operador": operador
                }
                try:
                    supabase.table("apostas_2").insert(d_v2).execute()
                    st.success("✅ Salvo no S2!"); time.sleep(1); st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

    st.markdown("---")
