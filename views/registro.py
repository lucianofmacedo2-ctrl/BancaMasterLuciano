import streamlit as st
from datetime import datetime
import pandas as pd
from database import carregar_mercados, salvar_novo_mercado, salvar_aposta

def mostrar_registro(df_csv):
    st.title("📝 Registro de Aposta")
    
    if df_csv.empty:
        st.warning("Carregue a base de dados para habilitar o registro.")
        return

    # --- CSS PARA DEIXAR OS CAMPOS BRANCOS E TEXTO PRETO ---
    st.markdown("""
        <style>
            input, div[data-baseweb="select"] > div, textarea {
                background-color: white !important;
                color: black !important;
            }
            label p { color: white !important; font-weight: bold; }
            .sessao-cadastro {
                background-color: rgba(255, 255, 255, 0.1);
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 20px;
                border: 1px solid #00ffcc;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- 1. SEÇÃO DE CADASTRO DE MERCADO (FIXA E VISÍVEL) ---
    st.markdown('<div class="sessao-cadastro">', unsafe_allow_html=True)
    st.subheader("➕ Novo Mercado")
    c_add1, c_add2 = st.columns([3, 1])
    
    novo_m = c_add1.text_input("Digite o nome do mercado (ex: Handicap, Chutes...)", key="input_novo_mercado")
    if c_add2.button("Cadastrar", use_container_width=True):
        if novo_m:
            if salvar_novo_mercado(novo_m):
                st.success(f"'{novo_m}' adicionado!")
                st.rerun()
            else:
                st.warning("Este mercado já existe.")
        else:
            st.error("Digite um nome.")
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 2. FORMULÁRIO DE REGISTRO ---
    with st.form("form_registro", clear_on_submit=True):
        c1, c2 = st.columns(2)
        data = c1.date_input("Data da Aposta", datetime.now())
        
        # Filtro de Liga e Times
        liga = c2.selectbox("Liga", sorted(df_csv['liga'].unique()))
        df_l = df_csv[df_csv['liga'] == liga]
        mandante = c1.selectbox("Mandante", sorted(df_l['mandande'].unique()))
        visitante = c2.selectbox("Visitante", sorted(df_l[df_l['mandande'] != mandante]['visitante'].unique()))

        st.divider()

        # Seleção do Mercado (que agora inclui os novos cadastrados)
        c3, c4, c5 = st.columns(3)
        lista_mercados = carregar_mercados()
        mercado = c3.selectbox("Mercado", lista_mercados)
        linha = c4.text_input("Linha (ex: 2.5, -1.0, 5.5)") # Campo Linha que você pediu
        metodo = c5.text_input("Método", placeholder="Ex: Funil")

        # Odds e Valores
        c6, c7, c8 = st.columns(3)
        odd = c6.number_input("Odd", min_value=1.01, format="%.2f", step=0.01)
        stake = c7.number_input("Stake", min_value=1.0, step=1.0)
        resultado = c8.selectbox("Resultado", ["Green", "Red", "Void", "Half Green", "Half Red"])

        obs = st.text_area("Observações da Partida")
        
        submit = st.form_submit_button("Confirmar Registro")

        if submit:
            # Cálculo de Lucro
            lucro = 0
            if resultado == "Green": lucro = stake * (odd - 1)
            elif resultado == "Red": lucro = -stake
            elif resultado == "Half Green": lucro = (stake * (odd - 1)) / 2
            elif resultado == "Half Red": lucro = -stake / 2
            
            dados = {
                'data': data.strftime('%Y-%m-%d'),
                'liga': liga,
                'mandante': mandante,
                'visitante': visitante,
                'mercado': mercado,
                'linha': linha,
                'metodo': metodo,
                'odd': odd,
                'stake': stake,
                'resultado': resultado,
                'lucro_prejuizo': lucro,
                'obs': obs
            }
            
            if salvar_aposta(dados):
                st.success(f"Aposta em {mercado} {linha} salva com sucesso!")
            else:
                st.error("Erro ao salvar no CSV.")
