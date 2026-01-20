import streamlit as st
import pandas as pd
from database import carregar_apostas

def mostrar_historico():
    st.title("📂 Gestão e Histórico")
    df = carregar_apostas()
    
    if df.empty:
        st.info("Nenhuma aposta registrada.")
        return

    tab1, tab2 = st.tabs(["⏳ Pendentes", "📅 Todas as Entradas"])

    with tab1:
        df_ab = df[df['resultado'] == "Aberto"].copy()
        for idx, row in df_ab.iterrows():
            with st.expander(f"⚽ {row['mandante']} x {row['visitante']}"):
                res = st.selectbox("Resultado", ["Aberto", "Green", "Red", "Half Green", "Half Red", "Void"], key=idx)
                if st.button("Salvar Resultado", key=f"btn_{idx}"):
                    s, o = float(row['stake']), float(row['odd'])
                    if res == "Green": lucro = s * (o - 1)
                    elif res == "Red": lucro = -s
                    elif res == "Half Green": lucro = (s * (o - 1)) / 2
                    elif res == "Half Red": lucro = -s / 2
                    else: lucro = 0
                    
                    df.at[idx, 'resultado'] = res
                    df.at[idx, 'lucro_prejuizo'] = lucro
                    df.to_csv('apostas_registradas.csv', index=False)
                    st.rerun()

    with tab2:
        def color_res(val):
            color = '#2ecc71' if 'Green' in str(val) else ('#e74c3c' if 'Red' in str(val) else 'white')
            return f'color: {color}; font-weight: bold'

        st.dataframe(df.sort_index(ascending=False).style.applymap(color_res, subset=['resultado']).format(precision=2), use_container_width=True)
        st.metric("Lucro Acumulado", f"R$ {df['lucro_prejuizo'].sum():.2f}")
