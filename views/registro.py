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

def carregar_aux(tipo):
    try:
        res = supabase.table("config_auxiliares").select("nome").eq("tipo", tipo).execute()
        return sorted([str(item['nome']) for item in res.data])
    except: 
        return []

def mostrar_registro(df_csv):
    st.title("📝 Registro de Aposta")
    
    # Busca bancas do Supabase
    try:
        res_b = supabase.table("bancas").select("nome").execute()
        lista_bancas = [str(b['nome']) for b in res_b.data]
    except: 
        lista_bancas = []

    if not lista_bancas:
        st.warning("⚠️ Cadastre uma Banca primeiro na tela de Bancas!")
        return

    # ------------------------------------------------------------------
    # 1. SEÇÃO: REGISTRO EM MASSA (CSV)
    # ------------------------------------------------------------------
    with st.expander("📤 REGISTRO EM MASSA (CSV)", expanded=False):
        st.markdown("Suba um arquivo CSV para registrar várias apostas de uma vez.")
        arquivo_massa = st.file_uploader("Selecione o arquivo CSV", type=["csv"], key="uploader_csv_massa")
        
        if arquivo_massa is not None:
            try:
                # Detecta separador automaticamente
                df_massa = pd.read_csv(arquivo_massa, sep=None, engine='python', encoding='utf-8-sig')
                df_massa.columns = [str(col).strip().lower() for col in df_massa.columns]
                
                st.write("📋 Prévia dos dados detectados:", df_massa.head())
                
                if st.button("🚀 Confirmar Importação em Massa"):
                    sucessos = 0
                    erros = 0
                    barra_progresso = st.progress(0)
                    total_linhas = len(df_massa)
                    
                    for i, row in df_massa.iterrows():
                        try:
                            # Tratamento de Data
                            data_raw = str(row.get('data', '')).strip()
                            data_f = data_raw if data_raw and data_raw != "nan" else datetime.now().strftime('%Y-%m-%d')
                            
                            # Tratamento de Valores
                            stk = float(str(row.get('stake', '0')).replace(',', '.'))
                            od = float(str(row.get('odd', '1')).replace(',', '.'))
                            stt = str(row.get('status', 'Aberta')).strip()
                            
                            # Cálculo de Lucro
                            luc = 0.0
                            if stt == "Green": luc = stk * (od - 1)
                            elif stt == "Meio Green": luc = (stk * (od - 1)) / 2
                            elif stt == "Red": luc = -stk
                            elif stt == "Meio Red": luc = -stk / 2
                            
                            dados_massa = {
                                "data": data_f,
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
                        except:
                            erros += 1
                        barra_progresso.progress((i + 1) / total_linhas)
                    
                    st.success(f"🏁 Processo concluído! Sucessos: {sucessos} | Erros: {erros}")
                    time.sleep(2)
                    st.rerun()
            except Exception as e:
                st.error(f"Erro ao processar CSV: {e}")

    st.markdown("---")

    # ------------------------------------------------------------------
    # 2. SEÇÃO: REGISTRO INDIVIDUAL (O FORMULÁRIO QUE SUMIU)
    # ------------------------------------------------------------------
    st.subheader("🎯 Registro Individual (Uma a uma)")
    
    # Carrega as listas auxiliares para os selectboxes
    lista_ligas = carregar_aux("LIGA")
    lista_mercados = carregar_aux("MERCADO")
    lista_metodos = carregar_aux("METODO")

    with st.form("form_registro_manual", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            data_m = st.date_input("Data da Aposta", datetime.now())
            banca_m = st.selectbox("Banca", lista_bancas)
            liga_m = st.selectbox("Liga", lista_ligas if lista_ligas else ["-"])
        with col2:
            mandante_m = st.text_input("Time Mandante")
            visitante_m = st.text_input("Time Visitante")
            mercado_m = st.selectbox("Mercado", lista_mercados if lista_mercados else ["-"])
        with col3:
            linha_m = st.text_input("Linha / Seleção")
            metodo_m = st.selectbox("Método", lista_metodos if lista_metodos else ["-"])
            status_m = st.selectbox("Status Inicial", ["Aberta", "Green", "Meio Green", "Red", "Meio Red", "Devolvida"])

        col4, col5, col6 = st.columns(3)
        with col4:
            stake_m = st.number_input("Valor Apostado (R$)", min_value=0.0, step=1.0, format="%.2f")
        with col5:
            odd_m = st.number_input("Odd", min_value=1.01, step=0.01, format="%.2f")
        with col6:
            obs_m = st.text_input("Observações")

        submit_manual = st.form_submit_button("✅ Salvar Aposta Individual")

        if submit_manual:
            if not mandante_m or not visitante_m:
                st.warning("⚠️ Por favor, preencha o nome dos times.")
            else:
                # Cálculo do lucro para o registro manual
                lucro_calc = 0.0
                if status_m == "Green": lucro_calc = stake_m * (odd_m - 1)
                elif status_m == "Meio Green": lucro_calc = (stake_m * (odd_m - 1)) / 2
                elif status_m == "Red": lucro_calc = -stake_m
                elif status_m == "Meio Red": lucro_calc = -stake_m / 2

                dados_manual = {
                    "data": str(data_m),
                    "banca_nome": banca_m,
                    "liga": liga_m,
                    "mandante": mandante_m,
                    "visitante": visitante_m,
                    "mercado": mercado_m,
                    "linha": linha_m,
                    "metodo": metodo_m,
                    "stake": float(stake_m),
                    "odd": float(odd_m),
                    "status": status_m,
                    "lucro": float(lucro_calc),
                    "obs": obs_m
                }

                try:
                    supabase.table("apostas").insert(dados_manual).execute()
                    st.success(f"Aposta em {mandante_m} x {visitante_m} salva com sucesso!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar no Supabase: {e}")
