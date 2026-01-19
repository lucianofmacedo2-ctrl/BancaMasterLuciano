import streamlit as st
from datetime import datetime
import pandas as pd
from database import carregar_mercados, salvar_novo_mercado, remover_mercado, salvar_aposta

def mostrar_registro(df_csv):
    st.title("📝 Registro de Aposta")
    
    if df_csv.empty:
        st.warning("Carregue a base de dados para habilitar o registro.")
        return

    # --- 1. GERENCIAMENTO DE MERCADOS ---
    with st.expander("⚙️ Gerenciar Mercados (Adicionar/Remover)"):
        tab1, tab2 = st.tabs(["➕ Adicionar", "🗑️ Remover"])
        with tab1:
            c_add1, c_add2 = st.columns([3, 1])
            novo_m = c_add1.text_input("Novo mercado", key="add_m")
            if c_add2.button("Salvar"):
                if salvar_novo_mercado(novo_m): st.rerun()
        with tab2:
            c_rem1, c_rem2 = st.columns([3, 1])
            m_para_remover = c_rem1.selectbox("Remover", carregar_mercados(), key="rem_m")
            if c_rem2.button("Excluir"):
                if remover_mercado(m_para_remover): st.rerun()

    st.divider()

    # --- 2. SELEÇÃO DA PARTIDA (DINÂMICA) ---
    st.subheader("Seleção da Partida")
    c1, c2 = st.columns(2)
    
    ligas_disponiveis = sorted(df_csv['liga'].unique())
    liga_sel = c1.selectbox("Escolha a Liga", ligas_disponiveis)
    
    df_filtrado = df_csv[df_csv['liga'] == liga_sel]
    col_m = 'mandande' if 'mandande' in df_filtrado.columns else 'mandante'
    
    times_mandantes = sorted(df_filtrado[col_m].unique())
    mandante_sel = c2.selectbox("Mandante", times_mandantes)
    
    times_visitantes = sorted(df_filtrado[df_filtrado[col_m] != mandante_sel]['visitante'].unique())
    visitante_sel = c1.selectbox("Visitante", times_visitantes)
    
    data_sel = c2.date_input("Data", datetime.now())

    # --- 3. DADOS DA APOSTA (FORMULÁRIO) ---
    with st.form("form_final"):
        st.write("---")
        c3, c4, c5 = st.columns(3)
        mercado = c3.selectbox("Mercado", carregar_mercados())
        linha = c4.text_input("Linha (ex: 2.5, -1.0)")
        metodo = c5.text_input("Método (Estratégia)")

        c6, c7, c8 = st.columns(3)
        odd = c6.number_input("Odd", min_value=1.01, format="%.2f", step=0.01)
        stake = c7.number_input("Stake (R$)", min_value=1.0, step=1.0)
        # Adicionado o status "Aberto"
        resultado = c8.selectbox("Resultado", ["Aberto", "Green", "Red", "Void", "Half Green", "Half Red"])

        obs = st.text_area("Observações")
        
        submit = st.form_submit_button("Confirmar Registro da Aposta")

        if submit:
            lucro = 0
            # Lógica de cálculo (Lucro é 0 se estiver Aberto)
            if resultado == "Green": lucro = stake * (odd - 1)
            elif resultado == "Red": lucro = -stake
            elif resultado == "Half Green": lucro = (stake * (odd - 1)) / 2
            elif resultado == "Half Red": lucro = -stake / 2
            
            dados = {
                'data': data_sel.strftime('%Y-%m-%d'), 
                'liga': liga_sel, 
                'mandante': mandante_sel,
                'visitante': visitante_sel, 
                'mercado': mercado, 
                'linha': linha,
                'metodo': metodo, 
                'odd': odd, 
                'stake': stake,
                'resultado': resultado, 
                'lucro_prejuizo': lucro, 
                'obs': obs
            }
            
            if salvar_aposta(dados):
                st.success(f"✅ Aposta registrada como {resultado}!")
                st.balloons()
            else:
                st.error("Erro ao salvar no banco de dados.")
