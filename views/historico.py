import streamlit as st
import pandas as pd
from database import carregar_apostas

def mostrar_historico():
    st.title("📜 Histórico e Gestão de Apostas")

    df = carregar_apostas()
    if df.empty:
        st.info("Nenhuma aposta registrada até o momento.")
        return

    # Organização por Abas
    tab_pendentes, tab_completo = st.tabs(["⏳ Apostas em Aberto", "📅 Histórico Geral"])

    # --- ABA 1: GESTÃO DE APOSTAS ABERTAS ---
    with tab_pendentes:
        df_abertas = df[df['resultado'] == "Aberto"].copy()
        
        if df_abertas.empty:
            st.success("Tudo em dia! Você não possui apostas pendentes.")
        else:
            st.warning(f"Você tem {len(df_abertas)} apostas aguardando resultado.")
            
            for idx, row in df_abertas.iterrows():
                # Card de atualização
                with st.expander(f"⚽ {row['mandante']} x {row['visitante']} ({row['mercado']} {row['linha']})"):
                    st.write(f"**Data:** {row['data']} | **Stake:** R$ {row['stake']} | **Odd:** {row['odd']}")
                    
                    c_update1, c_update2 = st.columns([2, 1])
                    
                    novo_res = c_update1.selectbox(
                        "Qual foi o resultado?", 
                        ["Aberto", "Green", "Red", "Void", "Half Green", "Half Red"], 
                        key=f"sel_{idx}"
                    )
                    
                    if c_update2.button("Atualizar", key=f"btn_{idx}", use_container_width=True):
                        if novo_res != "Aberto":
                            # Recalcular Lucro no momento do fechamento
                            lucro = 0
                            odd, stake = float(row['odd']), float(row['stake'])
                            if novo_res == "Green": lucro = stake * (odd - 1)
                            elif novo_res == "Red": lucro = -stake
                            elif novo_res == "Half Green": lucro = (stake * (odd - 1)) / 2
                            elif novo_res == "Half Red": lucro = -stake / 2
                            
                            # Aplicar mudanças no DataFrame
                            df.at[idx, 'resultado'] = novo_res
                            df.at[idx, 'lucro_prejuizo'] = lucro
                            
                            # Salvar no CSV
                            df.to_csv('apostas_registradas.csv', index=False)
                            st.success("Aposta encerrada com sucesso!")
                            st.rerun()

    # --- ABA 2: HISTÓRICO GERAL ---
    with tab_completo:
        # Filtros básicos para o histórico
        c1, c2 = st.columns(2)
        filtro_res = c1.multiselect("Filtrar por Resultado", df['resultado'].unique())
        if filtro_res:
            df_display = df[df['resultado'].isin(filtro_res)]
        else:
            df_display = df

        # Formatação de cores para a tabela
        def color_resultado(val):
            color = '#2ecc71' if val in ['Green', 'Half Green'] else ('#e74c3c' if val in ['Red', 'Half Red'] else 'white')
            return f'color: {color}; font-weight: bold'

        st.dataframe(
            df_display.sort_index(ascending=False).style.applymap(color_resultado, subset=['resultado']).format(precision=2),
            use_container_width=True
        )

        # Resumo Financeiro Simples
        st.divider()
        total_lucro = df[df['resultado'] != 'Aberto']['lucro_prejuizo'].sum()
        st.metric("Lucro/Prejuízo Total Acumulado", f"R$ {total_lucro:.2f}")
