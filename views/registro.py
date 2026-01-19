import streamlit as st
from datetime import datetime
import pandas as pd
from database import carregar_mercados, salvar_novo_mercado, remover_mercado, salvar_aposta

def mostrar_registro(df_csv):
    st.title("📝 Registro de Aposta")
    
    if df_csv.empty:
        st.warning("Carregue a base de dados para habilitar o registro.")
        return

    # Estilização
    st.markdown("""
        <style>
            input, div[data-baseweb="select"] > div, textarea {
                background-color: white !important;
                color: black !important;
            }
            label p { color: white !important; font-weight: bold; }
            .sessao-mercado {
                background-color: rgba(255, 255, 255, 0.05);
                padding: 20px;
                border-radius: 10px;
                border: 1px solid #00ffcc;
                margin-bottom: 25px;
            }
        </style>
    """, unsafe_allow_html=True)

    # --- 1. SEÇÃO DE GERENCIAMENTO DE MERCADOS ---
    st.markdown('<div class="sessao-mercado">', unsafe_allow_html=True)
    st.subheader("⚙️ Configurar Mercados")
    
    tab1, tab2 = st.tabs(["➕ Adicionar", "🗑️ Remover"])
    
    with tab1:
        c_add1, c_add2 = st.columns([3, 1])
        novo_m = c_add1.text_input("Nome do novo mercado", placeholder="Ex: Chutes ao Gol", key="add_m")
        if c_add2.button("Adicionar", use_container_width=True):
            if salvar_novo_mercado(novo_m):
                st.success("Adicionado!")
                st.rerun()

    with tab2:
        c_rem1, c_rem2 = st.columns([3, 1])
        mercados_atuais = carregar_mercados()
        m_para_remover = c_rem1.selectbox("Selecione para excluir", mercados_atuais, key="rem_m")
        if c_rem2.button("Excluir", use_container_width=True):
            if remover_mercado(m_para_remover):
                st.warning(f"'{m_para_remover}' removido.")
                st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # --- 2. FORMULÁRIO DE REGISTRO (CORRIGIDO) ---
    with st.form("form_registro", clear_on_submit=True):
        c1, c2 = st.columns(2)
        data = c1.date_input("Data da Aposta", datetime.now())
        
        # FILTRO DE LIGA
        ligas_disponiveis = sorted(df_csv['liga'].unique())
        liga = c2.selectbox("Liga", ligas_disponiveis, key="liga_selector")
        
        # FILTRO DE TIMES DINÂMICO BASEADO NA LIGA SELECIONADA
        df_times_filtrados = df_csv[df_csv['liga'] == liga]
        
        # Pegamos os nomes das colunas de mandante e visitante (tratando variações de nome como 'mandande')
        col_mandante = 'mandande' if 'mandande' in df_times_filtrados.columns else 'mandante'
        col_visitante = 'visitante' if 'visitante' in df_times_filtrados.columns else 'visitante'
        
        lista_mandantes = sorted(df_times_filtrados[col_mandante].unique())
        mandante = c1.selectbox("Mandante", lista_mandantes)
        
        # Visitante: filtra para não mostrar o mesmo time que o mandante
        lista_visitantes = sorted(df_times_filtrados[df_times_filtrados[col_mandante] != mandante][col_visitante].unique())
        visitante = c2.selectbox("Visitante", lista_visitantes)

        st.divider()

        c3, c4, c5 = st.columns(3)
        mercado = c3.selectbox("Mercado", carregar_mercados())
        linha = c4.text_input("Linha (ex: 2.5, -1.0)")
        metodo = c5.text_input("Método (Estratégia)")

        c6, c7, c8 = st.columns(3)
        odd = c6.number_input("Odd", min_value=1.01, format="%.2f", step=0.01)
        stake = c7.number_input("Stake (R$)", min_value=1.0, step=1.0)
        resultado = c8.selectbox("Resultado", ["Green", "Red", "Void", "Half Green", "Half Red"])

        obs = st.text_area("Observações")
        
        submit = st.form_submit_button("Confirmar Registro")

        if submit:
            lucro = 0
            if resultado == "Green": lucro = stake * (odd - 1)
            elif resultado == "Red": lucro = -stake
            elif resultado == "Half Green": lucro = (stake * (odd - 1)) / 2
            elif resultado == "Half Red": lucro = -stake / 2
            
            dados = {
                'data': data.strftime('%Y-%m-%d'), 
                'liga': liga, 
                'mandante': mandante,
                'visitante': visitante, 
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
                st.success("Aposta registrada com sucesso!")
            else:
                st.error("Erro ao salvar.")
