import pandas as pd
import os

# 1. Base de Estatísticas
def carregar_csv():
    caminho = 'dados_25_26.csv'
    if os.path.exists(caminho):
        try:
            df = pd.read_csv(caminho)
            df.columns = df.columns.str.lower().str.strip()
            return df
        except:
            return pd.DataFrame()
    return pd.DataFrame()

# 2. Gestão de Apostas
def carregar_apostas():
    caminho = 'apostas_registradas.csv'
    if os.path.exists(caminho):
        return pd.read_csv(caminho)
    return pd.DataFrame()

def salvar_aposta(dados_aposta):
    caminho = 'apostas_registradas.csv'
    df = carregar_apostas()
    if df.empty:
        df = pd.DataFrame(columns=['data', 'liga', 'mandante', 'visitante', 'mercado', 'metodo', 'odd', 'stake', 'resultado', 'lucro_prejuizo', 'obs'])
    novo = pd.DataFrame([dados_aposta])
    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(caminho, index=False)
    return True

# 3. Gestão de Bancas (Resolve o erro do Import)
def carregar_bancas():
    caminho = 'bancas.csv'
    if os.path.exists(caminho):
        return pd.read_csv(caminho)
    return pd.DataFrame(columns=['nome', 'saldo_inicial', 'saldo_atual'])

def salvar_banca(dados_banca):
    caminho = 'bancas.csv'
    df = carregar_bancas()
    novo = pd.DataFrame([dados_banca])
    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(caminho, index=False)
    return True
