import streamlit as st
import pandas as pd
import numpy as np

def mostrar_scout(df):
    st.title("🔎 Scout Estatístico")

    # --- DIAGNÓSTICO DE SEGURANÇA ---
    # Se der erro, isso vai mostrar quais colunas o sistema está lendo
    if 'Liga' not in df.columns:
        st.error("⚠️ Erro Crítico: A coluna 'Liga' não foi encontrada.")
        st.write("Colunas detectadas no seu arquivo:", list(df.columns))
        st.stop() # Para o código aqui para não dar o erro de KeyError

    # --- 1. FILTROS (Usando 'Liga' explicitamente) ---
    c1, c2 = st.columns(2)
    
    # AQUI ESTAVA O ERRO ANTIGO: trocamos df['pais'] por df['Liga']
    ligas_disponiveis = sorted(df['Liga'].unique())
    liga_sel = c1.selectbox("Selecione a Liga", ligas_disponiveis)
    
    df_liga = df[df['Liga'] == liga_sel].copy()
    
    # Filtro de Temporada
    temps_disponiveis = sorted(df_liga['Temporada'].unique(), reverse=True)
    temp_sel = c2.selectbox("Temporada", temps_disponiveis)
    
    df_filt = df_liga[df_liga['Temporada'] == temp_sel].copy()
    
    # Tratamento de data seguro
    df_filt['Data'] = pd.to_datetime(df_filt['Data'], dayfirst=True, errors='coerce')

    # Seleção de Times (Usando 'Mandande' com 'e' no final, conforme seu CSV)
    times = sorted(df_filt['Mandande'].unique())
    c3, c4 = st.columns(2)
    m_sel = c3.selectbox("Mandante", times)
    v_sel = c4.selectbox("Visitante", [t for t in times if t != m_sel])

    # Bases de dados
    df_m = df_filt[df_filt['Mandande'] == m_sel].sort_values('Data', ascending=False).head(10)
    df_v = df_filt[df_filt['Visitante'] == v_sel].sort_values('Data', ascending=False).head(10)

    # --- 2. EXIBIÇÃO ---
    st.divider()
    tab1, tab2 = st.tabs(["📊 Forma e H2H", "⏰ Minutos"])

    with tab1:
        col1, col2 = st.columns(2)
        # Mandante
        with col1:
            st.write(f"**{m_sel} (Casa)**")
            for _, r in df_m.head(5).iterrows():
                gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
                res = "✅" if gm > gv else ("🟧" if gm == gv else "❌")
                st.write(f"{res} vs {r['Visitante']} ({int(gm)}-{int(gv)})")
        
        # Visitante
        with col2:
            st.write(f"**{v_sel} (Fora)**")
            for _, r in df_v.head(5).iterrows():
                gm, gv = r['Gols_Mandante_FT'], r['Gols_Visitante_FT']
                res = "✅" if gv > gm else ("🟧" if gm == gv else "❌")
                st.write(f"{res} vs {r['Mandande']} ({int(gm)}-{int(gv)})")

    with tab2:
        st.subheader("Gols por Faixa de Tempo (%)")
        faixas = ["0-15", "16-30", "31-45+", "46-60", "61-75", "76-90+"]
        
        c_fm, c_fv = st.columns(2)
        
        # Usando os nomes exatos das suas colunas de minutos
        # Ex: 0-15_Mandante, 31-45+_Mandante (conforme seu CSV)
        with c_fm:
            vals_m = []
            for f in faixas:
                col_name = f"{f}_Mandante"
                if col_name in df_m.columns:
                    vals_m.append(df_m[col_name].mean() * 100)
                else:
                    vals_m.append(0)
            
            st.write(f"**{m_sel}**")
            st.dataframe(pd.DataFrame([vals_m], columns=faixas, index=["%"]).style.format("{:.1f}%").background_gradient(cmap="Greens", axis=1))

        with c_fv:
            vals_v = []
            for f in faixas:
                col_name = f"{f}_Visitante"
                if col_name in df_v.columns:
                    vals_v.append(df_v[col_name].mean() * 100)
                else:
                    vals_v.append(0)

            st.write(f"**{v_sel}**")
            st.dataframe(pd.DataFrame([vals_v], columns=faixas, index=["%"]).style.format("{:.1f}%").background_gradient(cmap="Greens", axis=1))
