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
    st.title("🧪 Auditoria & Backtest por Estratégia")

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
                    odd_m = float(str(row.get('Odd Mandante', 0)).replace(',','.'))
                    odd_v = float(str(row.get('Odd Visitante', 0)).replace(',','.'))
                    if odd_m < 1.4 or odd_v < 1.4: sinais.append("🌟")
                    elif 1.40 <= odd_m <= 1.80 or 1.40 <= odd_v <= 1.80: sinais.append("⭐")
                    if abs(odd_m - odd_v) <= 1.0: sinais.append("⚖️")
                except: odd_m, odd_v = 0, 0

                vitoria_super_fav = "❌"
                if odd_m < 1.4 and real['Gols_Mandante_FT'] > real['Gols_Visitante_FT']: vitoria_super_fav = "✅"
                elif odd_v < 1.4 and real['Gols_Visitante_FT'] > real['Gols_Mandante_FT']: vitoria_super_fav = "✅"

                dupla_chance_fav = "❌"
                if 1.40 <= odd_m <= 1.80 and real['Gols_Mandante_FT'] >= real['Gols_Visitante_FT']: dupla_chance_fav = "✅"
                elif 1.40 <= odd_v <= 1.80 and real['Gols_Visitante_FT'] >= real['Gols_Mandante_FT']: dupla_chance_fav = "✅"

                if sinais:
                    jogos_auditados.append({
                        "Data": row['dt_comparacao'],
                        "Liga": row.get('Liga', 'N/A'),
                        "Mandante": row['Mandante'],
                        "Visitante": row['Visitante'],
                        "Jogo": f"{row['Mandante']} x {row['Visitante']}",
                        "Sinais": sinais,
                        "RES_HT": "✅" if real['Total_Gols_HT'] >= 1 else "❌",
                        "RES_FT": "✅" if real['Total_Gols_FT'] > 2.5 else "❌",
                        "RES_AMBAS": "✅" if real['BTTS_REAL'] == 1 else "❌",
                        "RES_CNT": "✅" if real['Total_Corners'] > 9.5 else "❌",
                        "RES_SUPER_V": vitoria_super_fav,
                        "RES_FAV_DC": dupla_chance_fav,
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
        
        with st.expander(f"VER BACKTEST: {est['nome']}", expanded=True):
            if not df_filtrado.empty:
                # Métricas principais
                acertos = len(df_filtrado[df_filtrado[est['coluna']] == "✅"])
                total = len(df_filtrado)
                wr = (acertos / total) * 100
                odd_j = 100 / wr if wr > 0 else 0
                
                c1, c2, c3 = st.columns([1, 1, 2])
                c1.metric(est['meta'], f"{wr:.1f}%")
                c2.metric("Odd Justa", f"{odd_j:.2f}")
                c3.info(f"Analisando {total} jogos com o sinal {est['emoji']}")

                # --- NOVA SEÇÃO DE GRÁFICOS ---
                st.markdown("### 📊 Análise de Desempenho")
                col_graf1, col_graf2 = st.columns(2)

                with col_graf1:
                    # Desempenho por Liga
                    df_liga = df_filtrado.groupby(['Liga', est['coluna']]).size().unstack(fill_value=0).reset_index()
                    if '✅' in df_liga.columns:
                        df_liga = df_liga.sort_values(by='✅', ascending=False).head(8)
                        fig_liga = px.bar(df_liga, x='Liga', y='✅', title="Top Ligas (Greens)", 
                                          labels={'✅':'Greens'}, color_discrete_sequence=['#2ecc71'])
                        fig_liga.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
                        st.plotly_chart(fig_liga, use_container_width=True)
                    else: st.write("Aguardando dados de acertos por liga...")

                with col_graf2:
                    # Desempenho por Time (Mandante)
                    df_time = df_filtrado.groupby(['Mandante', est['coluna']]).size().unstack(fill_value=0).reset_index()
                    if '✅' in df_time.columns:
                        df_time = df_time.sort_values(by='✅', ascending=False).head(8)
                        fig_time = px.bar(df_time, x='Mandante', y='✅', title="Top Times Mandantes (Greens)", 
                                          labels={'✅':'Greens'}, color_discrete_sequence=['#3498db'])
                        fig_time.update_layout(height=300, margin=dict(l=20, r=20, t=40, b=20))
                        st.plotly_chart(fig_time, use_container_width=True)
                    else: st.write("Aguardando dados de acertos por time...")

                # Tabela de Jogos
                st.markdown("### 📋 Detalhes dos Confrontos")
                def style_v(val):
                    if val == "✅": return 'background-color: #d4edda; color: #155724'
                    if val == "❌": return 'background-color: #f8d7da; color: #721c24'
                    return ''

                df_view = df_filtrado[["Data", "Liga", "Jogo", est['coluna']]].rename(columns={est['coluna']: "Resultado"})
                st.dataframe(df_view.style.applymap(style_v, subset=['Resultado']), use_container_width=True, hide_index=True)
            else:
                st.write(f"Sem amostras para {est['emoji']} no momento.")
        st.write("")

if __name__ == "__main__":
    mostrar_backtest()
