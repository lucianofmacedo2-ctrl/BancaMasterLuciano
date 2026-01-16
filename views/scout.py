import streamlit as st
import pandas as pd

def mostrar_scout(df):
    st.title("🔎 Scout de Times")
    if df.empty:
        st.error("Dados não encontrados ou CSV vazio.")
        return

    c1, c2 = st.columns(2)
    pais = c1.selectbox("País", sorted(df['pais'].unique()))
    liga = c2.selectbox("Liga", sorted(df[df['pais'] == pais]['divisao'].unique()))
    
    times = sorted(df[df['divisao'] == liga]['mandante'].unique())
    c3, c4 = st.columns(2)
    m_sel = c3.selectbox("Mandante (Casa)", times)
    v_sel = c4.selectbox("Visitante (Fora)", [t for t in times if t != m_sel])

    # Filtros específicos: Mandante jogando em CASA e Visitante jogando FORA
    df_m = df[(df['mandante'] == m_sel) & (df['divisao'] == liga)]
    df_v = df[(df['visitante'] == v_sel) & (df['divisao'] == liga)]

    st.subheader("📊 Médias Detalhadas (Alto Contraste)")

    # Função corrigida para bater com as colunas do seu CSV
    def calcular_medias(data, is_home):
        # Mapeamento exato das colunas do seu arquivo
        if is_home:
            return {
                "Gols FT": data['gols_mandante_ft'].mean(),
                "Gols HT": data['gols_mandante_ht'].mean(),
                "Cantos": data['mandante_cantos'].mean(),
                "Finalizações": data['mandante_finalizacoes'].mean(),
                "Chutes ao Gol": data['mandante_chute_ao_gol'].mean(),
                "Cartões Amarelos": data['mandante_cartao_amarelo'].mean()
            }
        else:
            return {
                "Gols FT": data['gols_visitante_ft'].mean(),
                "Gols HT": data['gols_visitante_ht'].mean(),
                "Cantos": data['visitante_cantos'].mean(),
                "Finalizações": data['visitante_finalizacoes'].mean(),
                "Chutes ao Gol": data['visitante_chute_ao_gol'].mean(),
                "Cartões Amarelos": data['visitante_cartao_amarelo'].mean()
            }

    try:
        stats_m = calcular_medias(df_m, True)
        stats_v = calcular_medias(df_v, False)
        
        # Tabela de Comparação
        df_final = pd.DataFrame({
            f"{m_sel} (Em Casa)": stats_m, 
            f"{v_sel} (Fora)": stats_v
        })
        
        # Exibição com estilo de alta visibilidade
        st.table(df_final.style.format(precision=2))

        # 📈 FORMA ÚLTIMOS 5 JOGOS
        st.divider()
        st.subheader("📈 Forma Recente (Últimos 5 Jogos)")
        col_f1, col_f2 = st.columns(2)
        
        with col_f1:
            st.write(f"**{m_sel}** - Desempenho em Casa")
            # Pega os 5 jogos mais recentes do mandante em casa
            ultimos_casa = df_m.sort_values('data', ascending=False).head(5)
            if not ultimos_casa.empty:
                for _, r in ultimos_casa.iterrows():
                    res = "✅" if r['gols_mandante_ft'] > r['gols_visitante_ft'] else ("🟧" if r['gols_mandante_ft'] == r['gols_visitante_ft'] else "❌")
                    st.write(f"{res} {r['data'].strftime('%d/%m')} vs {r['visitante']} ({int(r['gols_mandante_ft'])} - {int(r['gols_visitante_ft'])})")
            else: st.info("Sem histórico em casa.")

        with col_f2:
            st.write(f"**{v_sel}** - Desempenho Fora")
            # Pega os 5 jogos mais recentes do visitante fora
            ultimos_fora = df_v.sort_values('data', ascending=False).head(5)
            if not ultimos_fora.empty:
                for _, r in ultimos_fora.iterrows():
                    res = "✅" if r['gols_visitante_ft'] > r['gols_mandante_ft'] else ("🟧" if r['gols_visitante_ft'] == r['gols_mandante_ft'] else "❌")
                    st.write(f"{res} {r['data'].strftime('%d/%m')} @ {r['mandante']} ({int(r['gols_mandante_ft'])} - {int(r['gols_visitante_ft'])})")
            else: st.info("Sem histórico fora.")

    except Exception as e:
        st.error(f"Erro ao processar médias: {e}")
        st.info("Verifique se o CSV contém as colunas de gols, cantos e chutes.")
