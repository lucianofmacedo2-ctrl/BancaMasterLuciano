import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime
from supabase import create_client

# --- CONFIGURAÇÃO SUPABASE ---
URL = "https://suhpdrqviuzrvygyhxhl.supabase.co"
KEY = "sb_publishable_pM5xDBpqZzo7h5SQqiFcfQ_ixbbydIB"
supabase = create_client(URL, KEY)

# Caminho local para backup
PATH_APOSTAS = "data/historico_apostas.csv"

def carregar_aux(tipo):
    try:
        res = supabase.table("config_auxiliares").select("nome").eq("tipo", tipo).execute()
        return sorted([item['nome'] for item in res.data])
    except: return []

def mostrar_registro(df_csv):
    st.title("📝 Registro de Aposta")
    
    # 1. Busca bancas da nuvem
    try:
        res_b = supabase.table("bancas").select("nome").execute()
        lista_bancas = [b['nome'] for b in res_b.data]
    except: lista_bancas = []

    if not lista_bancas:
        st.warning("⚠️ Cadastre uma Banca primeiro na tela de Bancas!")
        return

    # --- NOVA FUNCIONALIDADE: REGISTRO EM MASSA VIA CSV ---
    with st.expander("📤 REGISTRO EM MASSA (CSV)", expanded=True):
        st.markdown("""
        **Instruções:** Suba um arquivo CSV com as seguintes colunas:
        `data, liga, mandante, visitante, mercado, linha, metodo, stake, odd, status, banca_nome, obs`
        """)
        arquivo_massa = st.file_uploader("Selecione o arquivo CSV", type=["csv"], key="uploader_csv")
        
        if arquivo_massa is not None:
            try:
                df_massa = pd.read_csv(arquivo_massa)
                st.write("📋 Prévia dos dados para importação:", df_massa.head())
                
                if st.button("🚀 Confirmar Importação em Massa"):
                    sucessos = 0
                    erros = 0
                    barra_progresso = st.progress(0)
                    total_linhas = len(df_massa)
                    
                    for i, row in df_massa.iterrows():
                        try:
                            # Cálculo de lucro automático para o banco de dados
                            stk = float(row['stake'])
                            od = float(row['odd'])
                            stt = str(row['status']).strip()
                            luc = 0.0
                            
                            if stt == "Green": luc = stk * (od - 1)
                            elif stt == "Meio Green": luc = (stk * (od - 1)) / 2
                            elif stt == "Red": luc = -stk
                            elif stt == "Meio Red": luc = -stk / 2
                            
                            dados_massa = {
                                "data": str(row['data']),
                                "liga": str(row['liga']),
                                "mandante": str(row['mandante']),
                                "visitante": str(row['visitante']),
                                "mercado": str(row['mercado']),
                                "linha": str(row['linha']),
                                "metodo": str(row['metodo']),
                                "stake": stk,
                                "odd": od,
                                "status": stt,
                                "lucro": float(luc),
                                "banca_nome": str(row['banca_nome']),
                                "obs": str(row['obs']) if pd.notna(row['obs']) else ""
                            }
                            
                            # 1. Salva no Supabase (Nuvem)
                            supabase.table("apostas").insert(dados_massa).execute()
                            
                            # 2. Salva no Local (Backup CSV)
                            if not os.path.exists("data"): os.makedirs("data")
                            df_local = pd.read_csv(PATH_APOSTAS) if os.path.exists(PATH_APOSTAS) else pd.DataFrame()
                            df_local = pd.concat([df_local, pd.DataFrame([dados_massa])], ignore_index=True)
                            df_local.to_csv(PATH_APOSTAS, index=False)
                            
                            sucessos += 1
                        except Exception as e:
                            erros += 1
                            st.error(f"Erro na linha {i+1}: {e}")
                        
                        barra_progresso.progress((i + 1) / total_linhas)
                    
                    st.success(f"✅ Importação Concluída: {sucessos} sucessos!")
                    if erros > 0:
                        st.warning(f"⚠️ Houve erro em {erros} registros.")
                    
                    time.sleep(2)
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao ler o arquivo CSV: {e}")

    st.divider()

    # 2. Gerenciar Mercados e Métodos (Original)
    with st.expander("⚙️ Gerenciar Mercados e Métodos", expanded=False):
        c_aux1, c_aux2 = st.columns(2)
        with c_aux1:
            st.markdown("**📁 Mercados**")
            novo_m = st.text_input("Novo Mercado", key="add_m")
            if st.button("Adicionar Mercado"):
                if novo_m:
                    supabase.table("config_auxiliares").insert({"tipo": "Mercado", "nome": novo_m}).execute()
                    st.success("Adicionado!")
                    time.sleep(0.5)
                    st.rerun()
            
            lista_m = carregar_aux("Mercado")
            if lista_m:
                m_excluir = st.selectbox("Excluir Mercado", ["Selecione..."] + lista_m)
                if m_excluir != "Selecione..." and st.button("❌ Remover Mercado"):
                    supabase.table("config_auxiliares").delete().eq("tipo", "Mercado").eq("nome", m_excluir).execute()
                    st.rerun()

        with c_aux2:
            st.markdown("**🎯 Métodos**")
            novo_met = st.text_input("Novo Método", key="add_met")
            if st.button("Adicionar Método"):
                if novo_met:
                    supabase.table("config_auxiliares").insert({"tipo": "Metodo", "nome": novo_met}).execute()
                    st.success("Adicionado!")
                    time.sleep(0.5)
                    st.rerun()
            
            lista_met = carregar_aux("Metodo")
            if lista_met:
                met_excluir = st.selectbox("Excluir Método", ["Selecione..."] + lista_met)
                if met_excluir != "Selecione..." and st.button("❌ Remover Método"):
                    supabase.table("config_auxiliares").delete().eq("tipo", "Metodo").eq("nome", met_excluir).execute()
                    st.rerun()

    st.divider()
    
    # 3. Seleção de Tipo e Quantidade de Jogos (Original)
    tipo_aposta = st.radio("Tipo de Aposta Manual", ["Simples", "Dupla", "Tripla"], horizontal=True)
    n_jogos = 1 if tipo_aposta == "Simples" else (2 if tipo_aposta == "Dupla" else 3)
    
    jogos_finais = []

    # Gerador de campos dinâmicos baseado na escolha (Simples/Dupla/Tripla)
    for i in range(n_jogos):
        st.markdown(f"#### ⚽ Jogo {i+1}")
        fora_csv = st.checkbox(f"Jogo {i+1} fora do CSV? (Manual)", key=f"fora_{i}")
        col_j1, col_j2, col_j3 = st.columns(3)

        if fora_csv:
            liga = col_j1.text_input("Liga", key=f"liga_{i}")
            mandante = col_j2.text_input("Mandante", key=f"man_{i}")
            visitante = col_j3.text_input("Visitante", key=f"vis_{i}")
        else:
            liga = col_j1.selectbox("Selecione a Liga", sorted(df_csv['Liga'].unique()), key=f"liga_{i}")
            df_filtrado = df_csv[df_csv['Liga'] == liga]
            times = sorted(pd.concat([df_filtrado['Mandante'], df_filtrado['Visitante']]).unique())
            mandante = col_j2.selectbox("Mandante", times, key=f"man_{i}")
            visitante = col_j3.selectbox("Visitante", [t for t in times if t != mandante], key=f"vis_{i}")
        
        jogos_finais.append({"liga": liga, "mandante": mandante, "visitante": visitante})

    # 4. Formulário Financeiro Final (Original)
    st.subheader("📋 Detalhes da Operação Manual")
    with st.form("form_final_aposta", clear_on_submit=True):
        f1, f2, f3, f4 = st.columns(4)
        data_ap = f1.date_input("Data", datetime.now())
        banca_sel = f1.selectbox("Banca", lista_bancas)
        
        mercados_lista = carregar_aux("Mercado")
        mercado_reg = f2.selectbox("Mercado", mercados_lista if mercados_lista else ["Vazio"])
        linha = f2.text_input("Linha (Ex: -1.0 ou Over 2.5)")
        
        metodos_lista = carregar_aux("Metodo")
        metodo_reg = f3.selectbox("Método", metodos_lista if metodos_lista else ["Vazio"])
        status_reg = f3.selectbox("Status", ["Aberta", "Green", "Meio Green", "Red", "Meio Red", "Devolvida"])
        
        stake = f4.number_input("Stake", min_value=0.0, step=10.0)
        odd = f4.number_input("Odd Total", min_value=1.0, step=0.1)
        obs = st.text_input("Observação")
        
        if st.form_submit_button("🚀 Registrar Aposta"):
            # Validação: todos os jogos devem estar preenchidos
            erro_preenchimento = any(not j['mandante'] or not j['visitante'] for j in jogos_finais)
            
            if erro_preenchimento:
                st.error("Preencha os dados de todos os jogos!")
            else:
                # UNIFICAÇÃO DOS DADOS PARA O BANCO DE DADOS
                liga_final = " / ".join(list(set([j['liga'] for j in jogos_finais])))
                mandante_final = " + ".join([j['mandante'] for j in jogos_finais])
                visitante_final = " + ".join([j['visitante'] for j in jogos_finais])

                # Cálculo financeiro
                lucro = 0.0
                if status_reg == "Green": lucro = stake * (odd - 1)
                elif status_reg == "Meio Green": lucro = (stake * (odd - 1)) / 2
                elif status_reg == "Red": lucro = -stake
                elif status_reg == "Meio Red": lucro = -stake / 2

                dados = {
                    "data": data_ap.strftime('%Y-%m-%d'),
                    "liga": liga_final, 
                    "mandante": mandante_final, 
                    "visitante": visitante_final,
                    "mercado": mercado_reg, 
                    "linha": linha, 
                    "metodo": metodo_reg,
                    "stake": float(stake), 
                    "odd": float(odd), 
                    "status": status_reg,
                    "lucro": float(lucro), 
                    "banca_nome": banca_sel, 
                    "obs": obs
                }
                
                try:
                    # 1. Salva na Nuvem (Supabase)
                    supabase.table("apostas").insert(dados).execute()
                    
                    # 2. Salva no Local (Backup CSV)
                    if not os.path.exists("data"): os.makedirs("data")
                    df_local = pd.read_csv(PATH_APOSTAS) if os.path.exists(PATH_APOSTAS) else pd.DataFrame()
                    df_local = pd.concat([df_local, pd.DataFrame([dados])], ignore_index=True)
                    df_local.to_csv(PATH_APOSTAS, index=False)
                    
                    st.balloons()
                    st.success(f"✅ {tipo_aposta} Registrada com sucesso!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")
