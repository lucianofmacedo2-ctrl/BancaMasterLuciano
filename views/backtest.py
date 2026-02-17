import streamlit as st
import pandas as pd
import numpy as np
import unicodedata
from datetime import datetime
import plotly.express as px

# --- CONFIGURAÇÕES DE LINKS ---
URL_AGENDA = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/refs/heads/main/Lista_Jogos.csv"
URL_MAPEAMENTO = "https://raw.githubusercontent.com/lucianofmacedo2-ctrl/BancaMasterLuciano/main/mapeamento_times.xlsx%20-%20Tudo.csv"
ARQUIVO_HISTORICO = 'dados_25_26.csv'

def tratar_string_backtest(texto):
    if not texto or pd.isna(texto): return ""
    texto = str(texto)
    mapa_caracteres = {"Ã³": "O", "Ã©": "E", "Ã¡": "A", "Ã£": "A", "Ãª": "E", "Ã­": "I", "Ã§": "C", "Ã": "A", "Ã²": "O", "Ã¹": "U"}
    for erro, correto in mapa_caracteres.items():
        texto = texto.replace(erro, correto)
    nksf = unicodedata.normalize('NFKD', texto)
    texto = "".join([c for c in nksf if not unicodedata.combining(c)])
    return texto.upper().strip()

