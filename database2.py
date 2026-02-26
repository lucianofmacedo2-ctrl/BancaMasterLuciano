import pandas as pd
import os

# Nome do arquivo de banco de dados específico para o Sistema 2
DB_FILE = 'apostas_registradas_s2.csv'

def carregar_apostas():
    """Carrega o histórico de apostas do Sistema 2"""
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    # Retorna DataFrame vazio com as colunas padrão se o arquivo não existir
    return pd.DataFrame(columns=[
        'data', 'mandante', 'visitante', 'mercado', 
        'linha', 'odd', 'stake', 'resultado', 'lucro_prejuizo'
    ])

def salvar_aposta(nova_linha):
    """Adiciona um novo registro ao banco de dados do Sistema 2"""
    df = carregar_apostas()
    df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
    df.to_csv(DB_FILE, index=False)
