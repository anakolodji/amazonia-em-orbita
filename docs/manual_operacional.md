# Manual Operacional

Este manual descreve como executar e demonstrar o Amazônia em Órbita.

## 1. Pré-Requisitos

- Python 3.10 ou superior. Recomendado: Python 3.12.
- Dependências instaladas com `pip install -r requirements.txt`.
- Navegador atualizado.
- Opcional: chave de API LLM compatível com Chat Completions.

## 2. Execução Local

Instalar dependências:

```bash
pip install -r requirements.txt
```

Executar o dashboard:

```bash
streamlit run src/app.py
```

O terminal mostrará uma URL local, normalmente:

```text
http://localhost:8501
```

## 3. Configuração da IA Generativa

Copie `.env.example` para `.env` e preencha:

```env
LLM_API_KEY=sua_chave_aqui
LLM_MODEL=nome_do_modelo
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_TIMEOUT_SECONDS=60
LLM_STREAM=false
LLM_MAX_TOKENS=2048
LLM_MAX_COMPLETION_RETRIES=1
LLM_REASONING_EFFORT=
```

Se essas variáveis não estiverem configuradas, o app continuará funcionando com relatório local.

Mantenha `LLM_STREAM=false` para a demonstração. Se `LLM_STREAM=true` for usado, o cliente acumula todos os chunks do stream antes de exibir o relatório.

Para Google AI Studio/Gemini, configure `LLM_API_URL=https://generativelanguage.googleapis.com/v1beta/openai/chat/completions`, mantenha `LLM_REASONING_EFFORT=low` e use `LLM_TIMEOUT_SECONDS=60` para a demonstração. Quando o endpoint é do Google e a variável não existe, o cliente usa `low` automaticamente. Se a API retornar `finish_reason=length`, o cliente pede continuação antes de exibir o relatório.

## 4. Fluxo Recomendado de Demonstração

### 4.1 Abrir o Dashboard

Abra a URL exibida pelo Streamlit. A tela inicial mostra:

- cabeçalho da aplicação;
- status da cena selecionada;
- seletor de visão persistente;
- controles na barra lateral.

### 4.2 Escolher Imagem Orbital

Na barra lateral:

- escolha **Amostra** para usar a imagem incluída no projeto;
- escolha **Upload** para enviar uma imagem `.png`, `.jpg` ou `.jpeg`.
- escolha **NASA GIBS** para baixar uma cena orbital online por camada, recorte e data.

Ao usar NASA GIBS, selecione a camada, o recorte e a data. Clique em **Carregar cena NASA GIBS**. Se a rede ou o serviço externo falhar, a apresentação pode continuar com a amostra local.

### 4.3 Vincular a Comunidade

No campo **Cena orbital vinculada**, escolha a comunidade que receberá os indicadores extraídos da imagem.

### 4.4 Visão Território

Use essa visão para demonstrar:

- comunidades monitoradas;
- IPHO médio;
- áreas em prioridade alta;
- última análise;
- mapa operacional;
- gráfico de distribuição por prioridade.

### 4.5 Visão Imagem Orbital

Use essa visão para demonstrar:

- imagem original;
- imagem processada;
- percentual de água;
- percentual de vegetação;
- percentual de solo exposto;
- percentual de área afetada;
- risco ambiental.
- confiança da segmentação HSV + k-means.
- tabela de detecções YOLO-ready com classe, confiança e caixa delimitadora.

### 4.6 Visão IPHO

Use essa visão para explicar a priorização:

- risco ambiental;
- intensidade de chuva;
- isolamento logístico;
- casos sanitários;
- risco sanitário normalizado;
- área afetada pela imagem;
- IPHO final;
- risco preditivo ML;
- IPHO validado;
- prioridade baixa, média ou alta.

### 4.7 Visão Orquestração

Use essa visão para demonstrar a integração mais ampla:

- agente orbital;
- agente de visão computacional;
- agente IPHO;
- agente preditivo ML;
- agente generativo;
- agente IoT/sensores;
- agente cloud/distribuído.

### 4.8 Visão Tempo Real

Use essa visão para demonstrar:

- leitura das últimas linhas de `dados_sensores.jsonl`;
- risco calculado por temperatura, umidade e chuva;
- gráfico temporal das leituras;
- atualização manual ou automática;
- substituição do simulador por ESP32 real enviando JSON para a API Flask.

### 4.9 Visão Relatório IA

Use essa visão para gerar a síntese humanitária.

A navegação mantém a visão ativa mesmo depois do rerun do Streamlit. Portanto, ao clicar em **Gerar relatório humanitário**, o usuário permanece em **Relatório IA** enquanto a resposta é criada.

Se a API LLM estiver configurada:

- deixe **Usar API LLM** ligado;
- clique em **Gerar relatório humanitário**;
- aguarde a resposta da API.

Se a API LLM não estiver configurada:

- o app informa que usará fallback local;
- o relatório é gerado sem interromper a demonstração.

## 5. Fluxo Opcional de Sensores e Automação

Este fluxo é complementar ao dashboard principal e pode ser citado para demonstrar sensores, automação e Machine Learning.

Executar a API de sensores:

```bash
python3 src/sentinela/api_sensores.py
```

Em outro terminal, executar o simulador:

```bash
python3 src/sentinela/simulador_sensores.py
```

As leituras serão salvas em `dados_sensores.jsonl`. Um ESP32 real pode substituir o simulador enviando JSON para `http://localhost:5000/sensores` com os campos:

```json
{
  "temperatura": 26.5,
  "umidade": 78.0,
  "chuva": 64.0
}
```

Treinar a rede neural complementar:

```bash
python3 src/sentinela/treina_modelo_rn.py
```

Executar a automação climática periódica:

```bash
python3 src/scheduler.py
```

Para ingestão climática real, configure `WEATHER_API_KEY` no `.env`. Sem chave, esse fluxo é ignorado com aviso em log.

## 6. Como Explicar no Vídeo

Sugestão de sequência:

```text
1. Apresentar o problema de priorização em regiões remotas.
2. Mostrar que a solução usa imagem orbital e dados simulados.
3. Demonstrar o processamento da imagem.
4. Explicar o IPHO e seus pesos.
5. Mostrar o score ML e o IPHO validado.
6. Mostrar mapa e tabela de comunidades.
7. Demonstrar a orquestração multiagente.
8. Mostrar o fluxo de sensores em tempo real.
9. Gerar relatório IA com RAG local.
10. Concluir com impacto esperado e evoluções futuras.
```

## 7. Problemas Comuns

### Porta Ocupada

Se a porta `8501` estiver ocupada:

```bash
streamlit run src/app.py --server.port 8502
```

### API LLM Não Configurada

O app continuará funcionando com fallback local. Para usar LLM, configure `.env`.

### Imagem Não Carrega

Verifique se o arquivo é `.png`, `.jpg` ou `.jpeg`.

### Dependência Ausente

Rode novamente:

```bash
pip install -r requirements.txt
```

## 8. Validação

Antes de apresentar:

```bash
python3 -m pytest
```

Resultado esperado:

```text
tests/test_ingest.py
tests/test_orbital.py
```

Todos os testes devem passar.
