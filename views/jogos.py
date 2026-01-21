import requests
from bs4 import BeautifulSoup
import pandas as pd

def raspar_jogos_ogol(url):
    # Definimos um 'User-Agent' para o site não bloquear a requisição imediatamente
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Erro ao aceder ao site: {response.status_code}")
            return []

        soup = BeautifulSoup(response.content, 'html.parser')
        
        # O oGol costuma organizar os jogos em tabelas ou divs com a classe 'zzstats'
        # Esta parte precisa ser ajustada conforme a estrutura exata do HTML no momento
        jogos = []
        
        # Procuramos as linhas da tabela de jogos (ajuste os seletores se necessário)
        tabela = soup.find('table', class_='zztable')
        if not tabela:
            print("Não foi possível encontrar a tabela de jogos.")
            return []

        for linha in tabela.find_all('tr')[1:]: # Pula o cabeçalho
            colunas = linha.find_all('td')
            if len(colunas) >= 4:
                hora = colunas[0].get_text(strip=True)
                competicao = colunas[1].get_text(strip=True)
                # O oGol muitas vezes coloca os times em links ou spans
                time_casa = colunas[2].get_text(strip=True)
                time_fora = colunas[4].get_text(strip=True) # Geralmente o 5º elemento

                jogos.append({
                    "Hora": hora,
                    "Competição": competicao,
                    "Mandante": time_casa,
                    "Visitante": time_fora
                })
        
        return jogos

    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        return []

# URL que você forneceu
url_ogol = "https://www.ogol.com.br/futebol/proximos-jogos?jogo_data_year=2026&jogo_data_month=1&jogo_data_day=22"
lista_jogos = raspar_jogos_ogol(url_ogol)

# Exibe os resultados
if lista_jogos:
    df = pd.DataFrame(lista_jogos)
    print(df)
else:
    print("Nenhum dado capturado.")
