import streamlit as st
from datetime import datetime
from database import salvar_aposta

def mostrar_registro(df_csv):
    st.title("📝 Registro de Aposta")
    
    if df_csv.empty:
        st.warning("Base de dados não carregada.")
        return

    st.markdown("<style>input, textarea { background-color: white !important; color: black !important; }</style>", unsafe_allow_html=True)

    with st.form("form_registro", clear_on_submit=True):
        c1, c2 = st.columns(2)
        data = c1.date_input("Data", datetime.now())
        liga = c2.selectbox("Liga", sorted(df_csv['liga'].unique()))
        
        df_l = df_csv[df_csv['liga'] == liga]
        mandante = c1.selectbox("Mandante", sorted(df_l['mandande'].unique()))
        visitante = c2.selectbox("Visitante", sorted(df_l[df_l['mandande'] != mandante]['visitante'].unique()))

        c3, c4, c5 = st.columns(3)
        mercado = c3.selectbox("Mercado", ["Match Odds", "Over/Under", "Ambas Marcam", "Cantos"])
        metodo = c4.text_input("Método", placeholder="Ex: Funil")
        odd = c5.number_input("Odd", min_value=1.01, format="%.2f")

        c6, c7 = st.columns(2)
        stake = c6.number_input("Stake", min_value=1.0)
        resultado = c7.selectbox("Resultado", ["Green", "Red", "Void", "Half Green", "Half Red"])

        obs = st.text_area("Observações")
        submit = st.form_submit_button("Registrar")

        if submit:
            lucro = 0
            if resultado == "Green": lucro = stake * (odd - 1)
            elif resultado == "Red": lucro = -stake
            # ... (outros cálculos aqui)
            
            dados = {
                'data': data.strftime('%Y-%m-%d'), 'liga': liga, 'mandante': mandante,
                'visitante': visitante, 'mercado': mercado, 'metodo': metodo,
                'odd': odd, 'stake': stake, 'resultado': resultado, 
                'lucro_prejuizo': lucro, 'obs': obs
            }
            if salvar_aposta(dados):
                st.success("Registrado!")
