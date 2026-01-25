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
        st.markdown("Suba o arquivo CSV com as colunas: `data, liga, mandante, visitante, mercado, linha, metodo, stake, odd, status, banca_nome, obs`")
        arquivo_massa = st.file_uploader("Selecione o arquivo CSV", type=["csv"], key="uploader_csv")
        
        if arquivo_massa is not None:
            try:
                # Carrega garantindo que não haja confusão entre tipos
                df_massa = pd.read_csv(arquivo_massa)
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
                            # Tratamento robusto de números - Converte para string antes de tratar
                            s_val = str(row.get('stake', '0')).replace(',', '.').strip()
                            o_val = str(row.get('odd', '1')).replace(',', '.').strip()
                            
                            stk = float(s_val)
                            od = float(o_val)
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
                            
                            # Backup Local
                            if not os.path.exists("data"): os.makedirs("data")
                            df_local = pd.read_csv(PATH_APOSTAS) if os.path.exists(PATH_APOSTAS) else pd.DataFrame()
                            df_local = pd.concat([df_local, pd.DataFrame([dados_massa])], ignore_index=True)
                            df_local.to_csv(PATH_APOSTAS, index=False)
                            
                            detalhes_sucesso.append({
                                "Data": dados_massa['data'],
                                "Jogo": f"{dados_massa['mandante']} x {dados_massa['visitante']}",
                                "Status": stt,
                                "Lucro": f"R$ {luc:.2f}"
                            })
                            sucessos += 1
                        except Exception as e:
                            erros += 1
                            st.error(f"Erro na linha {i+1}: {str(e)}")
                        
                        barra_progresso.progress((i + 1) / total_linhas)
                    
                    st.divider()
                    st.balloons()
                    st.success(f"🏁 Finalizado! {sucessos} apostas registradas.")
                    
                    if detalhes_sucesso:
                        st.markdown("### ✅ Bilhetes Confirmados:")
                        st.table(pd.DataFrame(detalhes_sucesso))
                    
                    if erros > 0:
                        st.warning(f"⚠️ {erros} linhas falharam.")
                    
                    if st.button("🔄 Recarregar Página"):
                        st.rerun()
            except Exception as e:
                st.error(f"Erro crítico ao processar arquivo: {str(e)}")

    st.divider()

    # --- GERENCIAR AUXILIARES (IGUAL AO ANTERIOR) ---
    with st.expander("⚙️ Gerenciar Mercados e Métodos", expanded=False):
        c_aux1, c_aux2 = st.columns(2)
        with c_aux1:
            st.markdown("**📁 Mercados**")
            novo_m = st.text_input("Novo Mercado", key="add_m")
            if st.button("Adicionar Mercado"):
                if novo_m:
                    supabase.table("config_auxiliares").insert({"tipo": "Mercado", "nome": str(novo_m)}).execute()
                    st.success("Adicionado!"); time.sleep(0.5); st.rerun()
            lista_m = carregar_aux("Mercado")
            if lista_m:
                m_ex = st.selectbox("Excluir Mercado", ["Selecione..."] + lista_m)
                if m_ex != "Selecione..." and st.button("❌ Remover Mercado"):
                    supabase.table("config_auxiliares").delete().eq("tipo", "Mercado").eq("nome", m_ex).execute()
                    st.rerun()
        with c_aux2:
            st.markdown("**🎯 Métodos**")
            novo_met = st.text_input("Novo Método", key="add_met")
            if st.button("Adicionar Método"):
                if novo_met:
                    supabase.table("config_auxiliares").insert({"tipo": "Metodo", "nome": str(novo_met)}).execute()
                    st.success("Adicionado!"); time.sleep(0.5); st.rerun()
            lista_met = carregar_aux("Metodo")
            if lista_met:
                met_ex = st.selectbox("Excluir Método", ["Selecione..."] + lista_met)
                if met_ex != "Selecione..." and st.button("❌ Remover Método"):
                    supabase.table("config_auxiliares").delete().eq("tipo", "Metodo").eq("nome", met_ex).execute()
                    st.rerun()

    st.divider()
    
    # --- REGISTRO MANUAL ---
    tipo_ap = st.radio("Registro Manual", ["Simples", "Dupla", "Tripla"], horizontal=True)
    n_jogos = 1 if tipo_ap == "Simples" else (2 if tipo_ap == "Dupla" else 3)
    jogos_finais = []
    for i in range(n_jogos):
        st.markdown(f"#### ⚽ Jogo {i+1}")
        fora_csv = st.checkbox(f"Jogo {i+1} fora do CSV? (Manual)", key=f"fora_{i}")
        col1, col2, col3 = st.columns(3)
        if fora_csv:
            liga = col1.text_input("Liga", key=f"l_{i}")
            man = col2.text_input("Mandante", key=f"m_{i}")
            vis = col3.text_input("Visitante", key=f"v_{i}")
        else:
            liga = col1.selectbox("Liga", sorted(df_csv['Liga'].unique()), key=f"l_{i}")
            df_f = df_csv[df_csv['Liga'] == liga]
            times = sorted(pd.concat([df_f['Mandante'], df_f['Visitante']]).unique())
            man = col2.selectbox("Mandante", times, key=f"m_{i}")
            vis = col3.selectbox("Visitante", [t for t in times if t != man], key=f"v_{i}")
        jogos_finais.append({"liga": liga, "mandante": man, "visitante": vis})

    with st.form("form_manual", clear_on_submit=True):
        f1, f2, f3, f4 = st.columns(4)
        data_ap = f1.date_input("Data", datetime.now())
        banca_sel = f1.selectbox("Banca", lista_bancas)
        mercado_reg = f2.selectbox("Mercado", carregar_aux("Mercado"))
        linha = f2.text_input("Linha")
        metodo_reg = f3.selectbox("Método", carregar_aux("Metodo"))
        status_reg = f3.selectbox("Status", ["Aberta", "Green", "Meio Green", "Red", "Meio Red", "Devolvida"])
        stake = f4.number_input("Stake", min_value=0.0, step=1.0)
        odd = f4.number_input("Odd", min_value=1.0, step=0.1)
        obs = st.text_input("Observação")
        
        if st.form_submit_button("🚀 Registrar Aposta Manual"):
            liga_f = " / ".join(list(set([str(j['liga']) for j in jogos_finais])))
            man_f = " + ".join([str(j['mandante']) for j in jogos_finais])
            vis_f = " + ".join([str(j['visitante']) for j in jogos_finais])
            lucro = 0.0
            if status_reg == "Green": lucro = stake * (odd - 1)
            elif status_reg == "Meio Green": lucro = (stake * (odd - 1)) / 2
            elif status_reg == "Red": lucro = -stake
            elif status_reg == "Meio Red": lucro = -stake / 2
            dados = {
                "data": data_ap.strftime('%Y-%m-%d'), "liga": liga_f, "mandante": man_f, 
                "visitante": vis_f, "mercado": mercado_reg, "linha": linha, 
                "metodo": metodo_reg, "stake": float(stake), "odd": float(odd), 
                "status": status_reg, "lucro": float(lucro), "banca_nome": banca_sel, "obs": obs
            }
            try:
                supabase.table("apostas").insert(dados).execute()
                st.balloons(); st.success("Registrado!"); time.sleep(1); st.rerun()
            except Exception as e: st.error(f"Erro: {str(e)}")
