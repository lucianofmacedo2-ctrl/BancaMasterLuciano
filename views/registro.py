import streamlit as st
from datetime import datetime
import pandas as pd
from database import salvar_aposta

def mostrar_registro(df_csv):
    st.title("📝 Registro de Aposta")
    
    if df_csv.empty:
        st.warning("A base de dados 'dados_25_26.csv' não foi encontrada ou está vazia.")
        return

    # CSS para Inputs brancos com texto preto
    st.markdown("""
        <style>
            input, div[data-baseweb="select"] > div, textarea {
                background-color: white !important;
                color: black !important;
            }
            label p { color: white !important; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)

    with st.form("form_registro", clear_on_submit=True):
        c1, c2 = st.columns(2)
        data = c1.date_input("Data da Aposta", datetime.now())
        
        # Filtros usando os nomes da sua nova base (padronizados para minúsculas)
        liga = c2.selectbox("Liga", sorted(df_csv['liga'].unique()))

        df_liga = df_csv[df_csv['liga'] == liga]
        # 'mandande' com 'E' conforme você enviou na lista de colunas
        times = sorted(df_liga['mandande'].unique())
        
        mandante = c1.selectbox("Mandante", times)
        visitante = c2.selectbox("Visitante", [t for t in times if t != mandante])

        st.divider()
        
        c3, c4, c5 = st.columns(3)
        mercado = c3.selectbox("Mercado", ["Match Odds", "Over/Under", "Ambas Marcam", "Cantos", "Outros"])
        metodo = c4.text_input("Método / Estratégia", placeholder="Ex: Over 0.5 HT")
        odd = c5.number_input("Odd", min_value=1.01, step=0.01, format="%.2f")

        c6, c7 = st.columns(2)
        stake = c6.number_input("Valor (Stake)", min_value=1.0, step=1.0)
        resultado = c7.selectbox("Resultado", ["Green", "Red", "Void", "Half Green", "Half Red"])

        obs = st.text_area("Observações", placeholder="Detalhes da entrada...")

        submit = st.form_submit_button("Salvar no Banco de Dados")

        if submit:
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
                'metodo': metodo,
                'odd': odd,
                'stake': stake,
                'resultado': resultado,
                'lucro_prejuizo': lucro,
                'obs': obs
            }
            
            if salvar_aposta(dados):
                st.success("Aposta registrada!")
            else:
                st.error("Erro ao salvar.")
