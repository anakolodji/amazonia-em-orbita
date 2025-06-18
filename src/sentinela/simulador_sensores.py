"""
Simulador de sensores para envio periódico de dados ambientais (temperatura, umidade, chuva) para a API Flask.
Gera dados baseados em faixas ambientais que favorecem a proliferação do mosquito Anopheles (malária), conforme pesquisa científica:
- Temperatura: 22–30°C (ótimo: 25–27°C)
- Umidade: ≥ 70% (ótimo: 70–80%)
- Chuva: >50mm simula água parada pós-chuva
A maioria dos dados será gerada nessas faixas críticas.
"""
import requests
import random
import time

API_URL = "http://localhost:5000/sensores"

def gerar_temperatura():
    # 70% das vezes dentro da faixa crítica, 30% fora
    if random.random() < 0.7:
        return round(random.uniform(22, 30), 2)
    else:
        return round(random.choice([random.uniform(15, 21.9), random.uniform(30.1, 35)]), 2)

def gerar_umidade():
    # 70% das vezes >= 70%
    if random.random() < 0.7:
        return round(random.uniform(70, 80), 2)
    else:
        return round(random.uniform(40, 69.9), 2)

def gerar_chuva():
    # 60% das vezes simula pós-chuva (>50mm)
    if random.random() < 0.6:
        return round(random.uniform(50, 120), 2)
    else:
        return round(random.uniform(0, 49.9), 2)

while True:
    dados = {
        "temperatura": gerar_temperatura(),
        "umidade": gerar_umidade(),
        "chuva": gerar_chuva()
    }
    try:
        resp = requests.post(API_URL, json=dados)
        print(f"Enviado: {dados} | Resposta: {resp.text}")
    except Exception as e:
        print(f"Erro ao enviar dados: {e}")
    time.sleep(5)  # envia a cada 5 segundos
