import pandas as pd
import os

DB_FILE = 'apostas_registradas.csv'

def carregar_apostas():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=['data', 'mandante', 'visitante', 'mercado', 'linha', 'odd', 'stake', 'resultado', 'lucro_prejuizo'])

def salvar_aposta(nova_linha):
    df = carregar_apostas()
    df = pd.concat([df, pd.DataFrame([nova_linha])], ignore_index=True)
    df.to_csv(DB_FILE, index=False)
