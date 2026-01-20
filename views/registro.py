import streamlit as st
import pandas as pd
import os
from datetime import datetime

# --- CONFIGURAÇÃO DE CAMINHOS ---
PATH_APOSTAS = "data/historico_apostas.csv"
PATH_AUX = "data/config_auxiliares.csv" # Guarda Mercados e Métodos
PATH_BANCAS = "data/bancas_cadastradas.csv"

def carregar_auxiliares():
    if os.path.exists(PATH_AUX):
        return pd.read_csv(PATH_AUX)
    return pd.DataFrame(columns=["Tipo", "Nome"]) # Tipo: 'Mercado' ou 'Metodo'

def salvar_auxiliar(tipo, nome):
    df = carregar_auxiliares()
    if nome not in df[df['Tipo'] == tipo]['Nome'].values:
        nova_linha = pd.DataFrame({"Tipo": [tipo], "Nome": [nome]})
        df = pd.concat([df, nova_linha], ignore_index=True)
        df.to_csv(PATH_AUX, index=False)

def mostrar_registro(df_csv):
    st.title("📝 Registro de Aposta")
    
    # Verificar se existem bancas
    if not os.path.exists(PATH_BANCAS):
        st.warning("⚠️ Você precisa cadastrar uma Banca primeiro na tela de Bancas!")
        return

    df_bancas = pd.read_csv(PATH_BANCAS)
    df_aux = carregar_auxiliares()

    with st.form("form_registro", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            data_aposta = st.date_input("Data da Aposta", datetime.now())
            banca_sel = st.selectbox("Selecionar Banca", df_bancas["Nome da Banca"].tolist())
            liga_sel = st.selectbox("Liga", sorted(df_csv['Liga'].unique()))
            
        # Filtra times baseados na liga
        df_filtrado = df_csv[df_csv['Liga'] == liga_sel]
        times = sorted(pd.concat([df_filtrado['Mandande'], df_filtrado['Visitante']]).unique())

        with col2:
            mandante = st.selectbox("Mandante", times)
            visitante = st.selectbox("Visitante", [t for t in times if t != mandante])
            
            # --- MERCADO DINÂMICO ---
            mercados_salvos = sorted(df_aux[df_aux['Tipo'] == 'Mercado']['Nome'].tolist())
            mercado_sel = st.selectbox("Mercado (Selecione ou use o campo abaixo)", ["+ Novo Mercado"] + mercados_salvos)
            novo_mercado = st.text_input("Cadastrar Novo Mercado")
            
        with col3:
            linha = st.text_input("Linha (Ex: -0.5, Over 2.5, etc)")
            
            # --- MÉTODO DINÂMICO ---
            metodos_salvos = sorted(df_aux[df_aux['Tipo'] == 'Metodo']['Nome'].tolist())
            metodo_sel = st.selectbox("Método (Selecione ou use o campo abaixo)", ["+ Novo Método"] + metodos_salvos)
            novo_metodo = st.text_input("Cadastrar Novo Método")

        st.divider()
        
        c1, c2, c3 = st.columns([1, 1, 2])
        stake = c1.number_input("Stake (R$)", min_value=0.0, step=10.0)
        odd = c2.number_input("Odd", min_value=1.01, step=0.05)
        obs = c3.text_input("Observação")

        btn_salvar = st.form_submit_button("🚀 Registrar Aposta")

        if btn_salvar:
            # Processa Mercado e Método
            mercado_final = novo_mercado if mercado_sel == "+ Novo Mercado" else mercado_sel
            metodo_final = novo_metodo if metodo_sel == "+ Novo Método" else metodo_sel
            
            if not mercado_final or not metodo_final or stake <= 0:
                st.error("Preencha todos os campos obrigatórios (Mercado, Método e Stake)!")
            else:
                # Salva novos auxiliares se necessário
                if novo_mercado: salvar_auxiliar('Mercado', novo_mercado)
                if novo_metodo: salvar_auxiliar('Metodo', novo_metodo)
                
                # Criar dicionário da aposta
                nova_aposta = {
                    "Data": data_aposta,
                    "Banca": banca_sel,
                    "Liga": liga_sel,
                    "Jogo": f"{mandante} x {visitante}",
                    "Mercado": mercado_final,
                    "Linha": linha,
                    "Metodo": metodo_final,
                    "Stake": stake,
                    "Odd": odd,
                    "Obs": obs,
                    "Status": "Pendente", # Inicia como pendente para validar no histórico
                    "Resultado": 0.0
                }
                
                # Salvar no CSV de Apostas
                df_apostas = pd.read_csv(PATH_APOSTAS) if os.path.exists(PATH_APOSTAS) else pd.DataFrame()
                df_apostas = pd.concat([df_apostas, pd.DataFrame([nova_aposta])], ignore_index=True)
                
                if not os.path.exists("data"): os.makedirs("data")
                df_apostas.to_csv(PATH_APOSTAS, index=False)
                
                st.success("✅ Aposta registrada com sucesso!")
                st.balloons()
                st.rerun()
