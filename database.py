import pandas as pd
import os

# Manti o nome 'carregar_csv' para bater com o seu app.py
def carregar_csv():
    caminho = 'dados_25_26.csv'
    if os.path.exists(caminho):
        try:
            df = pd.read_csv(caminho)
            # Isso transforma "Liga" em "liga", "Mandante" em "mandante", etc.
            df.columns = df.columns.str.lower().str.strip()
            return df
        except Exception as e:
            print(f"Erro ao ler o CSV: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

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
        print(f"Erro ao salvar: {e}")
        return False
