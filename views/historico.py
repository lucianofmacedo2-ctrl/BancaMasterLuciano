import streamlit as st
import pandas as pd
from database import carregar_apostas

def mostrar_historico():
    st.title("📂 Gestão de Entradas")
    df = carregar_apostas()
    
    if df.empty:
        st.info("Nenhuma aposta registrada.")
        return

    tab1, tab2 = st.tabs(["⏳ Resolver Pendentes", "📜 Histórico Completo"])

    with tab1:
        df_ab = df[df['resultado'] == "Aberto"].copy()
        for idx, row in df_ab.iterrows():
            with st.expander(f"⚽ {row['mandante']} x {row['visitante']} | {row['mercado']}"):
                res = st.selectbox("Resultado", ["Aberto", "Green", "Red", "Half Green", "Half Red", "Void"], key=f"h_{idx}")
                if st.button("Salvar", key=f"b_{idx}"):
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
        def style_res(v):
            color = '#2ecc71' if 'Green' in str(v) else ('#e74c3c' if 'Red' in str(v) else 'white')
            return f'color: {color}; font-weight: bold'
        
        st.dataframe(df.sort_index(ascending=False).style.applymap(style_res, subset=['resultado']).format(precision=2), use_container_width=True)
        st.metric("Lucro Acumulado", f"R$ {df['lucro_prejuizo'].sum():.2f}")
