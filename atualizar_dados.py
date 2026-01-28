import pandas as pd
import ast
import numpy as np
import requests

# 1. LER CSV DO GITHUB
url = "https://raw.githubusercontent.com/futpythontrader/YouTube/refs/heads/main/Bases_de_Dados/FootyStats/Base_de_Dados_FootyStats.csv"
df = pd.read_csv(url)

# 2. EXCLUIR COLUNAS
colunas_excluir = [
    "Id_Jogo", "PPG_Home_Pre", "PPG_Away_Pre", "PPG_Home", "PPG_Away",
    "XG_Home_Pre", "XG_Away_Pre", "XG_Total_Pre", "Odd_Corners_H",
    "Odd_Corners_D", "Odd_Corners_A", "Odd_Corners_Over75",
    "Odd_Corners_Under75", "Odd_Corners_Over85", "Odd_Corners_Under85",
    "Odd_Corners_Over95", "Odd_Corners_Under95", "Odd_Corners_Over105",
    "Odd_Corners_Under105", "Odd_Corners_Over115", "Odd_Corners_Under115"
]
df = df.drop(columns=[c for c in colunas_excluir if c in df.columns])

# 3. RENOMEAR COLUNAS
mapa_colunas = {
    "League": "Liga", "Season": "Temporada", "Date": "Data", "Round": "Rodada",
    "Home": "Mandante", "Away": "Visitante",
    "Goals_H_HT": "Gols_Mandante_HT", "Goals_A_HT": "Gols_Visitante_HT",
    "TotalGoals_HT": "Total_Gols_HT", "Goals_H_FT": "Gols_Mandante_FT",
    "Goals_A_FT": "Gols_Visitante_FT", "TotalGoals_FT": "Total_Gols_FT",
    "Goals_H_Minutes": "Minutos_Gols_Mandante", "Goals_A_Minutes": "Minutos_Gols_Visitante",
    "Odd_H_HT": "Odd_Mandante_HT", "Odd_D_HT": "Odd_Empate_HT", "Odd_A_HT": "Odd_Visitante_HT",
    "Odd_Over05_HT": "Odd_Over_05Gols_HT", "Odd_Under05_HT": "Odd_Under_05Gols_HT",
    "Odd_Over15_HT": "Odd_Over_15Gols_HT", "Odd_Under15_HT": "Odd_Under_15Gols_HT",
    "Odd_Over25_HT": "Odd_Over_25Gols_HT", "Odd_Under25_HT": "Odd_Under_25Gols_HT",
    "Odd_H_FT": "Odd_Mandante_FT", "Odd_D_FT": "Odd_Empate_FT", "Odd_A_FT": "Odd_Visitante_FT",
    "Odd_Over05_FT": "Odd_Over_05Gols_FT", "Odd_Under05_FT": "Odd_Under_05Gols_FT",
    "Odd_Over15_FT": "Odd_Over_15Gols_FT", "Odd_Under15_FT": "Odd_Under_15Gols_FT",
    "Odd_Over25_FT": "Odd_Over_25Gols_FT", "Odd_Under25_FT": "Odd_Under_25Gols_FT",
    "Odd_BTTS_Yes": "Odd_BTTS_Sim", "Odd_BTTS_No": "Odd_BTTS_Não",
    "Odd_1X": "Odd_DC_1X", "Odd_12": "Odd_DC_12", "Odd_X2": "Odd_DC_X2",
    "ShotsOnTarget_H": "Chutes_Gol_Mandante", "ShotsOnTarget_A": "Chutes_Gol_Visitante",
    "ShotsOffTarget_H": "Chutes_Fora_Mandante", "ShotsOffTarget_A": "Chutes_Fora_Visitante",
    "Shots_H": "Finalizações_Totais_Mandante", "Shots_A": "Finalizações_Totais_Visitante",
    "Corners_H_FT": "Cantos_Mandante", "Corners_A_FT": "Cantos_Visitante",
    "TotalCorners_FT": "Total_Cantos_FT"
}
df = df.rename(columns=mapa_colunas)

# 3.5 TRATAMENTO
df['Data'] = pd.to_datetime(df['Data'], errors='coerce').dt.strftime('%d/%m/%Y')
df = df.dropna(subset=['Gols_Mandante_FT', 'Gols_Visitante_FT'])
cols_numericas = df.select_dtypes(include=[np.number]).columns
df[cols_numericas] = df[cols_numericas].fillna(0)

# 4. FUNÇÃO FAIXAS
def contar_gols_por_faixa(minutos_str):
    faixas = {"0-15": 0, "16-30": 0, "31-45+": 0, "46-60": 0, "61-75": 0, "76-90+": 0}
    if pd.isna(minutos_str) or minutos_str == "[]" or minutos_str == "":
        return faixas
    try:
        if isinstance(minutos_str, str):
            minutos = ast.literal_eval(minutos_str)
        else:
            minutos = minutos_str
        minutos = [int(str(m).replace("'", "").replace("+", "")) for m in minutos]
    except:
        return faixas
    for m in minutos:
        if m <= 15: faixas["0-15"] += 1
        elif m <= 30: faixas["16-30"] += 1
        elif m <= 45: faixas["31-45+"] += 1
        elif m <= 60: faixas["46-60"] += 1
        elif m <= 75: faixas["61-75"] += 1
        else: faixas["76-90+"] += 1
    return faixas

for mando in ["Mandante", "Visitante"]:
    col_name = f"Minutos_Gols_{mando}"
    res_faixas = df[col_name].apply(contar_gols_por_faixa).apply(pd.Series)
    res_faixas.columns = [f"{c}_{mando}" for c in res_faixas.columns]
    df = pd.concat([df, res_faixas], axis=1)

# 8. EXPORTAR
df.to_csv("dados_25_26.csv", index=False, encoding='utf-8-sig')
print("Arquivo dados_25_26.csv atualizado com sucesso!")
