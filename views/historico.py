import streamlit as st
from database import carregar_apostas, supabase, calcular_lucro_real

def mostrar_historico():
    st.title("📂 Histórico de Apostas")
    df = carregar_apostas()
    
    if df.empty:
        st.info("Histórico vazio.")
        return

    config = {
        "resultado": st.column_config.SelectboxColumn("Resultado", options=["Pendente", "Green", "Red", "Meio Green", "Meio Red"]),
        "lucro": st.column_config.NumberColumn("Lucro", disabled=True)
    }
    
    editado = st.data_editor(df, column_config=config, use_container_width=True, hide_index=True)
    
    if st.button("💾 Salvar Alterações"):
        for i, row in editado.iterrows():
            novo_lucro = calcular_lucro_real(row['resultado'], row['odd'], row['stake'])
            supabase.table("apostas").update({
                "resultado": row['resultado'], "lucro": novo_lucro
            }).eq("id", row['id']).execute()
        st.rerun()