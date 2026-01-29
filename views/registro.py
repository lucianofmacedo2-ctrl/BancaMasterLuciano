import streamlit as st
import pandas as pd
import time
from datetime import datetime
from supabase import create_client

# --- CONFIGURAÇÃO SUPABASE ---
URL = "https://suhpdrqviuzrvygyhxhl.supabase.co"
KEY = "sb_publishable_pM5xDBpqZzo7h5SQqiFcfQ_ixbbydIB"
supabase = create_client(URL, KEY)

def carregar_aux(tipo, filtro_pais=None):
    try:
        query = supabase.table("config_auxiliares").select("*").eq("tipo", tipo)
        if filtro_pais:
            query = query.eq("pais_vinculo", filtro_pais)
        res = query.execute()
        return sorted([item for item in res.data], key=lambda x: x['nome'])
    except: 
        return []

def carregar_operadores():
    try:
        res = supabase.table("operadores").select("*").execute()
        return sorted([item for item in res.data], key=lambda x: x['nome'])
    except:
        return []

def carregar_paises():
    try:
        res = supabase.table("config_auxiliares").select("pais_vinculo").neq("pais_vinculo", None).execute()
        paises = set([str(item['pais_vinculo']) for item in res.data if item['pais_vinculo']])
        return sorted(list(paises))
    except:
        return []

