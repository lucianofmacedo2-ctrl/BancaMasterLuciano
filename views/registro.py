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

PATH_APOSTAS = "data/historico_apostas.csv"

def carregar_aux(tipo):
    try:
        res = supabase.table("config_auxiliares").select("nome").eq("tipo", tipo).execute()
        return sorted([str(item['nome']) for item in res.data])
    except: return []

def mostrar_registro(df_csv):
    st.title("📝 Registro de Aposta")
    
    try:
        res_b = supabase.table("bancas").select("nome").execute()
        lista_bancas = [str(b['nome']) for b in res_b.data]
    except: lista_bancas = []

    if not lista_bancas:
        st.warning("⚠️ Cadastre uma Banca primeiro na tela de Bancas!")
        return

    # --- REGISTRO EM MASSA VIA CSV ---
    with st.expander("📤 REGISTRO EM MASSA (CSV)", expanded=True):
        st.markdown("Suba o arquivo CSV (O sistema agora aceita tanto vírgula quanto ponto e vírgula).")
        arquivo_massa = st.file_uploader("Selecione o arquivo CSV", type=["csv"], key="uploader_csv")
        
        if arquivo_massa is not None:
            try:
                # Tenta ler com vírgula, se falhar ou criar só 1 coluna, tenta ponto e vírgula
                df_massa = pd.read_csv(arquivo_massa, sep=None, engine='python')
                df_massa.columns = [str(col).strip().lower() for col in df_massa.columns]
                
                st.write("📋 Prévia dos dados detectados:", df_massa.head())
                
                if st.button("🚀 Confirmar Importação em Massa"):
                    sucessos = 0
                    erros = 0
                    detalhes_sucesso = []
                    barra_progresso = st.progress(0)
                    total_linhas = len(df_massa)
                    
                    for i, row in df_massa.iterrows():
                        try:
                            # Tratamento de Stake e Odd
                            s_raw = str(row.get('stake', '0')).replace(',', '.').strip()
                            o_raw = str(row.get('odd', '1')).replace(',', '.').strip()
                            
                            stk = float(s_raw)
                            od = float(o_raw)
                            stt = str(row.get('status', 'Aberta')).strip()
                            luc = 0.0
                            
                            if stt == "Green": luc = stk * (od - 1)
                            elif stt == "Meio Green": luc = (stk * (od - 1)) / 2
                            elif stt == "Red": luc = -stk
                            elif stt == "Meio Red": luc = -stk / 2
                            
                            dados_massa = {
                                "data": str(row.get('data', '')).strip(),
                                "liga": str(row.get('liga', '')).strip(),
                                "mandante": str(row.get('mandante', '')).strip(),
                                "visitante": str(row.get('visitante', '')).strip(),
                                "mercado": str(row.get('mercado', '')).strip(),
                                "linha": str(row.get('linha', '')).strip(),
                                "metodo": str(row.get('metodo', '')).strip(),
                                "stake": stk,
                                "odd": od,
                                "status": stt,
                                "lucro": float(luc),
                                "banca_nome": str(row.get('banca_nome', '')).strip(),
                                "obs": str(row.get('obs', '')) if pd.notna(row.get('obs')) else ""
                            }
                            
                            supabase.table("apostas").insert(dados_massa).execute()
                            sucessos += 1
                            
                            detalhes_sucesso.append({
                                "Data": dados_massa['data'],
                                "Jogo": f"{dados_massa['mandante']} x {dados_massa['visitante']}",
                                "Status": stt,
                                "Lucro": f"R$ {luc:.2f}"
                            })
                        except Exception as e:
                            erros += 1
                            st.error(f"Erro na linha {i+1}: {str(e)}")
                        
                        barra_progresso.progress((i + 1) / total_linhas)
                    
                    st.divider()
                    if sucessos > 0:
                        st.balloons()
                        st.success(f"🏁 Finalizado! {sucessos} apostas registradas.")
                        st.table(pd.DataFrame(detalhes_sucesso))
                    if erros > 0:
                        st.warning(f"⚠️ {erros} linhas falharam.")
                    st.button("🔄 Recarregar Página", on_click=st.rerun)

            except Exception as e:
                st.error(f"Erro crítico: {str(e)}")

    st.divider()

    # --- RESTANTE DO CÓDIGO (MANUAL E AUXILIARES) ---
    with st.expander("⚙️ Gerenciar Mercados e Métodos", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**📁 Mercados**")
            novo_m = st.text_input("Novo Mercado", key="add_m")
            if st.button("Adicionar Mercado") and novo_m:
                supabase.table("config_auxiliares").insert({"tipo": "Mercado", "nome": str(novo_m)}).execute()
                st.rerun()
        with c2:
            st.markdown("**🎯 Métodos**")
            novo_met = st.text_input("Novo Método", key="add_met")
            if st.button("Adicionar Método") and novo_met:
                supabase.table("config_auxiliares").insert({"tipo": "Metodo", "nome": str(novo_met)}).execute()
                st.rerun()

    tipo_ap = st.radio("Registro Manual", ["Simples", "Dupla", "Tripla"], horizontal=True)
    n_jogos = 1 if tipo_ap == "Simples" else (2 if tipo_ap == "Dupla" else 3)
    jogos_finais = []
    for i in range(n_jogos):
        st.markdown(f"#### ⚽ Jogo {i+1}")
        col1, col2, col3 = st.columns(3)
        liga = col1.selectbox("Liga", sorted(df_csv['Liga'].unique()), key=f"l_{i}")
        df_f = df_csv[df_csv['Liga'] == liga]
        times = sorted(pd.concat([df_f['Mandante'], df_f['Visitante']]).unique())
        man = col2.selectbox("Mandante", times, key=f"m_{i}")
        vis = col3.selectbox("Visitante", [t for t in times if t != man], key=f"v_{i}")
        jogos_finais.append({"liga": liga, "mandante": man, "visitante": vis})

    with st.form("form_manual"):
        f1, f2, f3, f4 = st.columns(4)
        data_ap = f1.date_input("Data", datetime.now())
        banca_sel = f1.selectbox("Banca", lista_bancas)
        mercado_reg = f2.selectbox("Mercado", carregar_aux("Mercado"))
        linha = f2.text_input("Linha")
        metodo_reg = f3.selectbox("Método", carregar_aux("Metodo"))
        status_reg = f3.selectbox("Status", ["Aberta", "Green", "Meio Green", "Red", "Meio Red", "Devolvida"])
        stake = f4.number_input("Stake", min_value=0.0, step=1.0)
        odd = f4.number_input("Odd", min_value=1.0, step=0.1)
        if st.form_submit_button("🚀 Registrar Aposta Manual"):
            # Lógica de inserção manual (igual à anterior)
            pass
