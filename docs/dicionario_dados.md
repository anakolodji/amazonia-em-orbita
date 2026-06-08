# Dicionário de Dados

## 1. Arquivo de Comunidades

Arquivo:

```text
data/communities_orbital.csv
```

Campos:

| Campo | Tipo | Descrição |
|---|---:|---|
| `community` | texto | Nome da comunidade monitorada. |
| `territory` | texto | Território ou região de referência. |
| `state` | texto | Unidade federativa. |
| `latitude` | número | Latitude usada no mapa. |
| `longitude` | número | Longitude usada no mapa. |
| `environmental_risk` | número 0-100 | Risco ambiental base. Pode ser elevado pela análise da imagem. |
| `rainfall_intensity` | número 0-100 | Intensidade de chuva simulada. |
| `logistic_isolation` | número 0-100 | Grau de isolamento logístico. |
| `sanitary_cases` | inteiro | Casos sanitários simulados no ciclo atual. |
| `orbital_area_affected` | número 0-100 | Percentual de área afetada por imagem orbital. |
| `monitored_population` | inteiro | População monitorada estimada. |
| `last_contact` | data | Última atualização ou contato registrado. |

## 2. Métricas Extraídas da Imagem

O módulo `src/orbital/image_analysis.py` retorna:

| Métrica | Descrição |
|---|---|
| `water_percent` | Percentual da imagem classificado como água. |
| `vegetation_percent` | Percentual da imagem classificado como vegetação. |
| `exposed_soil_percent` | Percentual da imagem classificado como solo exposto. |
| `affected_area_percent` | Métrica composta usada no IPHO como área afetada. |
| `environmental_risk` | Risco ambiental derivado da leitura visual. |
| `processed_image_rgb` | Imagem RGB com sobreposição das máscaras. |
| `mask_image_rgb` | Imagem RGB contendo apenas as máscaras. |

## 3. Cálculo do Risco Sanitário

Os casos sanitários são convertidos para escala de 0 a 100:

```text
risco_sanitario = min(100, sanitary_cases / 160 x 100)
```

No código, essa regra está em `sanitary_cases_to_score`.

## 4. Cálculo do IPHO

```text
IPHO =
(0.30 x risco ambiental) +
(0.25 x risco sanitário derivado dos casos) +
(0.20 x isolamento logístico) +
(0.15 x intensidade de chuva) +
(0.10 x área afetada por imagem orbital)
```

## 5. Classificação de Prioridade

| IPHO | Prioridade |
|---:|---|
| 0 a 39 | Baixa |
| 40 a 69 | Média |
| 70 a 100 | Alta |

## 6. Variáveis de Ambiente

Arquivo recomendado:

```text
.env
```

Variáveis:

| Variável | Obrigatória | Descrição |
|---|---|---|
| `LLM_API_KEY` | Não | Chave da API LLM. Necessária apenas para geração via API. |
| `LLM_MODEL` | Não | Nome do modelo usado pela API LLM. |
| `LLM_API_URL` | Não | Endpoint compatível com Chat Completions. |
| `LLM_TIMEOUT_SECONDS` | Não | Tempo máximo da chamada HTTP. Padrão interno: 25 segundos. Recomendado para Gemini em demonstrações: `60`. |
| `LLM_STREAM` | Não | Define se a chamada solicita streaming. Padrão: `false`. |
| `LLM_MAX_TOKENS` | Não | Orçamento máximo de saída da resposta LLM. Padrão: `2048`. |
| `LLM_MAX_COMPLETION_RETRIES` | Não | Quantidade de continuações automáticas quando a API retorna texto incompleto. Padrão: `1`. |
| `LLM_REASONING_EFFORT` | Não | Esforço de raciocínio em APIs compatíveis. Para Google AI Studio, o cliente usa `low` por padrão. |
| `SENTINELA_DB_PATH` | Não | Caminho alternativo do SQLite legado, usado principalmente em testes. |

## 7. Saída do Relatório

O relatório humanitário segue as seções:

- Resumo da situação.
- Nível de prioridade.
- Justificativa.
- Recomendações.
- Próximos passos.

Quando a API LLM está configurada, essas seções são solicitadas no prompt e validadas antes de aparecerem na interface. Se a API devolver stream, o cliente acumula todos os chunks. Se a resposta vier marcada como incompleta por limite de tokens, o cliente solicita uma continuação antes de renderizar o relatório. Quando a API não está configurada, o fallback local gera a mesma estrutura.
