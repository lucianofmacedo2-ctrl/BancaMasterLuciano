import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="BancaMaster Pro Web", layout="wide", initial_sidebar_state="expanded")

# --- ESTILIZAÇÃO CUSTOMIZADA ---
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1e2130; padding: 15px; border-radius: 10px; border: 1px solid #3498DB; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE CÁLCULO (Lógica de Poisson) ---
class Engine:
    @staticmethod
    def poisson(k, lamb):
        if lamb <= 0: return 1 if k == 0 else 0
        return (math.exp(-lamb) * (lamb**k)) / math.factorial(k)

    @staticmethod
    def calcular_stats(df, time, local):
        df_t = df[df[local] == time].copy()
        if df_t.empty: return None
        p = "mandante" if local == "mandante" else "visitante"
        return {
            "gols": df_t[f'gols_{p}_ft'].mean(),
            "cantos": df_t[f'{p}_cantos'].mean(),
            "chutes": df_t[f'{p}_chute_ao_gol'].mean(),
            "finaliza": df_t[f'{p}_finalizacoes'].mean(),
            "cartoes": df_t[f'{p}_cartao_amarelo'].mean() + df_t[f'{p}_cartao_vermelho'].mean()
        }

# --- CARREGAMENTO DE DADOS ---
@st.cache_data
def carregar_dados():
    try:
        df = pd.read_csv("dados_25_26.csv", sep=None, engine='python')
        df.columns = [str(c).strip().lower() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

df = carregar_dados()

# --- MENU LATERAL (NAVEGAÇÃO) ---
st.sidebar.title("🏆 BancaMaster Pro")
menu = st.sidebar.radio("Ir para:", ["🏠 Dashboard", "⚽ Análise Preditiva", "📝 Registrar Aposta"])

# ---------------------------------------------------------
# TELA: DASHBOARD
# ---------------------------------------------------------
if menu == "🏠 Dashboard":
    st.title("📊 Dashboard de Performance")
    
    # Exemplo de Métricas (Aqui integraríamos com o seu banco de dados SQL ou CSV de apostas)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Lucro Total", "R$ 1.250,00", "+5.2%")
    col2.metric("ROI", "12.5%", "+1.1%")
    col3.metric("Win Rate", "68%", "-2%")
    col4.metric("Banca Atual", "R$ 5.400,00")

    st.divider()
    st.subheader("📈 Evolução do Patrimônio")
    # Gráfico de exemplo - no futuro leremos do seu banco de dados
    chart_data = pd.DataFrame([100, 120, 110, 150, 180, 175, 210], columns=['Saldo'])
    st.line_chart(chart_data)

# ---------------------------------------------------------
# TELA: ANÁLISE PREDITIVA (O MOTOR QUE FIZEMOS)
# ---------------------------------------------------------
elif menu == "⚽ Análise Preditiva":
    st.title("🤖 Inteligência Poisson")
    
    if df.empty:
        st.error("Arquivo 'dados_25_26.csv' não encontrado.")
    else:
        # Filtros de Seleção
        c1, c2 = st.columns(2)
        pais = c1.selectbox("País", sorted(df['pais'].unique()))
        liga = c2.selectbox("Liga", sorted(df[df['pais'] == pais]['divisao'].unique()))
        
        filtro = df[(df['pais'] == pais) & (df['divisao'] == liga)]
        times = sorted(filtro['mandante'].unique())
        
        t1, t2 = st.columns(2)
        casa = t1.selectbox("Casa", times)
        fora = t2.selectbox("Fora", [t for t in times if t != casa])
        
        if st.button("GERAR PROGNÓSTICO COMPLETO", use_container_width=True):
            s_c = Engine.calcular_stats(df, casa, 'mandante')
            s_f = Engine.calcular_stats(df, fora, 'visitante')
            
            if s_c and s_f:
                # Probabilidades
                prob_c, prob_f, prob_e = 0, 0, 0
                for gc in range(6):
                    for gf in range(6):
                        p = Engine.poisson(gc, s_c['gols']) * Engine.poisson(gf, s_f['gols'])
                        if gc > gf: prob_c += p
                        elif gf > gc: prob_f += p
                        else: prob_e += p
                
                # Exibição
                st.markdown(f"#### 🏟️ {casa} vs {fora}")
                m1, m2, m3 = st.columns(3)
                m1.metric(f"Vitória {casa}", f"{prob_c*100:.1f}%")
                m2.metric("Empate", f"{prob_e*100:.1f}%")
                m3.metric(f"Vitória {fora}", f"{prob_f*100:.1f}%")
                
                st.divider()
                st.subheader("🎯 Expectativas de Eventos")
                e1, e2, e3, e4 = st.columns(4)
                e1.info(f"**Gols**\n\n {s_c['gols']+s_f['gols']:.2f}")
                e2.info(f"**Cantos**\n\n {s_c['cantos']+s_f['cantos']:.2f}")
                e3.info(f"**Chutes**\n\n {s_c['chutes']+s_f['chutes']:.2f}")
                e4.info(f"**Cartões**\n\n {s_c['cartoes']+s_f['cartoes']:.2f}")

# ---------------------------------------------------------
# TELA: REGISTRAR APOSTA
# ---------------------------------------------------------
elif menu == "📝 Registrar Aposta":
    st.title("🖊️ Nova Entrada")
    with st.form("form_aposta"):
        f1, f2 = st.columns(2)
        evento = f1.text_input("Evento")
        mercado = f2.selectbox("Mercado", ["Match Odds", "Over 2.5", "BTTS", "Cantos"])
        
        f3, f4, f5 = st.columns(3)
        stake = f3.number_input("Stake (R$)", min_value=0.0)
        odd = f4.number_input("Odd", min_value=1.01)
        data = f5.date_input("Data")
        
        submit = st.form_submit_button("Salvar Aposta")
        if submit:
            st.success("Aposta registrada com sucesso! (Nesta demo Web, os dados ainda não são gravados no SQLite)")