@st.cache_data(ttl=600)
def carregar_dados_auditoria():
    try:
        df_map = pd.read_csv(URL_MAPEAMENTO)
        mapa_times = dict(zip(df_map['Time Soccerway'].apply(tratar_string_backtest), 
                              df_map['Time Base '].apply(tratar_string_backtest)))
    except: mapa_times = {}

    try:
        df_h = pd.read_csv(ARQUIVO_HISTORICO, sep=None, engine='python', encoding='utf-8-sig')
        df_h.columns = [c.strip() for c in df_h.columns]
        df_h['dt_comparacao'] = pd.to_datetime(df_h['Data'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')
        df_h['M_NORM'] = df_h['Mandante'].apply(tratar_string_backtest)
        df_h['V_NORM'] = df_h['Visitante'].apply(tratar_string_backtest)
        
        for col in ['Total_Gols_FT', 'Total_Gols_HT', 'Total_Corners', 'Gols_Mandante_FT', 'Gols_Visitante_FT']:
            if col in df_h.columns:
                df_h[col] = pd.to_numeric(df_h[col].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        df_h['BTTS_REAL'] = ((df_h['Gols_Mandante_FT'] > 0) & (df_h['Gols_Visitante_FT'] > 0)).astype(int)
    except: df_h = pd.DataFrame()

    try:
        df_a = pd.read_csv(URL_AGENDA, sep=None, engine='python', encoding='utf-8-sig')
        df_a.columns = [c.strip() for c in df_a.columns]
        df_a['dt_comparacao'] = pd.to_datetime(df_a['Data'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')
        def aplicar_mapa(nome):
            norm = tratar_string_backtest(nome)
            return mapa_times.get(norm, norm)
        df_a['M_TRADUZ'] = df_a['Mandante'].apply(aplicar_mapa)
        df_a['V_TRADUZ'] = df_a['Visitante'].apply(aplicar_mapa)
    except: df_a = pd.DataFrame()

    return df_h, df_a

def mostrar_backtest():
    st.markdown("<style>[data-testid='stMetricValue'] { color: #31333F !important; }</style>", unsafe_allow_html=True)
    st.title("🧪 Auditoria Inteligente de Sinais")

    df_h, df_a = carregar_dados_auditoria()
    if df_h.empty or df_a.empty:
        st.warning("Dados não carregados corretamente.")
        return

    jogos_auditados = []
    for _, row in df_a.iterrows():
        match = df_h[(df_h['M_NORM'] == row['M_TRADUZ']) & (df_h['V_NORM'] == row['V_TRADUZ']) & (df_h['dt_comparacao'] == row['dt_comparacao'])]
        
        if not match.empty:
            real = match.iloc[0]
            h_m = df_h[((df_h['M_NORM'] == row['M_TRADUZ']) | (df_h['V_NORM'] == row['M_TRADUZ'])) & (df_h['dt_comparacao'] != row['dt_comparacao'])]
            h_v = df_h[((df_h['M_NORM'] == row['V_TRADUZ']) | (df_h['V_NORM'] == row['V_TRADUZ'])) & (df_h['dt_comparacao'] != row['dt_comparacao'])]
            
            if not h_m.empty and not h_v.empty:
                m_g, m_ht, m_c, m_b = (h_m['Total_Gols_FT'].mean()+h_v['Total_Gols_FT'].mean())/2, (h_m['Total_Gols_HT'].mean()+h_v['Total_Gols_HT'].mean())/2, (h_m['Total_Corners'].mean()+h_v['Total_Corners'].mean())/2, (h_m['BTTS_REAL'].mean()+h_v['BTTS_REAL'].mean())/2
                
                sinais = []
                if m_ht >= 1.0: sinais.append("⏱️")
                if m_g > 2.5: sinais.append("🔥⚽")
                if m_b > 0.60: sinais.append("🤝")
                if m_c > 9.5: sinais.append("🔥🚩")

                try:
                    odd_m, odd_v = float(str(row.get('Odd Mandante', 0)).replace(',','.')), float(str(row.get('Odd Visitante', 0)).replace(',','.'))
                    if odd_m < 1.4 or odd_v < 1.4: sinais.append("🌟")
                    elif 1.40 <= odd_m <= 1.80 or 1.40 <= odd_v <= 1.80: sinais.append("⭐")
                    if abs(odd_m - odd_v) <= 1.0: sinais.append("⚖️")
                except: odd_m, odd_v = 0, 0

                # Lógica de Resultados
                v_super = "✅" if ((odd_m < 1.4 and real['Gols_Mandante_FT'] > real['Gols_Visitante_FT']) or (odd_v < 1.4 and real['Gols_Visitante_FT'] > real['Gols_Mandante_FT'])) else "❌"
                v_fav_dc = "✅" if ((1.40 <= odd_m <= 1.80 and real['Gols_Mandante_FT'] >= real['Gols_Visitante_FT']) or (1.40 <= odd_v <= 1.80 and real['Gols_Visitante_FT'] >= real['Gols_Mandante_FT'])) else "❌"

                if sinais:
                    jogos_auditados.append({
                        "Data": row['dt_comparacao'],
                        "Liga": str(row.get('Liga', 'Outras')).strip().upper(),
                        "Mandante": str(row['Mandante']).strip(),
                        "Jogo": f"{row['Mandante']} x {row['Visitante']}",
                        "Sinais": sinais,
                        "RES_HT": "✅" if real['Total_Gols_HT'] >= 1 else "❌",
                        "RES_FT": "✅" if real['Total_Gols_FT'] > 2.5 else "❌",
                        "RES_AMBAS": "✅" if real['BTTS_REAL'] == 1 else "❌",
                        "RES_CNT": "✅" if real['Total_Corners'] > 9.5 else "❌",
                        "RES_SUPER_V": v_super,
                        "RES_FAV_DC": v_fav_dc,
                        "RES_UNDER_25": "✅" if real['Total_Gols_FT'] < 2.5 else "❌"
                    })

    if not jogos_auditados:
        st.info("Nenhum jogo cruzado encontrado.")
        return

    df_base = pd.DataFrame(jogos_auditados)

    estratogias = [
        {"nome": "⏱️ Gols HT (0.5 HT)", "emoji": "⏱️", "coluna": "RES_HT", "meta": "Winrate 0.5 HT"},
        {"nome": "🔥⚽ Gols FT (2.5 FT)", "emoji": "🔥⚽", "coluna": "RES_FT", "meta": "Winrate 2.5 FT"},
        {"nome": "🤝 Ambas Marcam (BTTS)", "emoji": "🤝", "coluna": "RES_AMBAS", "meta": "Winrate Ambas"},
        {"nome": "🔥🚩 Cantos (9.5 Corners)", "emoji": "🔥🚩", "coluna": "RES_CNT", "meta": "Winrate 9.5 Cnt"},
        {"nome": "🌟 Super Favorito (Vitória)", "emoji": "🌟", "coluna": "RES_SUPER_V", "meta": "Winrate Vitória"},
        {"nome": "⭐ Favorito (Dupla Chance)", "emoji": "⭐", "coluna": "RES_FAV_DC", "meta": "Winrate 1X ou X2"},
        {"nome": "⚖️ Equilibrado (Under 2.5 FT)", "emoji": "⚖️", "coluna": "RES_UNDER_25", "meta": "Winrate Under 2.5"}
    ]

    for est in estratogias:
        df_filtrado = df_base[df_base['Sinais'].apply(lambda x: est['emoji'] in x)].copy()
        
        with st.expander(f"ANALISAR ESTRATÉGIA: {est['nome']}", expanded=True):
            if not df_filtrado.empty:
                acertos = len(df_filtrado[df_filtrado[est['coluna']] == "✅"])
                total = len(df_filtrado)
                wr = (acertos / total) * 100
                odd_j = 100 / wr if wr > 0 else 0
                
                c1, c2, c3 = st.columns([1, 1, 2])
                c1.metric(est['meta'], f"{wr:.1f}%")
                c2.metric("Odd Justa", f"{odd_j:.2f}")
                c3.info(f"Base de Dados: {total} jogos processados.")

                # --- SEÇÃO DE GRÁFICOS ---
                st.write("---")
                g1, g2 = st.columns(2)

                # Gráfico de Ligas
                df_g_liga = df_filtrado.groupby('Liga')[est['coluna']].apply(lambda x: (x == '✅').sum()).reset_index(name='Greens')
                df_g_liga = df_g_liga.sort_values('Greens', ascending=False).head(10)
                
                with g1:
                    fig_l = px.bar(df_g_liga, x='Greens', y='Liga', orientation='h', 
                                   title="Top Ligas Lucrativas", color_discrete_sequence=['#27ae60'])
                    fig_l.update_layout(height=350, yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_l, use_container_width=True)

                # Gráfico de Times
                df_g_time = df_filtrado.groupby('Mandante')[est['coluna']].apply(lambda x: (x == '✅').sum()).reset_index(name='Greens')
                df_g_time = df_g_time.sort_values('Greens', ascending=False).head(10)

                with g2:
                    fig_t = px.bar(df_g_time, x='Greens', y='Mandante', orientation='h', 
                                   title="Top Times (Mandantes)", color_discrete_sequence=['#2980b9'])
                    fig_t.update_layout(height=350, yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_t, use_container_width=True)

                # Tabela Detalhada
                st.write("**Histórico Detalhado:**")
                def color_map(val):
                    return 'background-color: #d4edda' if val == "✅" else 'background-color: #f8d7da'

                df_final_view = df_filtrado[["Data", "Liga", "Jogo", est['coluna']]].rename(columns={est['coluna']: "Resultado"})
                st.dataframe(df_final_view.style.applymap(color_map, subset=['Resultado']), use_container_width=True, hide_index=True)
            else:
                st.caption(f"Sem dados históricos suficientes para o sinal {est['emoji']}.")

if __name__ == "__main__":
    mostrar_backtest()
