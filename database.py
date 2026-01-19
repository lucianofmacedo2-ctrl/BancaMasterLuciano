import pandas as pd
import os

# --- BASE DE ESTATÍSTICAS ---
def carregar_csv():
    caminho = 'dados_25_26.csv'
    if os.path.exists(caminho):
        df = pd.read_csv(caminho)
        df.columns = df.columns.str.lower().str.strip()
        return df
    return pd.DataFrame()

# --- GESTÃO DE MERCADOS (DINÂMICO) ---
def carregar_mercados():
    caminho = 'mercados_cadastrados.csv'
    if os.path.exists(caminho):
        return sorted(pd.read_csv(caminho)['nome'].tolist())
    # Lista inicial padrão caso o arquivo não exista
    return ["Match Odds", "Over/Under", "Ambas Marcam"]

def salvar_novo_mercado(novo_nome):
    caminho = 'mercados_cadastrados.csv'
    mercados = carregar_mercados()
    if novo_nome not in mercados:
        df = pd.DataFrame({'nome': mercados + [novo_nome]})
        df.to_csv(caminho, index=False)
        return True
    return False

# --- GESTÃO DE APOSTAS ---
def carregar_apostas():
    caminho = 'apostas_registradas.csv'
    if os.path.exists(caminho):
        return pd.read_csv(caminho)
    return pd.DataFrame()

def salvar_aposta(dados_aposta):
    caminho = 'apostas_registradas.csv'
    df = carregar_apostas()
    if df.empty:
        # Adicionada a coluna 'linha' na estrutura
        df = pd.DataFrame(columns=['data', 'liga', 'mandante', 'visitante', 'mercado', 'linha', 'metodo', 'odd', 'stake', 'resultado', 'lucro_prejuizo', 'obs'])
    novo = pd.DataFrame([dados_aposta])
    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(caminho, index=False)
    return True
