import pandas as pd
import io
import requests
import numpy as np
from datetime import datetime

def atualizar_base():
    print("Iniciando atualização da base de dados...")
    
    # 1. Carregar os dados (Fonte Parquet do FootyStats)
    url = "https://github.com/futpythontrader/Bases_de_Dados/raw/refs/heads/main/Base_de_Dados_FootyStats.parquet"
    response = requests.get(url)
    df = pd.read_parquet(io.BytesIO(response.content))

    # 2. Excluir as colunas indesejadas
    colunas_para_excluir = [
        'Id_Game', 'Id_League', 'Time', 'Status', 'Odd_Over35_FT', 'Odd_Over45_FT',
        'Odd_Under35_FT', 'Odd_Under45_FT', 'Odd_DNB_H', 'Odd_DNB_A', 'PPG_H_Geral_Pre',
        'PPG_A_Geral_Pre', 'xG_H_Pre', 'xG_A_Pre', 'Total_xG_Pre', 'Odd_Corners_H',
        'Odd_Corners_D', 'Odd_Corners_A', 'Odd_Corners_Over75', 'Odd_Corners_Over85',
        'Odd_Corners_Over95', 'Odd_Corners_Over105', 'Odd_Corners_Over115',
        'Odd_Corners_Under75', 'Odd_Corners_Under85', 'Odd_Corners_Under95',
        'Odd_Corners_Under105', 'Odd_Corners_Under115', 'Corners_H_2H',
        'Corners_A_2H', 'Total_Corners_2H', 'Url_Jogo', 'Url_Home', 'Logo_Home',
        'Url_Away', 'Logo_Away'
    ]
    df = df.drop(columns=colunas_para_excluir, errors='ignore')

    # 3. Renomear as colunas
    dicionario_renomear = {
        'League': 'Liga', 'Season': 'Temporada', 'Date': 'Data', 'Round': 'Rodada',
        'Home': 'Mandante', 'Away': 'Visitante',
        'Goals_H_HT': 'Gols_Mandante_HT', 'Goals_A_HT': 'Gols_Visitante_HT', 'TotalGoals_HT': 'Total_Gols_HT',
        'Goals_H_FT': 'Gols_Mandante_FT', 'Goals_A_FT': 'Gols_Visitante_FT', 'TotalGoals_FT': 'Total_Gols_FT',
        'Goals_H_Min': 'Minutos_Gols_Mandante', 'Goals_A_Min': 'Minutos_Gols_Visitante',
        'Odd_H_FT': 'Odd_Mandante_FT', 'Odd_D_FT': 'Odd_Empate_FT', 'Odd_A_FT': 'Odd_Visitante_FT',
        'Odd_BTTS_Yes': 'Odd_BTTS_Sim', 'Odd_BTTS_No': 'Odd_BTTS_Não',
        'xG_H': 'xG_Mandante', 'xG_A': 'xG_Visitante', 'Total_xG': 'Total_xG'
    }
    df = df.rename(columns=dicionario_renomear)

    # Ajuste de Data
    df['Data'] = pd.to_datetime(df['Data'])

    # 4. Remover temporadas antigas
    temporadas_remover = [
        '2019/2020', '2020/2021', '2021/2022', '2022/2023', '2023/2024',
        '2019', '2020', '2021', '2022', '2023'
    ]
    df = df[~df['Temporada'].astype(str).isin(temporadas_remover)]

    # 5. Função para faixas de gols
    def calcular_faixas_gols(minutos_entrada):
        faixas = {'0-15': 0, '16-30': 0, '31-45+': 0, '46-60': 0, '61-75': 0, '76-90+': 0}
        if minutos_entrada is None: return pd.Series(faixas)
        if isinstance(minutos_entrada, (list, np.ndarray)):
            lista_minutos = minutos_entrada
        elif isinstance(minutos_entrada, str):
            if minutos_entrada in ['', '[]', 'nan']: return pd.Series(faixas)
            minutos_limpos = minutos_entrada.replace('[', '').replace(']', '').replace(' ', '')
            if minutos_limpos == '': return pd.Series(faixas)
            lista_minutos = minutos_limpos.split(',')
        else:
            if pd.isna(minutos_entrada): return pd.Series(faixas)
            lista_minutos = [minutos_entrada]

        for m in lista_minutos:
            m_str = str(m)
            base = int(m_str.split('+')[0]) if '+' in m_str else None
            try:
                if base is None: base = int(float(m_str))
                if 0 <= base <= 15: faixas['0-15'] += 1
                elif 16 <= base <= 30: faixas['16-30'] += 1
                elif 31 <= base <= 45: faixas['31-45+'] += 1
                elif 46 <= base <= 60: faixas['46-60'] += 1
                elif 61 <= base <= 75: faixas['61-75'] += 1
                elif base >= 76: faixas['76-90+'] += 1
            except: continue
        return pd.Series(faixas)

    # 6. Aplicar faixas
    faixas_h = df['Minutos_Gols_Mandante'].apply(calcular_faixas_gols)
    faixas_h.columns = [f"{c}_Mandante" for c in faixas_h.columns]
    faixas_a = df['Minutos_Gols_Visitante'].apply(calcular_faixas_gols)
    faixas_a.columns = [f"{c}_Visitante" for c in faixas_a.columns]
    df = pd.concat([df, faixas_h, faixas_a], axis=1)

    # 7. Salvar
    df.to_csv("dados_25_26.csv", index=False)
    print(f"Sucesso! Base atualizada em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")

if __name__ == "__main__":
    atualizar_base()
