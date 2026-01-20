import streamlit as st
import pandas as pd
import os

# --- CAMINHOS ---
PATH_APOSTAS = "data/historico_apostas.csv"

def carregar_apostas():
    if os.path.exists(PATH_APOSTAS):
        df = pd.read_csv(PATH_APOSTAS)
        df['Data'] = pd.to_datetime(df['Data'])
        return df
    return pd.DataFrame()

def salvar_apostas(df):
    df.to_csv(PATH_APOSTAS, index=False)

def mostrar_historico():
    st.title("📂 Histórico de Apostas")

    df = carregar_apostas()

    if df.empty:
        st.info("Nenhuma aposta registrada ainda.")
        return

    # --- FILTROS NO TOPO ---
    with st.expander("🔍 Filtros Avançados", expanded=True):
        c1, c2, c3 = st.columns(3)
        bancas_disp = ["Todas"] + sorted(df['Banca'].unique().tolist())
        banca_f = c1.selectbox("Filtrar por Banca", bancas_disp)
        
        status_disp = ["Todos"] + sorted(df['Status'].unique().tolist())
        status_f = c2.selectbox("Filtrar por Status", status_disp)
        
        # Filtro de lógica
        df_filtrado = df.copy()
        if banca_f != "Todas":
            df_filtrado = df_filtrado[df_filtrado['Banca'] == banca_f]
        if status_f != "Todos":
            df_filtrado = df_filtrado[df_filtrado['Status'] == status_f]

    # --- MÉTRICAS DO FILTRO ---
    lucro_total = df_filtrado['Resultado'].sum()
    roi = (lucro_total / df_filtrado['Stake'].sum() * 100) if df_filtrado['Stake'].sum() > 0 else 0
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Qtd. Apostas", len(df_filtrado))
    m2.metric("Lucro/Prejuízo (P&L)", f"R$ {lucro_total:.2f}", delta=f"{lucro_total:.2f}")
    m3.metric("ROI %", f"{roi:.2f}%")

    st.divider()

    # --- TABELA DE EXIBIÇÃO ---
    # Centralizando os dados conforme seu padrão
    st.subheader("📋 Lista de Registros")
    df_display = df_filtrado.copy()
    df_display['Data'] = df_display['Data'].dt.strftime('%d/%m/%Y')
    
    st.dataframe(
        df_display.style.format({"Stake": "R$ {:.2f}", "Odd": "{:.2f}", "Resultado": "R$ {:.2f}"})
        .set_properties(**{'text-align': 'center'})
        .background_gradient(cmap="RdYlGn", subset=['Resultado']),
        use_container_width=True,
        hide_index=True
    )

    # --- ÁREA DE AÇÕES (EDITAR/EXCLUIR) ---
    st.divider()
    st.subheader("⚙️ Ações")
    
    col_edit, col_del = st.columns(2)

    with col_edit:
        with st.expander("🔄 Atualizar Status de Aposta"):
            # Seleciona a aposta pelo índice e descrição
            opcoes_aposta = {i: f"{r['Data'].strftime('%d/%m')} - {r['Jogo']} ({r['Mercado']})" for i, r in df.iterrows()}
            id_sel = st.selectbox("Selecione a aposta para alterar", options=opcoes_aposta.keys(), format_func=lambda x: opcoes_aposta[x])
            
            novo_status = st.selectbox("Novo Status", ["Aberta", "Green", "Meio Green", "Red", "Meio Red", "Devolvida"], key="edit_status")
            
            if st.button("Confirmar Alteração"):
                # Recalcular resultado financeiro
                stake = df.at[id_sel, 'Stake']
                odd = df.at[id_sel, 'Odd']
                
                res_novo = 0.0
                if novo_status == "Green": res_novo = stake * (odd - 1)
                elif novo_status == "Meio Green": res_novo = (stake * (odd - 1)) / 2
                elif novo_status == "Red": res_novo = -stake
                elif novo_status == "Meio Red": res_novo = -stake / 2
                
                df.at[id_sel, 'Status'] = novo_status
                df.at[id_sel, 'Resultado'] = res_novo
                
                salvar_apostas(df)
                st.success("Status atualizado!")
                st.rerun()

    with col_del:
        with st.expander("🗑️ Excluir Registro"):
            id_del = st.selectbox("Selecione a aposta para remover", options=opcoes_aposta.keys(), format_func=lambda x: opcoes_aposta[x], key="del_ap")
            if st.button("Remover Permanentemente", type="primary"):
                df = df.drop(id_del)
                salvar_apostas(df)
                st.warning("Aposta excluída com sucesso!")
                st.rerun()
