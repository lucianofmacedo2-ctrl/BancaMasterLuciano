import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime

# --- CONFIGURAÇÃO DE CAMINHOS ---
PATH_APOSTAS = "data/historico_apostas.csv"
PATH_AUX = "data/config_auxiliares.csv"
PATH_BANCAS = "data/bancas_cadastradas.csv"

def carregar_auxiliares():
    if os.path.exists(PATH_AUX):
        return pd.read_csv(PATH_AUX)
    return pd.DataFrame(columns=["Tipo", "Nome"])

def salvar_auxiliar(tipo, nome):
    df = carregar_auxiliares()
    nome = nome.strip()
    if nome != "" and nome not in df[df['Tipo'] == tipo]['Nome'].values:
        nova_linha = pd.DataFrame({"Tipo": [tipo], "Nome": [nome]})
        df = pd.concat([df, nova_linha], ignore_index=True)
        df.to_csv(PATH_AUX, index=False)
        return True
    return False

def excluir_auxiliar(tipo, nome):
    df = carregar_auxiliares()
    df = df[~((df['Tipo'] == tipo) & (df['Nome'] == nome))]
    df.to_csv(PATH_AUX, index=False)

def mostrar_registro(df_csv):
    st.title("📝 Registro de Aposta")
    
    if not os.path.exists(PATH_BANCAS):
        st.warning("⚠️ Você precisa cadastrar uma Banca primeiro na tela de Bancas!")
        return

    # --- ÁREA DE GESTÃO (MERCADOS E MÉTODOS) NO TOPO ---
    with st.expander("⚙️ Gerenciar Mercados e Métodos", expanded=False):
        c_aux1, c_aux2 = st.columns(2)
        with c_aux1:
            st.markdown("**📁 Mercados**")
            novo_m = st.text_input("Novo Mercado", key="add_m")
            if st.button("Adicionar Mercado"):
                if salvar_auxiliar('Mercado', novo_m):
                    st.success(f"Mercado adicionado!")
                    time.sleep(0.5)
                    st.rerun()
            df_m = carregar_auxiliares()
            lista_m = df_m[df_m['Tipo'] == 'Mercado']['Nome'].tolist()
            if lista_m:
                m_excluir = st.selectbox("Excluir Mercado", ["Selecione..."] + sorted(lista_m), key="del_m")
                if m_excluir != "Selecione..." and st.button("❌ Remover Mercado"):
                    excluir_auxiliar('Mercado', m_excluir)
                    st.rerun()

        with c_aux2:
            st.markdown("**🎯 Métodos**")
            novo_met = st.text_input("Novo Método", key="add_met")
            if st.button("Adicionar Método"):
                if salvar_auxiliar('Metodo', novo_met):
                    st.success(f"Método adicionado!")
                    time.sleep(0.5)
                    st.rerun()
            df_met = carregar_auxiliares()
            lista_met = df_met[df_met['Tipo'] == 'Metodo']['Nome'].tolist()
            if lista_met:
                met_excluir = st.selectbox("Excluir Método", ["Selecione..."] + sorted(lista_met), key="del_met")
                if met_excluir != "Selecione..." and st.button("❌ Remover Método"):
                    excluir_auxiliar('Metodo', met_excluir)
                    st.rerun()

    st.divider()

    # --- NOVA OPÇÃO: JOGO FORA DO CSV ---
    fora_csv = st.checkbox("🏟️ Jogo fora do CSV? (Entrada Manual)")

    df_bancas = pd.read_csv(PATH_BANCAS)
    df_aux = carregar_auxiliares()
    
    col_j1, col_j2, col_j3 = st.columns(3)

    if fora_csv:
        liga_final = col_j1.text_input("Liga (Manual)")
        mandante_final = col_j2.text_input("Mandante (Manual)")
        visitante_final = col_j3.text_input("Visitante (Manual)")
    else:
        liga_sel = col_j1.selectbox("1. Selecione a Liga", sorted(df_csv['Liga'].unique()))
        df_filtrado = df_csv[df_csv['Liga'] == liga_sel]
        times = sorted(pd.concat([df_filtrado['Mandande'], df_filtrado['Visitante']]).unique())
        
        mandante_final = col_j2.selectbox("2. Mandante", times)
        visitante_final = col_j3.selectbox("3. Visitante", [t for t in times if t != mandante_final])
        liga_final = liga_sel

    # --- FORMULÁRIO DE REGISTRO ---
    st.subheader("📋 Detalhes da Aposta")
    with st.form("form_final_aposta", clear_on_submit=True):
        f1, f2, f3, f4 = st.columns(4)
        
        with f1:
            data_aposta = st.date_input("Data", datetime.now())
            banca_sel = st.selectbox("Banca", df_bancas["Nome da Banca"].tolist())

        with f2:
            mercados_finais = sorted(df_aux[df_aux['Tipo'] == 'Mercado']['Nome'].tolist())
            mercado_reg = st.selectbox("Mercado", mercados_finais if mercados_finais else ["Vazio"])
            linha = st.text_input("Linha (Ex: -1.0, +0.5)")
            
        with f3:
            metodos_finais = sorted(df_aux[df_aux['Tipo'] == 'Metodo']['Nome'].tolist())
            metodo_reg = st.selectbox("Método", metodos_finais if metodos_finais else ["Vazio"])
            status_reg = st.selectbox("Status", ["Aberta", "Green", "Meio Green", "Red", "Meio Red", "Devolvida"])
            
        with f4:
            stake = st.number_input("Stake (R$)", min_value=0.0, step=10.0)
            odd = st.number_input("Odd", min_value=1.01, step=0.05)
            
        obs = st.text_input("Observação")
        
        btn_final = st.form_submit_button("🚀 Registrar Aposta")

        if btn_final:
            if not liga_final or not mandante_final or not visitante_final:
                st.error("Erro: Preencha os dados do jogo (Liga e Times)!")
            elif not mercados_finais or not metodos_finais or stake <= 0:
                st.error("Erro: Verifique Mercado/Método e Stake!")
            else:
                # GERAÇÃO DO ID ÚNICO PARA O HISTÓRICO
                id_unico = f"{datetime.now().strftime('%M%S')}-{mandante_final[:3].upper().replace(' ', '')}"

                # Cálculo financeiro
                resultado_fin = 0.0
                if status_reg == "Green": resultado_fin = stake * (odd - 1)
                elif status_reg == "Meio Green": resultado_fin = (stake * (odd - 1)) / 2
                elif status_reg == "Red": resultado_fin = -stake
                elif status_reg == "Meio Red": resultado_fin = -stake / 2

                nova_aposta = {
                    "ID": id_unico, # Inclusão da nova coluna
                    "Data": data_aposta.strftime('%Y-%m-%d'),
                    "Banca": banca_sel,
                    "Liga": liga_final,
                    "Jogo": f"{mandante_final} x {visitante_final}",
                    "Mercado": mercado_reg,
                    "Linha": linha,
                    "Metodo": metodo_reg,
                    "Stake": stake,
                    "Odd": odd,
                    "Status": status_reg,
                    "Resultado": resultado_fin,
                    "Obs": obs
                }
                
                # Salvar em CSV com proteção de colunas
                if not os.path.exists("data"): os.makedirs("data")
                df_apostas = pd.read_csv(PATH_APOSTAS) if os.path.exists(PATH_APOSTAS) else pd.DataFrame()
                
                # Garante que o arquivo existente tenha a coluna ID antes de salvar a nova
                if not df_apostas.empty and "ID" not in df_apostas.columns:
                    df_apostas.insert(0, "ID", "Antiga")

                df_apostas = pd.concat([df_apostas, pd.DataFrame([nova_aposta])], ignore_index=True)
                df_apostas.to_csv(PATH_APOSTAS, index=False)
                
                st.balloons()
                st.success(f"✅ Aposta ID: {id_unico} registrada!")
                time.sleep(2)
                st.rerun()
