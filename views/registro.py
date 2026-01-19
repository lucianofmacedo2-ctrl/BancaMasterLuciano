import streamlit as st
from datetime import datetime
from database import carregar_mercados, salvar_novo_mercado, salvar_aposta

def mostrar_registro(df_csv):
    st.title("📝 Registro de Aposta")
    
    if df_csv.empty:
        st.warning("Carregue a base de dados primeiro.")
        return

    # Estilização de alto contraste
    st.markdown("<style>input, textarea, div[data-baseweb='select'] > div { background-color: white !important; color: black !important; } label p { color: white !important; font-weight: bold; }</style>", unsafe_allow_html=True)

    # --- Seção de Cadastro de Mercado ---
    with st.expander("➕ Cadastrar Novo Mercado"):
        c_add1, c_add2 = st.columns([3, 1])
        novo_m = c_add1.text_input("Nome do Mercado (ex: Handicap Asiático, Chutes ao Gol)")
        if c_add2.button("Salvar Mercado"):
            if novo_m:
                salvar_novo_mercado(novo_m)
                st.success("Mercado cadastrado!")
                st.rerun()

    with st.form("form_registro", clear_on_submit=True):
        c1, c2 = st.columns(2)
        data = c1.date_input("Data", datetime.now())
        liga = c2.selectbox("Liga", sorted(df_csv['liga'].unique()))
        
        df_l = df_csv[df_csv['liga'] == liga]
        mandante = c1.selectbox("Mandante", sorted(df_l['mandande'].unique()))
        visitante = c2.selectbox("Visitante", sorted(df_l[df_l['mandande'] != mandante]['visitante'].unique()))

        st.divider()

        # Linha de Mercado, Linha da Aposta e Método
        c3, c4, c5 = st.columns(3)
        lista_mercados = carregar_mercados()
        mercado = c3.selectbox("Mercado", lista_mercados)
        linha = c4.text_input("Linha (ex: 2.5, -1.0, 5.5)", placeholder="Digite a linha")
        metodo = c5.text_input("Método", placeholder="Ex: Funil")

        # Odds, Stake e Resultado
        c6, c7, c8 = st.columns(3)
        odd = c6.number_input("Odd", min_value=1.01, format="%.2f", step=0.01)
        stake = c7.number_input("Stake", min_value=1.0, step=1.0)
        resultado = c8.selectbox("Resultado", ["Green", "Red", "Void", "Half Green", "Half Red"])

        obs = st.text_area("Observações Adicionais")
        
        submit = st.form_submit_button("Finalizar Registro")

        if submit:
            # Cálculo de Lucro
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
                'linha': linha, # Novo dado
                'metodo': metodo,
                'odd': odd,
                'stake': stake,
                'resultado': resultado,
                'lucro_prejuizo': lucro,
                'obs': obs
            }
            
            if salvar_aposta(dados):
                st.success(f"Aposta em {mercado} {linha} registrada!")
            else:
                st.error("Erro ao salvar.")
