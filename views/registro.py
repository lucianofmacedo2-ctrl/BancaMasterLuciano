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
        st.markdown("Suba o arquivo CSV (O sistema detecta automaticamente se usou ',' ou ';').")
        arquivo_massa = st.file_uploader("Selecione o arquivo CSV", type=["csv"], key="uploader_csv")
        
        if arquivo_massa is not None:
            try:
                # Lógica robusta para detectar separadores e limpar nomes de colunas
                # Usamos sep=None para o pandas tentar descobrir sozinho (vírgula ou ponto e vírgula)
                df_massa = pd.read_csv(arquivo_massa, sep=None, engine='python', encoding='utf-8-sig')
                
                # Limpa espaços e remove caracteres invisíveis dos nomes das colunas
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
                            # 1. Tratamento da Data (Evita erro de data vazia)
                            data_raw = str(row.get('data', '')).strip()
                            if not data_raw or data_raw == "nan":
                                data_final = datetime.now().strftime('%Y-%m-%d')
                            else:
                                data_final = data_raw

                            # 2. Tratamento de Stake e Odd
                            s_raw = str(row.get('stake', '0')).replace(',', '.').strip()
                            o_raw = str(row.get('odd', '1')).replace(',', '.').strip()
                            stk = float(s_raw) if s_raw != 'nan' else 0.0
                            od = float(o_raw) if o_raw != 'nan' else 1.0
                            
                            # 3. Status e Lucro
                            stt = str(row.get('status', 'Aberta')).strip()
                            luc = 0.0
                            if stt == "Green": luc = stk * (od - 1)
                            elif stt == "Meio Green": luc = (stk * (od - 1)) / 2
                            elif stt == "Red": luc = -stk
                            elif stt == "Meio Red": luc = -stk / 2
                            
                            # Montagem dos dados
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
                            
                            # Envio ao Supabase
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
                st.error(f"Erro crítico ao ler arquivo: {str(e)}")

    st.divider()
    # ... (Restante do código de Registro Manual e Auxiliares permanece igual)
