import pandas as pd
import os

# --- 1. BASE DE ESTATÍSTICAS (Scout) ---
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

# --- 2. GESTÃO DE MERCADOS (Dinâmico) ---
def carregar_mercados():
    caminho = 'mercados_cadastrados.csv'
    if os.path.exists(caminho):
        try:
            return sorted(pd.read_csv(caminho)['nome'].tolist())
        except:
            return ["Match Odds", "Over/Under", "Ambas Marcam"]
    return ["Match Odds", "Over/Under", "Ambas Marcam"]

def salvar_novo_mercado(novo_nome):
    caminho = 'mercados_cadastrados.csv'
    mercados = carregar_mercados()
    if novo_nome not in mercados:
        df = pd.DataFrame({'nome': mercados + [novo_nome]})
        df.to_csv(caminho, index=False)
        return True
    return False

# --- 3. GESTÃO DE APOSTAS (Registro/Histórico) ---
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

# --- 4. GESTÃO DE BANCAS (Financeiro) ---
def carregar_bancas():
    caminho = 'bancas.csv'
    if os.path.exists(caminho):
        return pd.read_csv(caminho)
    # Estrutura inicial se não existir
    return pd.DataFrame(columns=['nome', 'saldo_inicial', 'saldo_atual'])

def salvar_banca(dados_banca):
    caminho = 'bancas.csv'
    df = carregar_bancas()
    novo = pd.DataFrame([dados_banca])
    df = pd.concat([df, novo], ignore_index=True)
    df.to_csv(caminho, index=False)
    return True
