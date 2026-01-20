import streamlit as st
from database import salvar_aposta
from datetime import datetime

def mostrar_registro(df_base):
    st.title("📝 Registrar Entrada")
    
    with st.form("form_registro"):
        c1, c2 = st.columns(2)
        liga = c1.selectbox("Liga", df_base['Liga'].unique())
        times = df_base[df_base['Liga'] == liga]['Mandande'].unique()
        
        m = c1.selectbox("Mandante", times)
        v = c2.selectbox("Visitante", [t for t in times if t != m])
        
        mercado = c1.selectbox("Mercado", ["Gols", "Cantos", "Vencedor"])
        linha = c2.text_input("Linha / Seleção")
        
        odd = c1.number_input("Odd", min_value=1.01, value=1.90)
        stake = c2.number_input("Stake (R$)", min_value=1.0, value=10.0)
        
        if st.form_submit_button("Registrar Aposta"):
            nova = {
                'data': datetime.now().strftime("%d/%m/%Y"),
                'mandante': m, 'visitante': v, 'mercado': mercado,
                'linha': linha, 'odd': odd, 'stake': stake,
                'resultado': 'Aberto', 'lucro_prejuizo': 0.0
            }
            salvar_aposta(nova)
            st.success("Aposta registrada!")
