import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from supabase import create_client

# --- CONFIGURAÇÃO SUPABASE ---
URL = "https://suhpdrqviuzrvygyhxhl.supabase.co"
KEY = "sb_publishable_pM5xDBpqZzo7h5SQqiFcfQ_ixbbydIB"
supabase = create_client(URL, KEY)

# Caminho local (mantido para backup se você quiser)
PATH_APOSTAS = "data/historico_apostas.csv"

def carregar_aux(tipo):
    try:
        res = supabase.table("config_auxiliares").select("nome").eq("tipo", tipo).execute()
        return sorted([item['nome'] for item in res.data])
    except: return []

def mostrar_registro(df_csv):
    st.title("📝 Registro de Aposta")
    
    # 1. Busca bancas da nuvem
    try:
        res_b = supabase.table("bancas").select("nome").execute()
        lista_bancas = [b['nome'] for b in res_b.data]
    except: lista_bancas = []

    if not lista_bancas:
        st.warning("⚠️ Cadastre uma Banca primeiro na tela de Bancas!")
        return

    # 2. Gerenciar Mercados e Métodos (IGUAL À SUA ANTIGA, MAS NA NUVEM)
    with st.expander("⚙️ Gerenciar Mercados e Métodos", expanded=False):
        c_aux1, c_aux2 = st.columns(2)
        with c_aux1:
            st.markdown("**📁 Mercados**")
            novo_m = st.text_input("Novo Mercado", key="add_m")
            if st.button("Adicionar Mercado"):
                if novo_m:
                    supabase.table("config_auxiliares").insert({"tipo": "Mercado", "nome": novo_m}).execute()
                    st.success("Adicionado!")
                    time.sleep(0.5)
                    st.rerun()
            
            lista_m = carregar_aux("Mercado")
            if lista_m:
                m_excluir = st.selectbox("Excluir Mercado", ["Selecione..."] + lista_m)
                if m_excluir != "Selecione..." and st.button("❌ Remover Mercado"):
                    supabase.table("config_auxiliares").delete().eq("tipo", "Mercado").eq("nome", m_excluir).execute()
                    st.rerun()

        with c_aux2:
            st.markdown("**🎯 Métodos**")
            novo_met = st.text_input("Novo Método", key="add_met")
            if st.button("Adicionar Método"):
                if novo_met:
                    supabase.table("config_auxiliares").insert({"tipo": "Metodo", "nome": novo_met}).execute()
                    st.success("Adicionado!")
                    time.sleep(0.5)
                    st.rerun()
            
            lista_met = carregar_aux("Metodo")
            if lista_met:
                met_excluir = st.selectbox("Excluir Método", ["Selecione..."] + lista_met)
                if met_excluir != "Selecione..." and st.button("❌ Remover Método"):
                    supabase.table("config_auxiliares").delete().eq("tipo", "Metodo").eq("nome", met_excluir).execute()
                    st.rerun()

    st.divider()
    
    # 3. Seleção de Jogo (Igual à antiga)
    fora_csv = st.checkbox("🏟️ Jogo fora do CSV? (Entrada Manual)")
    col_j1, col_j2, col_j3 = st.columns(3)

    if fora_csv:
        liga_final, mandante_final, visitante_final = col_j1.text_input("Liga"), col_j2.text_input("Mandante"), col_j3.text_input("Visitante")
    else:
        liga_sel = col_j1.selectbox("1. Selecione a Liga", sorted(df_csv['Liga'].unique()))
        df_filtrado = df_csv[df_csv['Liga'] == liga_sel]
        times = sorted(pd.concat([df_filtrado['Mandande'], df_filtrado['Visitante']]).unique())
        mandante_final = col_j2.selectbox("2. Mandante", times)
        visitante_final = col_j3.selectbox("3. Visitante", [t for t in times if t != mandante_final])
        liga_final = liga_sel

    # 4. Formulário (Igual à antiga)
    st.subheader("📋 Detalhes da Aposta")
    with st.form("form_final_aposta", clear_on_submit=True):
        f1, f2, f3, f4 = st.columns(4)
        data_ap = f1.date_input("Data", datetime.now())
        banca_sel = f1.selectbox("Banca", lista_bancas)
        
        mercados_lista = carregar_aux("Mercado")
        mercado_reg = f2.selectbox("Mercado", mercados_lista if mercados_lista else ["Vazio"])
        linha = f2.text_input("Linha (Ex: -1.0)")
        
        metodos_lista = carregar_aux("Metodo")
        metodo_reg = f3.selectbox("Método", metodos_lista if metodos_lista else ["Vazio"])
        status_reg = f3.selectbox("Status", ["Aberta", "Green", "Meio Green", "Red", "Meio Red", "Devolvida"])
        
        stake = f4.number_input("Stake", min_value=0.0, step=10.0)
        odd = f4.number_input("Odd", min_value=1.0, step=0.1)
        obs = st.text_input("Observação")
        
        if st.form_submit_button("🚀 Registrar Aposta"):
            if not liga_final or not mandante_final or not visitante_final:
                st.error("Preencha os dados do jogo!")
            else:
                # Cálculo financeiro
                lucro = 0.0
                if status_reg == "Green": lucro = stake * (odd - 1)
                elif status_reg == "Meio Green": lucro = (stake * (odd - 1)) / 2
                elif status_reg == "Red": lucro = -stake
                elif status_reg == "Meio Red": lucro = -stake / 2

                dados = {
                    "data": data_ap.strftime('%Y-%m-%d'),
                    "liga": liga_final, "mandante": mandante_final, "visitante": visitante_final,
                    "mercado": mercado_reg, "linha": linha, "metodo": metodo_reg,
                    "stake": float(stake), "odd": float(odd), "status": status_reg,
                    "lucro": float(lucro), "banca_nome": banca_sel, "obs": obs
                }
                
                try:
                    # Salva na Nuvem
                    supabase.table("apostas").insert(dados).execute()
                    
                    # Salva no Local (Backup CSV)
                    if not os.path.exists("data"): os.makedirs("data")
                    df_local = pd.read_csv(PATH_APOSTAS) if os.path.exists(PATH_APOSTAS) else pd.DataFrame()
                    df_local = pd.concat([df_local, pd.DataFrame([dados])], ignore_index=True)
                    df_local.to_csv(PATH_APOSTAS, index=False)
                    
                    st.balloons()
                    st.success("✅ Aposta Registrada em todo lugar!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
