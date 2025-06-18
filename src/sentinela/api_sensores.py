"""
API Flask para ingestão de dados simulados de sensores (temperatura, umidade, chuva).
Esses dados podem ser enviados por um ESP32 real ou simulador Python.
Os dados recebidos são salvos em um arquivo JSONL para posterior ingestão e análise pelo painel e pelo modelo de RN.
"""
from flask import Flask, request, jsonify
import json
import os
from datetime import datetime

app = Flask(__name__)

# Caminho do arquivo onde os dados dos sensores serão armazenados
SENSOR_DATA_PATH = os.path.join(os.path.dirname(__file__), '../../dados_sensores.jsonl')

@app.route('/sensores', methods=['POST'])
def receber_dados():
    dados = request.json
    dados['timestamp'] = datetime.utcnow().isoformat()
    with open(SENSOR_DATA_PATH, 'a') as f:
        f.write(json.dumps(dados) + '\n')
    return jsonify({"status": "ok", "msg": "Dados recebidos com sucesso."})

if __name__ == '__main__':
    app.run(port=5000)
