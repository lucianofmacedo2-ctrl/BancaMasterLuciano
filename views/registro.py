import streamlit as st
from datetime import datetime
import pandas as pd
from database import salvar_aposta

def mostrar_registro(df_csv):
    st.title("📝 Registro de Aposta")
    
    if df_csv.empty:
        st.warning("Carregue a base de dados para habilitar o registro.")
        return

    # CSS para Inputs brancos com texto preto e Labels em branco
    st.markdown("""
        <style>
            input, div[data-baseweb="select"] > div, textarea {
                background-color: white !important;
                color: black !important;
            }
            label p { color: white !important; font-weight: bold; }
            .stForm { background-color: rgba(255,255,255,0.05); padding: 20px; border-radius: 10px; }
        </style>
    """, unsafe_allow_html=True)

    with st.form("form_registro", clear_on_submit=True):
        c1, c2 = st.columns(2)
        data = c1.date_input("Data da Aposta", datetime.now())
        
        # Usando 'liga' em minúsculo conforme padronizado no database.py
        liga = c2.selectbox("Liga", sorted(df_csv['liga'].unique()))

        # Filtragem de times baseada na liga selecionada
        df_liga = df_csv[df_csv['liga'] == liga]
        times = sorted(df_liga['mandante'].unique())
        
        mandante = c1.selectbox("Mandante", times)
        visitante = c2.selectbox("Visitante", [t for t in times if t != mandante])

        st.divider()
        
        c3, c4, c5 = st.columns(3)
        mercado = c3.selectbox("Mercado", ["Match Odds", "Over/Under", "Ambas Marcam", "Cantos", "Outros"])
        # NOVO CAMPO: Método
        metodo = c4.text_input("Método / Estratégia", placeholder="Ex: Funil, BTTS, Back...")
        odd = c5.number_input("Odd da Entrada", min_value=1.01, step=0.01, format="%.2f")

        c6, c7 = st.columns(2)
        stake = c6.number_input("Valor da Stake", min_value=1.0, step=1.0)
        resultado = c7.selectbox("Resultado", ["Green", "Red", "Void", "Half Green", "Half Red"])

        # NOVO CAMPO: Observação
        obs = st.text_area("Observações da Partida", placeholder="Ex: Time pressionando muito, expulsão aos 20 min...")

        submit = st.form_submit_button("Confirmar Registro")

        if submit:
            # Cálculo de Lucro/Prejuízo Real
            lucro = 0
            if resultado == "Green": lucro = stake * (odd - 1)
            elif resultado == "Red": lucro = -stake
            elif resultado == "Half Green": lucro = (stake * (odd - 1)) / 2
            elif resultado == "Half Red": lucro = -stake / 2
            elif resultado == "Void": lucro = 0
            
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
                st.success(f"Sucesso! Aposta em {mandante} x {visitante} salva no histórico.")
            else:
                st.error("Falha ao salvar aposta. Verifique as permissões do arquivo.")
