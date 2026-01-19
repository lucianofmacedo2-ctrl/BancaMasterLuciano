import pandas as pd
import os

# Função para carregar a base de dados de estatísticas (dados_25_26.csv)
def carregar_dados():
    caminho = 'dados_25_26.csv'
    if os.path.exists(caminho):
        df = pd.read_csv(caminho)
        # Padroniza colunas para minúsculas e remove espaços para evitar KeyErrors
        df.columns = df.columns.str.lower().str.strip()
        return df
    return pd.DataFrame()

# Função para salvar as apostas feitas pelo usuário
def salvar_aposta(dados_aposta):
    caminho_apostas = 'apostas_registradas.csv'
    try:
        if os.path.exists(caminho_apostas):
            df = pd.read_csv(caminho_apostas)
        else:
            # Cria o arquivo com a estrutura correta se não existir
            df = pd.DataFrame(columns=[
                'data', 'liga', 'mandante', 'visitante', 'mercado', 
                'metodo', 'odd', 'stake', 'resultado', 'lucro_prejuizo', 'obs'
            ])

        novo_registro = pd.DataFrame([dados_aposta])
        df = pd.concat([df, novo_registro], ignore_index=True)
        df.to_csv(caminho_apostas, index=False)
        return True
    except Exception as e:
        print(f"Erro ao salvar: {e}")
        return False
