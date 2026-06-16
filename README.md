# FIAP - Faculdade de Informática e Administração Paulista

<p align="center">
<a href="https://www.fiap.com.br/"><img src="assets/logo-fiap.png" alt="FIAP - Faculdade de Informática e Administração Paulista" border="0" width="40%" height="40%"></a>
</p>

<br>

# Graduação ON em Inteligência Artificial

----

# Amazônia em Órbita

## Grupo Amazônia em Órbita

## Integrantes

- Ana Ingrid Pires Alves Kolodji - RM 559629
- Fábio Santos Cardôso - RM a preencher no PDF final
- Bruno Henrique Nielsen Conter - RM a preencher no PDF final
- Matheus Conciani da Silva - RM a preencher no PDF final

## Professores

### Tutor(a)

- A preencher

### Coordenador(a)

- A preencher

## Descrição

O **Amazônia em Órbita** é uma prova de conceito desenvolvida para a Global Solution da FIAP, no contexto de economia espacial, Inteligência Artificial, visão computacional, automação e impacto positivo na Terra.

A pergunta central respondida pelo projeto é:

```text
Como tecnologias avançadas de Inteligência Artificial e computação podem impulsionar a nova economia espacial e gerar impacto positivo na Terra?
```

A solução propõe uma plataforma Streamlit para apoiar decisões humanitárias em comunidades remotas da Amazônia. O sistema combina imagens orbitais, inclusive fonte online NASA GIBS quando há rede, indicadores ambientais, isolamento logístico, chuva, casos sanitários simulados e leitura de sensores para calcular o **IPHO - Índice de Prioridade Humanitária Orbital**.

O MVP entrega seis visões principais:

- **Território:** mapa operacional, cards, gráfico de distribuição de prioridade e tabela resumida.
- **Imagem orbital:** seleção de amostra, upload ou cena NASA GIBS, processamento com OpenCV, HSV, k-means e detector YOLO-ready por contornos.
- **IPHO:** cálculo do índice explicável, score preditivo ML, IPHO validado e classificação baixa, média ou alta.
- **Orquestração:** visão multiagente com camadas orbital, visão computacional, IPHO, ML, IA Generativa, IoT/sensores e cloud.
- **Tempo real:** fluxo de sensores a partir de `dados_sensores.jsonl`, com risco calculado por temperatura, umidade e chuva.
- **Relatório IA:** geração de relatório humanitário com RAG local, API LLM compatível com Chat Completions ou fallback local.

### Principais componentes técnicos

- Visão computacional com OpenCV para detectar água, vegetação, solo exposto e área afetada.
- Integração opcional com NASA GIBS/WMS para uso de fonte orbital real.
- Detector YOLO-ready documentado, com saída de classe, confiança e caixa delimitadora.
- IPHO explicável com validação complementar por score preditivo ML.
- RAG local com documentos humanitários em `docs/rag_corpus/`.
- Cliente de IA Generativa com fallback local para garantir demonstração sem chave de API.
- Simulador/API de sensores substituível por ESP32.
- Dashboard inteligente com mapas, gráficos, tabelas e fluxo em tempo real.

### IPHO

```text
IPHO =
(0.30 x risco ambiental) +
(0.25 x risco sanitário derivado dos casos) +
(0.20 x isolamento logístico) +
(0.15 x intensidade de chuva) +
(0.10 x área afetada por imagem orbital)
```

| IPHO | Prioridade |
|---:|---|
| 0 a 39 | Baixa |
| 40 a 69 | Média |
| 70 a 100 | Alta |

### Arquitetura resumida

```text
Imagem orbital / upload / NASA GIBS
          ↓
OpenCV: HSV + k-means para água, vegetação e solo exposto
          ↓
Detector YOLO-ready por contornos OpenCV
          ↓
Métricas visuais: área afetada e risco ambiental
          ↓
CSV de comunidades + fluxo de sensores
          ↓
Cálculo do IPHO + score preditivo ML
          ↓
Dashboard Streamlit + orquestração multiagente
          ↓
RAG local + API LLM ou fallback local
          ↓
Relatório humanitário automatizado
```

## Estrutura de pastas

Dentre os arquivos e pastas presentes na raiz do projeto, definem-se:

