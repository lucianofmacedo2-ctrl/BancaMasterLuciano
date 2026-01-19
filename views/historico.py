import streamlit as st
import pandas as pd
from database import carregar_apostas

def mostrar_historico():
    st.title("📜 Histórico de Apostas")

    df = carregar_apostas()

    if df.empty:
        st.info("Nenhuma aposta registrada até o momento.")
        return

    # --- CSS para Tabelas e Cores de Resultado ---
    st.markdown("""
        <style>
            div[data-testid="stTable"] td { text-align: center !important; color: white !important; }
            div[data-testid="stTable"] th { text-align: center !important; color: white !important; }
        </style>
    """, unsafe_allow_html=True)

    # Ordenar por data mais recente
    df['data'] = pd.to_datetime(df['data']).dt.strftime('%d/%m/%Y')
    df = df.sort_index(ascending=False)

    # --- Filtros Rápidos ---
    c1, c2, c3 = st.columns(3)
    filtro_liga = c1.multiselect("Filtrar Liga", df['liga'].unique())
    filtro_res = c2.multiselect("Filtrar Resultado", df['resultado'].unique())
    filtro_metodo = c3.multiselect("Filtrar Método", df['metodo'].unique() if 'metodo' in df.columns else [])

    if filtro_liga: df = df[df['liga'].isin(filtro_liga)]
    if filtro_res: df = df[df['resultado'].isin(filtro_res)]
    if filtro_metodo: df = df[df['metodo'].isin(filtro_metodo)]

    # --- Tabela Principal ---
    # Reorganizando as colunas para incluir Mercado + Linha
    colunas_exibir = ['data', 'liga', 'mandante', 'visitante', 'mercado', 'linha', 'metodo', 'odd', 'stake', 'resultado', 'lucro_prejuizo']
    
    # Verifica se todas as colunas existem no DF para evitar erros
    colunas_finais = [c for c in colunas_exibir if c in df.columns]
    
    # Formatação visual: Green em verde, Red em vermelho (opcional via Pandas Styler)
    def color_resultado(val):
        color = '#2ecc71' if val == 'Green' or val == 'Half Green' else ('#e74c3c' if val == 'Red' or val == 'Half Red' else 'white')
        return f'color: {color}; font-weight: bold'

    st.table(df[colunas_finais].style.applymap(color_resultado, subset=['resultado']).format(precision=2))

    # --- Seção de Detalhes (Observações) ---
    st.subheader("📝 Detalhes e Observações")
    for _, row in df.head(10).iterrows():
        with st.expander(f"📌 {row['data']} - {row['mandante']} x {row['visitante']} ({row['mercado']} {row['linha']})"):
            c_obs1, c_obs2 = st.columns(2)
            c_obs1.write(f"**Método:** {row.get('metodo', 'N/A')}")
            c_obs1.write(f"**Odd:** {row['odd']} | **Stake:** R$ {row['stake']}")
            c_obs2.write(f"**Lucro/Prejuízo:** R$ {row['lucro_prejuizo']:.2f}")
            st.info(f"**Observação:** {row.get('obs', 'Sem observações.')}")
