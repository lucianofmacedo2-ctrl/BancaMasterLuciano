import streamlit as st
import pandas as pd
from database import carregar_apostas

def mostrar_historico():
    st.title("📜 Histórico e Gestão de Apostas")
    df = carregar_apostas()
    
    if df.empty:
        st.info("Nenhuma aposta registrada.")
        return

    tab_abertas, tab_geral = st.tabs(["⏳ Apostas em Aberto", "📅 Histórico Total"])

    with tab_abertas:
        df_abertas = df[df['resultado'] == "Aberto"].copy()
        if df_abertas.empty:
            st.success("Não há apostas pendentes!")
        else:
            for idx, row in df_abertas.iterrows():
                with st.expander(f"⚽ {row['mandante']} x {row['visitante']} ({row['mercado']})"):
                    st.write(f"Odd: {row['odd']} | Stake: R$ {row['stake']}")
                    
                    c1, c2 = st.columns([2, 1])
                    novo_res = c1.selectbox("Resultado", ["Aberto", "Green", "Red", "Void", "Half Green", "Half Red"], key=f"res_{idx}")
                    
                    if c2.button("Atualizar", key=f"btn_{idx}"):
                        lucro = 0
                        s, o = float(row['stake']), float(row['odd'])
                        
                        if novo_res == "Green": lucro = s * (o - 1)
                        elif novo_res == "Red": lucro = -s
                        elif novo_res == "Half Green": lucro = (s * (o - 1)) / 2
                        elif novo_res == "Half Red": lucro = -s / 2
                        
                        df.at[idx, 'resultado'] = novo_res
                        df.at[idx, 'lucro_prejuizo'] = lucro
                        df.to_csv('apostas_registradas.csv', index=False)
                        st.rerun()

    with tab_geral:
        # Estilo de cores
        def color_resultado(val):
            if "Green" in str(val): color = '#2ecc71'
            elif "Red" in str(val): color = '#e74c3c'
            else: color = 'white'
            return f'color: {color}; font-weight: bold'

        st.dataframe(
            df.sort_index(ascending=False).style.applymap(color_resultado, subset=['resultado']).format(precision=2),
            use_container_width=True
        )
        
        lucro_total = df['lucro_prejuizo'].sum()
        st.metric("Lucro/Prejuízo Total", f"R$ {lucro_total:.2f}", delta=f"{lucro_total:.2f}")