def mostrar_registro(df_csv):
    st.title("📝 Registro de Aposta")
    
    # Busca bancas
    try:
        res_b = supabase.table("bancas").select("nome").execute()
        lista_bancas = [str(b['nome']) for b in res_b.data]
    except: 
        lista_bancas = []

    if not lista_bancas:
        st.warning("⚠️ Cadastre uma Banca primeiro na tela de Bancas!")
        return

    # ------------------------------------------------------------------
    # 1. SEÇÃO: CONFIGURAÇÕES (CADASTRO E EXCLUSÃO)
    # ------------------------------------------------------------------
    st.subheader("⚙️ Configurações do Sistema")
    tab_cad, tab_exc = st.tabs(["➕ Adicionar Novo", "🗑️ Excluir Existente"])
    
    with tab_cad:
        col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
        with col_c1:
            tipo_novo = st.selectbox("Tipo", ["LIGA", "MERCADO", "METODO", "OPERADOR"], key="tipo_cad")
        with col_c2:
            nome_novo = st.text_input("Nome", key="nome_cad").strip().upper()
        with col_c3:
            pais_v = st.text_input("País (Só p/ LIGA)", key="pais_cad").strip().upper() if tipo_novo == "LIGA" else None
        
        if st.button("➕ Confirmar Cadastro"):
            if nome_novo:
                try:
                    if tipo_novo == "OPERADOR":
                        supabase.table("operadores").insert({"nome": nome_novo}).execute()
                    else:
                        payload = {"nome": nome_novo, "tipo": tipo_novo, "pais_vinculo": pais_v if pais_v else None}
                        supabase.table("config_auxiliares").insert(payload).execute()
                    st.success("Cadastrado com sucesso!")
                    time.sleep(1); st.rerun()
                except Exception as e: st.error(f"Erro: {e}")
            else: st.warning("Preencha o nome!")

    with tab_exc:
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            tipo_exc = st.selectbox("Categoria para Excluir", ["LIGA", "MERCADO", "METODO", "OPERADOR"], key="tipo_exc")
        with col_e2:
            if tipo_exc == "OPERADOR":
                opcoes = carregar_operadores()
                op_sel = st.selectbox("Selecione o Operador", [item['nome'] for item in opcoes])
            else:
                opcoes = carregar_aux(tipo_exc)
                op_sel = st.selectbox(f"Selecione {tipo_exc}", [f"{item['nome']} ({item.get('pais_vinculo') or 'Global'})" for item in opcoes])
        
        if st.button("🗑️ Excluir Selecionado", type="primary"):
            try:
                nome_real = op_sel.split(" (")[0] if " (" in op_sel else op_sel
                if tipo_exc == "OPERADOR":
                    supabase.table("operadores").delete().eq("nome", nome_real).execute()
                else:
                    supabase.table("config_auxiliares").delete().eq("nome", nome_real).eq("tipo", tipo_exc).execute()
                st.success("Excluído com sucesso!")
                time.sleep(1); st.rerun()
            except Exception as e: st.error(f"Erro: {e}")

    st.markdown("---")

    # ------------------------------------------------------------------
    # 2. SEÇÃO: REGISTRO INDIVIDUAL (MANUAL)
    # ------------------------------------------------------------------
    st.subheader("🎯 Registro Individual")
    
    lista_paises = carregar_paises()
    lista_mercados = [item['nome'] for item in carregar_aux("MERCADO")]
    lista_metodos = [item['nome'] for item in carregar_aux("METODO")]
    lista_operadores = [item['nome'] for item in carregar_operadores()]

    with st.form("form_registro_manual", clear_on_submit=True):
        # LINHA 1: Data - País - Liga
        l1_c1, l1_c2, l1_c3 = st.columns(3)
        with l1_c1: data_m = st.date_input("Data da Aposta", datetime.now())
        with l1_c2: pais_m = st.selectbox("País", ["-"] + lista_paises)
        with l1_c3: 
            ligas_f = carregar_aux("LIGA", filtro_pais=pais_m) if pais_m != "-" else []
            liga_m = st.selectbox("Liga", [item['nome'] for item in ligas_f] if ligas_f else ["-"])

        # LINHA 2: Mandante - Visitante - Entrada
        l2_c1, l2_c2, l2_c3 = st.columns(3)
        with l2_c1: mandante_m = st.text_input("Time Mandante")
        with l2_c2: visitante_m = st.text_input("Time Visitante")
        with l2_c3: entrada_m = st.text_input("Entrada (Minuto)", placeholder="Ex: 25'")

        # LINHA 3: Mercado - Linha - Método
        l3_c1, l3_c2, l3_c3 = st.columns(3)
        with l3_c1: mercado_m = st.selectbox("Mercado", lista_mercados if lista_mercados else ["-"])
        with l3_c2: linha_m = st.text_input("Linha / Seleção")
        with l3_c3: metodo_m = st.selectbox("Método", lista_metodos if lista_metodos else ["-"])

        # LINHA 4: Valor - Odd - Operador
        l4_c1, l4_c2, l4_c3 = st.columns(3)
        with l4_c1: stake_m = st.number_input("Valor Apostado (R$)", min_value=0.0, step=1.0, format="%.2f")
        with l4_c2: odd_m = st.number_input("Odd", min_value=1.01, step=0.01, format="%.2f")
        with l4_c3: operador_m = st.selectbox("Operador", lista_operadores if lista_operadores else ["-"])

        # LINHA 5: Banca - Status - Observações
        l5_c1, l5_c2, l5_c3 = st.columns(3)
        with l5_c1: banca_m = st.selectbox("Banca", lista_bancas)
        with l5_c2: status_m = st.selectbox("Status Inicial", ["Aberta", "Green", "Meio Green", "Red", "Meio Red", "Devolvida"])
        with l5_c3: obs_m = st.text_input("Observações")

        if st.form_submit_button("🚀 Salvar Aposta Individual"):
            if not mandante_m or not visitante_m or liga_m == "-":
                st.warning("⚠️ Preencha os campos obrigatórios.")
            else:
                lucro_calc = 0.0
                if status_m == "Green": lucro_calc = stake_m * (odd_m - 1)
                elif status_m == "Meio Green": lucro_calc = (stake_m * (odd_m - 1)) / 2
                elif status_m == "Red": lucro_calc = -stake_m
                elif status_m == "Meio Red": lucro_calc = -stake_m / 2

                dados = {
                    "data": str(data_m), "banca_nome": banca_m, "liga": liga_m, "pais": pais_m,
                    "mandante": mandante_m, "visitante": visitante_m, "mercado": mercado_m,
                    "linha": linha_m, "metodo": metodo_m, "stake": float(stake_m),
                    "odd": float(odd_m), "status": status_m, "lucro": float(lucro_calc),
                    "obs": obs_m, "entrada": entrada_m, "operador": operador_m
                }
                try:
                    supabase.table("apostas").insert(dados).execute()
                    st.success("✅ Aposta salva!"); time.sleep(1); st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

    st.markdown("---")

    # ------------------------------------------------------------------
    # 3. SEÇÃO: REGISTRO EM MASSA (CSV)
    # ------------------------------------------------------------------
    with st.expander("📤 REGISTRO EM MASSA (CSV)", expanded=False):
        st.markdown("Suba um arquivo CSV para registrar várias apostas. Colunas necessárias: data, pais, liga, mandante, visitante, entrada, mercado, linha, metodo, stake, odd, operador, status, banca_nome, obs.")
        arquivo_massa = st.file_uploader("Selecione o arquivo CSV", type=["csv"], key="uploader_csv_massa")
        
        if arquivo_massa is not None:
            try:
                df_massa = pd.read_csv(arquivo_massa, sep=None, engine='python', encoding='utf-8-sig')
                df_massa.columns = [str(col).strip().lower() for col in df_massa.columns]
                st.write("📋 Prévia:", df_massa.head())
                
                if st.button("🚀 Confirmar Importação"):
                    sucessos, erros = 0, 0
                    barra_p = st.progress(0)
                    total = len(df_massa)
                    
                    for i, row in df_massa.iterrows():
                        try:
                            stt = str(row.get('status', 'Aberta')).strip()
                            stk = float(str(row.get('stake', '0')).replace(',', '.'))
                            od = float(str(row.get('odd', '1')).replace(',', '.'))
                            luc = 0.0
                            if stt == "Green": luc = stk * (od - 1)
                            elif stt == "Meio Green": luc = (stk * (od - 1)) / 2
                            elif stt == "Red": luc = -stk
                            elif stt == "Meio Red": luc = -stk / 2
                            
                            d = {
                                "data": str(row.get('data', datetime.now().strftime('%Y-%m-%d'))),
                                "pais": str(row.get('pais', '')).strip().upper(),
                                "liga": str(row.get('liga', '')).strip().upper(),
                                "mandante": str(row.get('mandante', '')).strip(),
                                "visitante": str(row.get('visitante', '')).strip(),
                                "entrada": str(row.get('entrada', '')),
                                "mercado": str(row.get('mercado', '')).strip().upper(),
                                "linha": str(row.get('linha', '')).strip(),
                                "metodo": str(row.get('metodo', '')).strip().upper(),
                                "stake": stk, "odd": od, "status": stt, "lucro": float(luc),
                                "operador": str(row.get('operador', '')).strip().upper(),
                                "banca_nome": str(row.get('banca_nome', '')).strip(),
                                "obs": str(row.get('obs', '')) if pd.notna(row.get('obs')) else ""
                            }
                            supabase.table("apostas").insert(d).execute()
                            sucessos += 1
                        except: erros += 1
                        barra_p.progress((i + 1) / total)
                    st.success(f"🏁 Concluído! Sucessos: {sucessos} | Erros: {erros}")
                    time.sleep(1); st.rerun()
            except Exception as e: st.error(f"Erro no CSV: {e}")
