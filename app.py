import streamlit as st
import pandas as pd
import os
import shutil
from datetime import datetime
# Importamos o novo módulo 'jogos' além dos outros
from views import scout, registro, historico, dashboard, bancas, jogos
import styles

# --- FUNÇÃO DE BACKUP AUTOMÁTICO ---
def realizar_backup():
    pasta_data = "data"
    pasta_backup = "backups"
    
    # Só faz backup se a pasta de dados existir
    if not os.path.exists(pasta_data):
        return

    # Cria a pasta de backup se não existir
    if not os.path.exists(pasta_backup):
        os.makedirs(pasta_backup)

    # Nome do backup baseado no dia (formato: backup_2024-05-20.zip)
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    arquivo_zip = os.path.join(pasta_backup, f"backup_{data_hoje}")

    # Só cria o zip se ainda não existir um backup hoje
    if not os.path.exists(arquivo_zip + ".zip"):
        try:
            shutil.make_archive(arquivo_zip, 'zip', pasta_data)
        except Exception as e:
            print(f"Erro no backup: {e}")

# Executa o backup toda vez que o app inicia ou atualiza
realizar_backup()

st.set_page_config(page_title="Master Luciano - Banca", layout="wide", page_icon="⚽")

# Aplica o visual profissional
styles.apply_styles()

def carregar_dados_csv():
    try:
        # Carrega o arquivo de scout (dados_25_26.csv)
        df = pd.read_csv('dados_25_26.csv')
        df.columns = [c.strip() for c in df.columns] 
        return df
    except Exception as e:
        return pd.DataFrame()

df_csv = carregar_dados_csv()

st.sidebar.title("🏆 Master Luciano")

# Adicionamos "📅 Jogos" na lista de Navegação
menu = st.sidebar.radio("Navegação", ["📊 Dashboard", "📅 Jogos", "🔎 Scout", "📝 Registro", "📂 Histórico", "🏦 Bancas"])

if menu == "📊 Dashboard":
    dashboard.mostrar_dashboard() 

elif menu == "📅 Jogos":
    # Chamada para o novo módulo que usa a API Football
    jogos.mostrar_jogos()

elif menu == "🔎 Scout":
    if not df_csv.empty:
        scout.mostrar_scout(df_csv)
    else:
        st.error("Arquivo 'dados_25_26.csv' não encontrado para o Scout.")

elif menu == "📝 Registro":
    registro.mostrar_registro(df_csv)

elif menu == "📂 Histórico":
    historico.mostrar_historico()

elif menu == "🏦 Bancas":
    bancas.mostrar_bancas()
