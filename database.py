import pandas as pd
import os

# Função para carregar a base de estatísticas (dados_25_26.csv)
def carregar_csv():
    caminho = 'dados_25_26.csv'
    if os.path.exists(caminho):
        try:
            df = pd.read_csv(caminho)
            df.columns = df.columns.str.lower().str.strip()
            return df
        except Exception as e:
            return pd.DataFrame()
    return pd.DataFrame()

# Função para salvar aposta no CSV
def salvar_aposta(dados_aposta):
    caminho_apostas = 'apostas_registradas.csv'
    try:
        if os.path.exists(caminho_apostas):
            df = pd.read_csv(caminho_apostas)
        else:
            df = pd.DataFrame(columns=[
                'data', 'liga', 'mandante', 'visitante', 'mercado', 
                'metodo', 'odd', 'stake', 'resultado', 'lucro_prejuizo', 'obs'
            ])
        novo_registro = pd.DataFrame([dados_aposta])
        df = pd.concat([df, novo_registro], ignore_index=True)
        df.to_csv(caminho_apostas, index=False)
        return True
    except Exception as e:
        return False

# NOVA FUNÇÃO: Para o Dashboard e Histórico lerem as apostas
def carregar_apostas():
    caminho = 'apostas_registradas.csv'
    if os.path.exists(caminho):
        return pd.read_csv(caminho)
    return pd.DataFrame()
