import streamlit as st
import pandas as pd
import os
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
                    
                    c_up1, c_up2, c_up3 = st.columns([2, 1, 1])
                    
                    # Seleção de resultado completa
                    novo_res = c_up1.selectbox(
                        "Qual foi o resultado?", 
                        ["Aberto", "Green", "Red", "Void", "Half Green", "Half Red"], 
                        key=f"sel_{idx}"
                    )
                    
                    # Botão de Atualizar com lógica financeira completa
                    if c_up2.button("Atualizar", key=f"btn_up_{idx}", use_container_width=True):
                        if novo_res != "Aberto":
                            lucro = 0
                            odd = float(row['odd'])
                            stake = float(row['stake'])
                            
                            if novo_res == "Green": 
                                lucro = stake * (odd - 1)
                            elif novo_res == "Red": 
                                lucro = -stake
                            elif novo_res == "Half Green": 
                                lucro = (stake * (odd - 1)) / 2
                            elif novo_res == "Half Red": 
                                lucro = -stake / 2
                            elif novo_res == "Void":
                                lucro = 0
                            
                            df.at[idx, 'resultado'] = novo_res
                            df.at[idx, 'lucro_prejuizo'] = lucro
                            df.to_csv('apostas_registradas.csv', index=False)
                            st.success(f"Aposta encerrada como {novo_res}!")
                            st.rerun()

                    # BOTÃO DE EXCLUIR
                    if c_up3.button("❌ Excluir", key=f"btn_del_{idx}", use_container_width=True):
                        df = df.drop(idx)
                        df.to_csv('apostas_registradas.csv', index=False)
                        st.warning("Aposta removida com sucesso!")
                        st.rerun()

    # --- ABA 2: HISTÓRICO GERAL ---
    with tab_completo:
        st.subheader("Todas as Entradas")
        
        # Filtros rápidos
        c_f1, c_f2 = st.columns(2)
        filtro_res = c_f1.multiselect("Filtrar por Resultado", df['resultado'].unique())
        
        df_display = df[df['resultado'].isin(filtro_res)] if filtro_res else df

        # Opção de exclusão por ID
        with st.expander("🗑️ Excluir por ID (Erro de Digitação)"):
            c_del1, c_del2 = st.columns([3, 1])
            id_para_excluir = c_del1.number_input("ID da aposta (número à esquerda)", min_value=0, max_value=20000, step=1)
            if c_del2.button("Confirmar Exclusão", use_container_width=True):
                if id_para_excluir in df.index:
                    df = df.drop(id_para_excluir)
                    df.to_csv('apostas_registradas.csv', index=False)
                    st.error(f"Aposta {id_para_excluir} removida!")
                    st.rerun()
                else:
                    st.error("ID não encontrado.")

        st.divider()

        # Formatação de cores para a tabela
        def color_resultado(val):
            if val in ['Green', 'Half Green']: color = '#2ecc71' # Verde
            elif val in ['Red', 'Half Red']: color = '#e74c3c'   # Vermelho
            elif val == 'Void': color = '#f1c40f'               # Amarelo
            else: color = 'white'
            return f'color: {color}; font-weight: bold'

        # Exibição da Tabela Estilizada
        st.dataframe(
            df_display.sort_index(ascending=False).style.applymap(color_resultado, subset=['resultado']).format(precision=2),
            use_container_width=True
        )

        # Resumo Financeiro
        st.divider()
        total_lucro = df[df['resultado'] != 'Aberto']['lucro_prejuizo'].sum()
        
        # Cor do metric baseado no lucro
        label_color = "normal" if total_lucro >= 0 else "inverse"
        st.metric("Lucro/Prejuízo Total Acumulado", f"R$ {total_lucro:.2f}", delta=f"{total_lucro:.2f}")