- `assets/`: imagens institucionais usadas no README.
- `data/`: bases utilizadas pelo MVP, incluindo `communities_orbital.csv` e imagens orbitais de amostra.
- `docs/`: documentação textual, checklist do enunciado, dicionário de dados, manual operacional, estrutura sugerida do PDF, corpus RAG, diagramas, prints e relatório final.
- `screenshots/`: imagens da interface para documentação e apresentação.
- `src/`: código-fonte da aplicação, incluindo dashboard Streamlit, análise orbital, cálculo IPHO, RAG, detector YOLO-ready, sensores, ingestões e módulos complementares.
- `tests/`: testes automatizados com Pytest.
- `README.md`: guia geral do projeto.
- `requirements.txt`: dependências Python necessárias para execução.
- `.env.example`: exemplo de configuração de variáveis de ambiente.

Estrutura principal:

```text
src/
  app.py
  orbital/
    app.py
    image_analysis.py
    llm_client.py
    mission_agents.py
    ml_risk_model.py
    nasa_gibs.py
    priority_index.py
    rag.py
    report_generator.py
    sample_assets.py
    sensor_stream.py
    yolo_detector.py
  sentinela/
    api_sensores.py
    simulador_sensores.py
    treina_modelo_rn.py
data/
  communities_orbital.csv
  sample_images/
docs/
  rag_corpus/
screenshots/
tests/
```

## Links e Observações

- Repositório do projeto: https://github.com/anakolodji/amazonia-em-orbita
- Vídeo da entrega: https://youtu.be/x0P39spT4ho?si=qQbJYVNmByXvD0Bn
- Documentação da aplicação: [docs/documentacao_aplicacao.md](docs/documentacao_aplicacao.md)
- Manual operacional: [docs/manual_operacional.md](docs/manual_operacional.md)
- Dicionário de dados: [docs/dicionario_dados.md](docs/dicionario_dados.md)
- Estrutura sugerida do PDF: [docs/estrutura_pdf.md](docs/estrutura_pdf.md)
- Relatório final em PDF: [docs/amazonia_em_orbita_relatorio_final.pdf](docs/amazonia_em_orbita_relatorio_final.pdf)

### Observações técnicas

- A aplicação funciona sem chave de API LLM, usando fallback local para o relatório.
- A integração NASA GIBS depende de rede e disponibilidade do serviço externo, mas a demonstração mantém amostra local e upload como fallback.
- O detector YOLO-ready é um placeholder funcional por contornos OpenCV, preparado para substituição futura por pesos YOLO treinados.
- O fluxo de sensores em tempo real lê `dados_sensores.jsonl`, que pode ser alimentado pelo simulador Python ou por um ESP32 enviando JSON para a API Flask.
- Os RMs e nomes de professores devem ser conferidos e preenchidos no PDF final antes da entrega.

## Como executar o código

### Pré-requisitos

- Python 3.10 ou superior. Recomendado: Python 3.12.
- Pip atualizado.
- Navegador atualizado para acessar o dashboard Streamlit.
- Opcional: chave de API LLM compatível com Chat Completions.

### Instalação

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuração opcional da IA Generativa

Copie `.env.example` para `.env` e preencha quando quiser usar a API LLM:

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

Sem essas variáveis, o app continua funcionando com relatório local.

### Executar o dashboard

```bash
streamlit run src/app.py
```

A aplicação normalmente abre em:

```text
http://localhost:8501
```

### Gerar imagem orbital de amostra

```bash
python3 src/orbital/sample_assets.py
```

### Fluxo opcional de sensores

Em um terminal, execute a API:

```bash
python3 src/sentinela/api_sensores.py
```

Em outro terminal, execute o simulador:

```bash
python3 src/sentinela/simulador_sensores.py
```

As leituras serão gravadas em `dados_sensores.jsonl` e aparecerão na visão **Tempo real** do dashboard.

### Testes

```bash
python3 -m pytest
```

Os testes cobrem cálculo do IPHO, visão computacional, NASA GIBS com HTTP falso, detector YOLO-ready, RAG, sensores em tempo real, orquestração multiagente, prompt/cliente LLM e mapa.

## Histórico de lançamentos

- 0.5.0 - Inclusão de RAG local, detector YOLO-ready, visão Tempo real e documentação alinhada ao enunciado.
- 0.4.0 - Inclusão de NASA GIBS, k-means, IPHO validado por ML e orquestração multiagente.
- 0.3.0 - Ajustes no cliente LLM, fallback local e validação de seções obrigatórias do relatório.
- 0.2.0 - Implementação do dashboard Streamlit com mapa, IPHO, análise orbital e relatório IA.
- 0.1.0 - Estrutura inicial do projeto, dados simulados, módulos de sensores e ingestão.

----

## Licença

Este projeto acadêmico é destinado à avaliação da Global Solution e às atividades da Graduação ON em Inteligência Artificial da FIAP.
