import pandas as pd
import ast

print("Iniciando atualização da base...")

url = "https://raw.githubusercontent.com/futpythontrader/YouTube/main/Bases_de_Dados/Base_de_Dados_FootyStats.csv"
df = pd.read_csv(url)

colunas_excluir = [
    "Id_Jogo","PPG_Home_Pre","PPG_Away_Pre","PPG_Home","PPG_Away",
    "XG_Home_Pre","XG_Away_Pre","XG_Total_Pre",
    "Odd_Corners_H","Odd_Corners_D","Odd_Corners_A",
    "Odd_Corners_Over75","Odd_Corners_Under75",
    "Odd_Corners_Over85","Odd_Corners_Under85",
    "Odd_Corners_Over95","Odd_Corners_Under95",
    "Odd_Corners_Over105","Odd_Corners_Under105",
    "Odd_Corners_Over115","Odd_Corners_Under115"
]

df = df.drop(columns=[c for c in colunas_excluir if c in df.columns])

mapa_colunas = {
    "League": "Liga",
    "Season": "Temporada",
    "Date": "Data",
    "Home": "Mandante",
    "Away": "Visitante",
    "Goals_H_Minutes": "Minutos_Gols_Mandante",
    "Goals_A_Minutes": "Minutos_Gols_Visitante"
}

df = df.rename(columns=mapa_colunas)

def contar_gols_por_faixa(minutos_str):
    faixas = {"0-15":0,"16-30":0,"31-45+":0,"46-60":0,"61-75":0,"76-90+":0}
    if pd.isna(minutos_str) or minutos_str == "[]":
        return faixas
    try:
        minutos = [int(m) for m in ast.literal_eval(minutos_str)]
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

mandante = df["Minutos_Gols_Mandante"].apply(contar_gols_por_faixa).apply(pd.Series)
visitante = df["Minutos_Gols_Visitante"].apply(contar_gols_por_faixa).apply(pd.Series)

mandante.columns = [f"{c}_Mandante" for c in mandante.columns]
visitante.columns = [f"{c}_Visitante" for c in visitante.columns]

df = pd.concat([df, mandante, visitante], axis=1)

df.to_csv("dados_25_26.csv", index=False, encoding="utf-8-sig")

print("Base atualizada com sucesso!")
