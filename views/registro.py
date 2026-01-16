import streamlit as st
from database import supabase, carregar_bancas, calcular_lucro_real
from datetime import datetime

def mostrar_registro(df_csv):
    st.title("📝 Nova Entrada")
    df_b = carregar_bancas()
    
    if df_b.empty:
        st.warning("Crie uma banca primeiro.")
        return

    with st.form("form_aposta"):
        banca = st.selectbox("Selecione a Banca", df_b['nome'])
        c1, c2 = st.columns(2)
        mandante = c1.text_input("Mandante")
        visitante = c2.text_input("Visitante")
        
        c3, c4, c5 = st.columns(3)
        mercado = c3.text_input("Mercado")
        odd = c4.number_input("Odd", 1.01, value=1.90)
        stake = c5.number_input("Stake", 1.0, value=50.0)
        
        res_ini = st.selectbox("Resultado", ["Pendente", "Green", "Red", "Meio Green", "Meio Red"])
        
        if st.form_submit_button("SALVAR APOSTA"):
            b_id = int(df_b[df_b['nome'] == banca]['id'].iloc[0])
            lucro = calcular_lucro_real(res_ini, odd, stake)
            supabase.table("apostas").insert({
                "banca_id": b_id, "mandante": mandante, "visitante": visitante,
                "mercado": mercado, "odd": odd, "stake": stake, 
                "resultado": res_ini, "lucro": lucro, "data": str(datetime.now().date())
            }).execute()
            st.success("Aposta registrada!")