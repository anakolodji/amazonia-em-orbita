"""
Script para treinar um modelo de Rede Neural (RN) para predição de risco ambiental.
Utiliza dados reais coletados dos sensores (arquivo dados_sensores.jsonl).
O modelo treinado é salvo para ser usado pelo painel Streamlit.
"""

import pandas as pd
import numpy as np
import json
from tensorflow import keras
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
import joblib
import os

# Caminho do arquivo de dados dos sensores
dados_path = os.path.join(os.path.dirname(__file__), '../../dados_sensores.jsonl')

# Carregar dados dos sensores
dados = []
if os.path.exists(dados_path):
    with open(dados_path, 'r') as f:
        for linha in f:
            try:
                dados.append(json.loads(linha))
            except Exception:
                continue
else:
    print(f"Arquivo {dados_path} não encontrado. Execute o simulador de sensores para gerar dados.")
    exit(1)

if len(dados) < 10:
    print("Poucos dados para treinar. Aguarde mais leituras dos sensores.")
    exit(1)

df = pd.DataFrame(dados)

"""
Script para treinar um modelo de Rede Neural (RN) para predição de risco de malária.
Lógica baseada em pesquisa científica sobre condições ambientais favoráveis ao mosquito Anopheles:
- Temperatura: 22–30°C (ótimo: 25–27°C)
- Umidade: ≥ 70% (ótimo: 70–80%)
- Chuva: >50mm (simulando água parada pós-chuva)
O risco é considerado ALTO se pelo menos 2 dessas condições forem verdadeiras simultaneamente.
"""

# Funções de risco baseadas na pesquisa
def risco_temperatura(temp):
    return 22 <= temp <= 30

def risco_umidade(umid):
    return umid >= 70

def risco_chuva(chuva):
    return chuva > 50

# Risco alto se pelo menos 2 condições forem verdadeiras
df['risco'] = (
    df.apply(lambda row: (
        int(risco_temperatura(row['temperatura'])) +
        int(risco_umidade(row['umidade'])) +
        int(risco_chuva(row['chuva']))
    ) >= 2, axis=1)
).astype(int)

# Seleção de features e target
X = df[['chuva', 'temperatura', 'umidade']]
y = df['risco']

# Normalização
scaler = MinMaxScaler()
X_scaled = scaler.fit_transform(X)

# Split
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2)

# Modelo RN simples
model = keras.Sequential([
    keras.layers.Dense(8, activation='relu', input_shape=(3,)),
    keras.layers.Dense(4, activation='relu'),
    keras.layers.Dense(1, activation='sigmoid')
])

model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
model.fit(X_train, y_train, epochs=20, batch_size=8, validation_split=0.1)

# Avaliação
loss, acc = model.evaluate(X_test, y_test)
print(f"Acurácia no teste: {acc:.2f}")

# Salvar modelo e scaler
model.save(os.path.join(os.path.dirname(__file__), '../../modelo_risco.h5'))
joblib.dump(scaler, os.path.join(os.path.dirname(__file__), '../../scaler_risco.save'))
