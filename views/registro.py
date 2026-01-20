import streamlit as st
import pandas as pd
import os
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
    if nome.strip() != "" and nome not in df[df['Tipo'] == tipo]['Nome'].values:
        nova_linha = pd.DataFrame({"Tipo": [tipo], "Nome": [nome]})
        df = pd.concat([df, nova_linha], ignore_index=True)
        df.to_csv(PATH_AUX, index=False)

def mostrar_registro(df_csv):
    st.title("📝 Registro de Aposta")
    
    if not os.path.exists(PATH_BANCAS):
        st.warning("⚠️ Você precisa cadastrar uma Banca primeiro na tela de Bancas!")
        return

    df_bancas = pd.read_csv(PATH_BANCAS)
    df_aux = carregar_auxiliares()

    # --- SELEÇÃO DE LIGA E TIMES (FORA DO FORM PARA FUNCIONAR O FILTRO) ---
    col_f1, col_f2, col_f3 = st.columns(3)
    
    with col_f1:
        liga_sel = st.selectbox("1. Selecione a Liga", sorted(df_csv['Liga'].unique()))
    
    # Filtro em tempo real
    df_filtrado = df_csv[df_csv['Liga'] == liga_sel]
    times = sorted(pd.concat([df_filtrado['Mandande'], df_filtrado['Visitante']]).unique())

    with col_f2:
        mandante = st.selectbox("2. Mandante", times)
    with col_f3:
        visitante = st.selectbox("3. Visitante", [t for t in times if t != mandante])

    st.divider()

    # --- RESTANTE DOS DADOS (DENTRO DO FORM) ---
    with st.form("form_registro", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        
        with c1:
            data_aposta = st.date_input("Data da Aposta", datetime.now())
            banca_sel = st.selectbox("Selecionar Banca", df_bancas["Nome da Banca"].tolist())
            linha = st.text_input("Linha (Ex: -0.5, Over 2.5)")
            
        with c2:
            # Mercado Dinâmico
            mercados_salvos = sorted(df_aux[df_aux['Tipo'] == 'Mercado']['Nome'].tolist())
            mercado_sel = st.selectbox("Mercado Salvo", ["+ Novo Mercado"] + mercados_salvos)
            novo_mercado = st.text_input("Ou digite novo Mercado")
            
            # Método Dinâmico
            metodos_salvos = sorted(df_aux[df_aux['Tipo'] == 'Metodo']['Nome'].tolist())
            metodo_sel = st.selectbox("Método Salvo", ["+ Novo Método"] + metodos_salvos)
            novo_metodo = st.text_input("Ou digite novo Método")
            
        with c3:
            stake = st.number_input("Stake (R$)", min_value=0.0, step=10.0)
            odd = st.number_input("Odd", min_value=1.01, step=0.05)
            obs = st.text_area("Observação", height=110)

        btn_salvar = st.form_submit_button("🚀 Registrar Aposta")

        if btn_salvar:
            mercado_final = novo_mercado if mercado_sel == "+ Novo Mercado" else mercado_sel
            metodo_final = novo_metodo if metodo_sel == "+ Novo Método" else metodo_sel
            
            if not mercado_final or not metodo_final or stake <= 0:
                st.error("Erro: Mercado, Método e Stake são obrigatórios!")
            else:
                if novo_mercado: salvar_auxiliar('Mercado', novo_mercado)
                if novo_metodo: salvar_auxiliar('Metodo', novo_metodo)
                
                nova_aposta = {
                    "Data": data_aposta.strftime('%Y-%m-%d'),
                    "Banca": banca_sel,
                    "Liga": liga_sel,
                    "Jogo": f"{mandante} x {visitante}",
                    "Mercado": mercado_final,
                    "Linha": linha,
                    "Metodo": metodo_final,
                    "Stake": stake,
                    "Odd": odd,
                    "Obs": obs,
                    "Status": "Pendente",
                    "Resultado": 0.0
                }
                
                # Salvar
                if not os.path.exists("data"): os.makedirs("data")
                df_apostas = pd.read_csv(PATH_APOSTAS) if os.path.exists(PATH_APOSTAS) else pd.DataFrame()
                df_apostas = pd.concat([df_apostas, pd.DataFrame([nova_aposta])], ignore_index=True)
                df_apostas.to_csv(PATH_APOSTAS, index=False)
                
                st.success(f"Aposta em {mandante} x {visitante} registrada!")
                st.rerun()
