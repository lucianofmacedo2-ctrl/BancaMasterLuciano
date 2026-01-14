import streamlit as st
import pandas as pd
import math
import matplotlib.pyplot as plt

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="BancaMaster Pro Web", layout="wide", initial_sidebar_state="expanded")

# --- AJUSTE DE CONTRASTE (CSS CUSTOMIZADO) ---
st.markdown("""
    <style>
    /* Fundo da página */
    .main { background-color: #0e1117; }
    
    /* Customização dos Cards de Métrica para Alto Contraste */
    [data-testid="stMetricValue"] {
        color: #FFFFFF !important; /* Branco Puro para o valor principal */
        font-size: 24px !important;
        font-weight: bold !important;
    }
    [data-testid="stMetricLabel"] {
        color: #BDC3C7 !important; /* Cinza claro para o rótulo */
        font-size: 14px !important;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    div[data-testid="metric-container"] {
        background-color: #1c2431; /* Fundo levemente mais claro que o fundo da página */
        border: 2px solid #3498db; /* Borda azul vibrante */
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE CÁLCULO ---
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

# --- MENU LATERAL ---
st.sidebar.title("🏆 BancaMaster Pro")
menu = st.sidebar.radio("Ir para:", ["🏠 Dashboard", "⚽ Análise Preditiva", "📝 Registrar Aposta"])

# --- TELA: DASHBOARD ---
if menu == "🏠 Dashboard":
    st.title("📊 Dashboard de Performance")
    
    # Agora com alto contraste
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Lucro Total", "R$ 1.250,00", "+5.2%")
    with col2:
        st.metric("ROI", "12.5%", "+1.1%")
    with col3:
        st.metric("Win Rate", "68%", "-2%")
    with col4:
        st.metric("Banca Atual", "R$ 5.400,00")

    st.divider()
    st.subheader("📈 Evolução do Patrimônio")
    chart_data = pd.DataFrame([100, 120, 110, 150, 180, 175, 210], columns=['Saldo'])
    st.line_chart(chart_data)

# --- TELA: ANÁLISE PREDITIVA ---
elif menu == "⚽ Análise Preditiva":
    st.title("🤖 Inteligência Poisson")
    if df.empty:
        st.error("Arquivo 'dados_25_26.csv' não encontrado.")
    else:
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
                prob_c, prob_f, prob_e = 0, 0, 0
                for gc in range(6):
                    for gf in range(6):
                        p = Engine.poisson(gc, s_c['gols']) * Engine.poisson(gf, s_f['gols'])
                        if gc > gf: prob_c += p
                        elif gf > gc: prob_f += p
                        else: prob_e += p
                
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

# --- TELA: REGISTRAR APOSTA ---
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
            st.success("Aposta registrada! Próximo passo: Conectar ao Google Sheets.")
