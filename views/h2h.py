import streamlit as st
import pandas as pd
import unicodedata

def tratar_string(texto):
    if not texto or pd.isna(texto): return ""
    texto = str(texto).upper().strip()
    nksf = unicodedata.normalize('NFKD', texto)
    return "".join([c for c in nksf if not unicodedata.combining(c)])

def mostrar_h2h(df):
    st.title("⚔️ Confronto Direto (H2H)")
    
    if df.empty:
        st.error("Base de dados vazia.")
        return

    # Preparar listas de times
    df['M_T'] = df['Mandante'].apply(tratar_string)
    df['V_T'] = df['Visitante'].apply(tratar_string)
    times = sorted(list(set(df['M_T'].unique()) | set(df['V_T'].unique())))

    col1, col2 = st.columns(2)
    with col1:
        time_a = st.selectbox("Selecione o Time A", times)
    with col2:
        time_b = st.selectbox("Selecione o Time B", times, index=1 if len(times)>1 else 0)

    if time_a == time_b:
        st.warning("Selecione times diferentes para comparar.")
        return

    # Filtrar jogos onde ambos se enfrentaram (independente de quem foi mandante)
    filtro = ((df['M_T'] == time_a) & (df['V_T'] == time_b)) | ((df['M_T'] == time_b) & (df['V_T'] == time_a))
    confrontos = df[filtro].copy()

    if confrontos.empty:
        st.info(f"Não foram encontrados confrontos diretos entre {time_a} e {time_b} na base.")
        return

    # Estatísticas Rápidas
    v_a = len(confrontos[((confrontos['M_T'] == time_a) & (confrontos['Gols_Mandante_FT'] > confrontos['Gols_Visitante_FT'])) | 
                         ((confrontos['V_T'] == time_a) & (confrontos['Gols_Visitante_FT'] > confrontos['Gols_Mandante_FT']))])
    
    v_b = len(confrontos[((confrontos['M_T'] == time_b) & (confrontos['Gols_Mandante_FT'] > confrontos['Gols_Visitante_FT'])) | 
                         ((confrontos['V_T'] == time_b) & (confrontos['Gols_Visitante_FT'] > confrontos['Gols_Mandante_FT']))])
    
    empates = len(confrontos) - v_a - v_b

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(f"Vitórias {time_a}", v_a)
    c2.metric("Empates", empates)
    c3.metric(f"Vitórias {time_b}", v_b)
    c4.metric("Total de Jogos", len(confrontos))

    st.divider()
    st.subheader("📜 Histórico de Partidas")
    
    # Formatação para exibição
    exibir = confrontos[['Data', 'Liga', 'Mandante', 'Gols_Mandante_FT', 'Gols_Visitante_FT', 'Visitante', 'Total_Corners']].copy()
    exibir.columns = ['Data', 'Liga', 'Casa', 'Gols C', 'Gols V', 'Visitante', 'Cantos']
    st.dataframe(exibir.sort_values('Data', ascending=False), use_container_width=True, hide_index=True)

    # Médias do Confronto
    st.subheader("📊 Médias Específicas deste Confronto")
    m1, m2, m3 = st.columns(3)
    m1.write(f"**Média de Gols:** {(confrontos['Total_Gols_FT'].mean()):.2f}")
    m2.write(f"**Média de Cantos:** {(confrontos['Total_Corners'].mean()):.2f}")
    m3.write(f"**Ambas Marcam:** {(len(confrontos[(confrontos['Gols_Mandante_FT']>0) & (confrontos['Gols_Visitante_FT']>0)])/len(confrontos)*100):.1f}%")
