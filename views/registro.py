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
        return sorted([item['nome'] for item in res.data])
    except: return []

def mostrar_registro(df_csv):
    st.title("📝 Registro de Aposta")
    
    # 1. Busca bancas
    try:
        res_b = supabase.table("bancas").select("nome").execute()
        lista_bancas = [b['nome'] for b in res_b.data]
    except: lista_bancas = []

    if not lista_bancas:
        st.warning("⚠️ Cadastre uma Banca primeiro!")
        return

    # --- GERENCIAR MERCADOS E MÉTODOS (Omitido para focar na Múltipla) ---
    # ... (Seu código original de expander continua aqui igual)

    st.divider()
    
    # 2. SELEÇÃO DE TIPO DE APOSTA
    tipo_aposta = st.radio("Tipo de Aposta", ["Simples", "Dupla", "Tripla"], horizontal=True)
    num_jogos = 1 if tipo_aposta == "Simples" else (2 if tipo_aposta == "Dupla" else 3)
    
    jogos_finais = []
    
    # 3. GERADOR DINÂMICO DE JOGOS
    for i in range(num_jogos):
        st.markdown(f"**⚽ Jogo {i+1}**")
        fora_csv = st.checkbox(f"Jogo {i+1} fora do CSV?", key=f"manual_{i}")
        c1, c2, c3 = st.columns(3)
        
        if fora_csv:
            l = c1.text_input("Liga", key=f"l_{i}")
            m = c2.text_input("Mandante", key=f"m_{i}")
            v = c3.text_input("Visitante", key=f"v_{i}")
        else:
            l = c1.selectbox("Liga", sorted(df_csv['Liga'].unique()), key=f"l_{i}")
            df_f = df_csv[df_csv['Liga'] == l]
            times = sorted(pd.concat([df_f['Mandande'], df_f['Visitante']]).unique())
            m = c2.selectbox("Mandante", times, key=f"m_{i}")
            v = c3.selectbox("Visitante", [t for t in times if t != m], key=f"v_{i}")
        
        jogos_finais.append({"l": l, "m": m, "v": v})

    # 4. FORMULÁRIO FINANCEIRO
    st.subheader("📋 Detalhes da Múltipla" if num_jogos > 1 else "📋 Detalhes da Aposta")
    with st.form("form_aposta", clear_on_submit=True):
        f1, f2, f3, f4 = st.columns(4)
        data_ap = f1.date_input("Data", datetime.now())
        banca_sel = f1.selectbox("Banca", lista_bancas)
        
        mercados_lista = carregar_aux("Mercado")
        mercado_reg = f2.selectbox("Mercado", ["Múltipla"] + mercados_lista if num_jogos > 1 else mercados_lista)
        linha = f2.text_input("Linha (Ex: Over 2.5 / ML)")
        
        metodos_lista = carregar_aux("Metodo")
        metodo_reg = f3.selectbox("Método", metodos_lista)
        status_reg = f3.selectbox("Status", ["Aberta", "Green", "Meio Green", "Red", "Meio Red", "Devolvida"])
        
        stake = f4.number_input("Stake", min_value=0.0, step=10.0)
        odd = f4.number_input("Odd Total", min_value=1.0, step=0.1)
        obs = st.text_input("Observação (Jogos da múltipla)")

        if st.form_submit_button("🚀 Registrar Aposta"):
            # Lógica profissional: Une os nomes para o banco de dados
            liga_unificada = " / ".join(list(set([j['l'] for j in jogos_finais])))
            mandante_unificado = " + ".join([j['m'] for j in jogos_finais])
            visitante_unificado = " + ".join([j['v'] for j in jogos_finais])
            
            # Cálculo financeiro (Igual ao seu)
            lucro = 0.0
            if status_reg == "Green": lucro = stake * (odd - 1)
            elif status_reg == "Meio Green": lucro = (stake * (odd - 1)) / 2
            elif status_reg == "Red": lucro = -stake
            elif status_reg == "Meio Red": lucro = -stake / 2

            dados = {
                "data": data_ap.strftime('%Y-%m-%d'),
                "liga": liga_unificada, 
                "mandante": mandante_unificado, 
                "visitante": visitante_unificado,
                "mercado": mercado_reg, "linha": linha, "metodo": metodo_reg,
                "stake": float(stake), "odd": float(odd), "status": status_reg,
                "lucro": float(lucro), "banca_nome": banca_sel, "obs": obs
            }
            
            try:
                supabase.table("apostas").insert(dados).execute()
                # Backup local
                if not os.path.exists("data"): os.makedirs("data")
                df_local = pd.read_csv(PATH_APOSTAS) if os.path.exists(PATH_APOSTAS) else pd.DataFrame()
                df_local = pd.concat([df_local, pd.DataFrame([dados])], ignore_index=True)
                df_local.to_csv(PATH_APOSTAS, index=False)
                
                st.balloons()
                st.success(f"✅ {tipo_aposta} registrada com sucesso!")
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(f"Erro: {e}")
