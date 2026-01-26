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

    # --- 1. REGISTRO EM MASSA VIA CSV ---
    with st.expander("📤 REGISTRO EM MASSA (CSV)", expanded=False):
        st.markdown("Suba o arquivo CSV (O sistema detecta automaticamente se usou ',' ou ';').")
        arquivo_massa = st.file_uploader("Selecione o arquivo CSV", type=["csv"], key="uploader_csv")
        
        if arquivo_massa is not None:
            try:
                df_massa = pd.read_csv(arquivo_massa, sep=None, engine='python', encoding='utf-8-sig')
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
                            data_raw = str(row.get('data', '')).strip()
                            data_final = data_raw if data_raw and data_raw != "nan" else datetime.now().strftime('%Y-%m-%d')

                            s_raw = str(row.get('stake', '0')).replace(',', '.').strip()
                            o_raw = str(row.get('odd', '1')).replace(',', '.').strip()
                            stk = float(s_raw) if s_raw != 'nan' else 0.0
                            od = float(o_raw) if o_raw != 'nan' else 1.0
                            
                            stt = str(row.get('status', 'Aberta')).strip()
                            luc = 0.0
                            if stt == "Green": luc = stk * (od - 1)
                            elif stt == "Meio Green": luc = (stk * (od - 1)) / 2
                            elif stt == "Red": luc = -stk
                            elif stt == "Meio Red": luc = -stk / 2
                            
                            dados_massa = {
                                "data": data_final,
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
                                "Data": data_final,
                                "Jogo": f"{dados_massa['mandante']} x {dados_massa['visitante']}",
                                "Status": stt,
                                "Lucro": f"R$ {luc:.2f}"
                            })
                        except Exception as e:
                            erros += 1
                        
                        barra_progresso.progress((i + 1) / total_linhas)
                    
                    if sucessos > 0:
                        st.balloons()
                        st.success(f"🏁 Finalizado! {sucessos} apostas registradas.")
                        st.table(pd.DataFrame(detalhes_sucesso))
                    if erros > 0:
                        st.warning(f"⚠️ {erros} linhas falharam.")
            except Exception as e:
                st.error(f"Erro crítico ao ler arquivo: {str(e)}")

    st.divider()

    # --- 2. REGISTRO MANUAL (UMA A UMA) ---
    st.subheader("🎯 Registro Individual")
    with st.form("form_registro_manual", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            data = st.date_input("Data da Aposta", datetime.now())
            banca = st.selectbox("Banca", lista_bancas)
            liga = st.selectbox("Liga", carregar_aux("LIGA"))
        with col2:
            mandante = st.text_input("Time Mandante")
            visitante = st.text_input("Time Visitante")
            mercado = st.selectbox("Mercado", carregar_aux("MERCADO"))
        with col3:
            linha = st.text_input("Linha / Seleção")
            metodo = st.selectbox("Método", carregar_aux("METODO"))
            status = st.selectbox("Status Inicial", ["Aberta", "Green", "Meio Green", "Red", "Meio Red", "Devolvida"])

        col4, col5, col6 = st.columns(3)
        with col4:
            stake = st.number_input("Valor Apostado (R$)", min_value=0.0, step=1.0, format="%.2f")
        with col5:
            odd = st.number_input("Odd", min_value=1.01, step=0.01, format="%.2f")
        with col6:
            obs = st.text_input("Observações")

        submit = st.form_submit_button("✅ Salvar Aposta Individual")

        if submit:
            if not mandante or not visitante:
                st.error("Preencha os nomes dos times!")
            else:
                # Cálculo do lucro manual
                lucro_manual = 0.0
                if status == "Green": lucro_manual = stake * (odd - 1)
                elif status == "Meio Green": lucro_manual = (stake * (odd - 1)) / 2
                elif status == "Red": lucro_manual = -stake
                elif status == "Meio Red": lucro_manual = -stake / 2

                dados_manual = {
                    "data": str(data),
                    "banca_nome": banca,
                    "liga": liga,
                    "mandante": mandante,
                    "visitante": visitante,
                    "mercado": mercado,
                    "linha": linha,
                    "metodo": metodo,
                    "stake": float(stake),
                    "odd": float(odd),
                    "status": status,
                    "lucro": float(lucro_manual),
                    "obs": obs
                }

                try:
                    supabase.table("apostas").insert(dados_manual).execute()
                    st.success(f"Aposta em {mandante} x {visitante} registrada com sucesso!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar no banco: {e}")

    st.divider()
