import streamlit as st
import pandas as pd
from supabase import create_client, Client

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Banca Master Luciano", layout="wide")

# --- CONEXÃO SUPABASE ---
@st.cache_resource
def conectar_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = conectar_supabase()

# --- FUNÇÃO: CÁLCULO DE LUCRO ---
def calcular_lucro_detalhado(row):
    status = str(row['resultado']).strip().lower()
    odd = float(row['odd'])
    stake = float(row['stake'])
    
    if status == 'green':
        return (stake * odd) - stake
    elif status == 'meio green':
        return ((stake * odd) - stake) / 2
    elif status == 'red':
        return -stake
    elif status == 'meio red':
        return -stake / 2
    elif status == 'devolvida' or status == 'anulada':
        return 0.0
    else: # Pendente
        return 0.0

# --- CARREGAR DADOS DO CSV (PARA FILTROS) ---
@st.cache_data
def carregar_dados_csv():
    try:
        df = pd.read_csv("dados_25_26.csv", sep=None, engine='python')
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

df_csv = carregar_dados_csv()

# --- NAVEGAÇÃO ---
st.sidebar.title("🏆 BancaMaster")
menu = st.sidebar.radio("Navegação:", ["🏠 Dashboard", "📝 Registrar Aposta"])

# --- TELA: DASHBOARD ---
if menu == "🏠 Dashboard":
    st.title("📊 Desempenho da Banca")
    
    try:
        res = supabase.table("apostas").select("*").execute()
        df_nuvem = pd.DataFrame(res.data)
        
        if not df_nuvem.empty:
            # Aplicar cálculo de lucro linha por linha
            df_nuvem['lucro_bruto'] = df_nuvem.apply(calcular_lucro_detalhado, axis=1)
            
            lucro_total = df_nuvem['lucro_bruto'].sum()
            total_apostas = len(df_nuvem)
            total_investido = df_nuvem['stake'].sum()
            roi = (lucro_total / total_investido * 100) if total_investido > 0 else 0
            
            # Métricas em colunas
            c1, c2, c3, c4 = st.columns(4)
            cor_lucro = "normal" if lucro_total >= 0 else "inverse"
            c1.metric("Lucro Total", f"R$ {lucro_total:.2f}", delta_color=cor_lucro)
            c2.metric("Total Apostas", total_apostas)
            c3.metric("ROI %", f"{roi:.2f}%")
            c4.metric("Investimento", f"R$ {total_investido:.2f}")
            
            st.divider()
            st.subheader("Últimas Entradas")
            st.dataframe(df_nuvem[['data', 'mandante', 'visitante', 'mercado', 'odd', 'resultado', 'lucro_bruto']].tail(10), use_container_width=True)
            
        else:
            st.info("Nenhuma aposta registrada no banco de dados.")
    except Exception as e:
        st.error(f"Erro ao carregar dashboard: {e}")

# --- TELA: REGISTRAR APOSTA ---
elif menu == "📝 Registrar Aposta":
    st.title("🖊️ Nova Entrada")
    
    with st.form("form_aposta", clear_on_submit=True):
        col1, col2 = st.columns(2)
        data = col1.date_input("Data")
        
        paises = sorted(df_csv['pais'].unique()) if not df_csv.empty else ["Brasil"]
        pais = col2.selectbox("País", paises)
        
        ligas = sorted(df_csv[df_csv['pais'] == pais]['divisao'].unique()) if not df_csv.empty else ["Série A"]
        liga = col1.selectbox("Liga", ligas)
        
        times = sorted(df_csv[(df_csv['pais'] == pais) & (df_csv['divisao'] == liga)]['mandante'].unique()) if not df_csv.empty else ["Time A"]
        mandante = col1.selectbox("Mandante", times)
        visitante = col2.selectbox("Visitante", [t for t in times if t != mandante] + ["Time B"])
        
        c3, c4, c5 = st.columns(3)
        mercado = c3.text_input("Mercado")
        odd = c4.number_input("Odd", min_value=1.01, value=1.80, step=0.01)
        stake = c5.number_input("Stake (R$)", min_value=1.0, value=10.0)
        
        # AQUI AS OPÇÕES QUE VOCÊ PEDIU:
        resultado = st.selectbox("Resultado", ["Pendente", "Green", "Meio Green", "Red", "Meio Red", "Devolvida"])
        
        if st.form_submit_button("GRAVAR APOSTA", use_container_width=True):
            try:
                dados = {
                    "data": str(data), "pais": pais, "liga": liga, "mandante": mandante, 
                    "visitante": visitante, "mercado": mercado, "odd": float(odd), 
                    "stake": float(stake), "resultado": resultado
                }
                supabase.table("apostas").insert(dados).execute()
                st.success("✅ Gravado com sucesso!")
            except Exception as e:
                st.error(f"Erro: {e}")
