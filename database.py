import pandas as pd
import os

# --- BASE DE ESTATÍSTICAS ---
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

# --- GESTÃO DE MERCADOS (DINÂMICO COM EXCLUSÃO) ---
def carregar_mercados():
    caminho = 'mercados_cadastrados.csv'
    padrao = ["Match Odds", "Over/Under", "Ambas Marcam"]
    if os.path.exists(caminho):
        try:
            df = pd.read_csv(caminho)
            return sorted(df['nome'].unique().tolist())
        except:
            return padrao
    return padrao

def salvar_novo_mercado(novo_nome):
    caminho = 'mercados_cadastrados.csv'
    mercados = carregar_mercados()
    if novo_nome and novo_nome not in mercados:
        df = pd.DataFrame({'nome': mercados + [novo_nome]})
        df.to_csv(caminho, index=False)
        return True
    return False

def remover_mercado(nome_remover):
    caminho = 'mercados_cadastrados.csv'
    mercados = carregar_mercados()
    if nome_remover in mercados:
        mercados.remove(nome_remover)
        df = pd.DataFrame({'nome': mercados})
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
        df = pd.DataFrame(columns=['data', 'liga', 'mandante', 'visitante', 'mercado', 'linha', 'metodo', 'odd', 'stake', 'resultado', 'lucro_prejuizo', 'obs'])
    novo = pd.DataFrame([dados_aposta])
    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(caminho, index=False)
    return True

# --- GESTÃO DE BANCAS ---
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
