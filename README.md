# Amazônia em Órbita

Sistema inteligente para priorização de áreas vulneráveis usando imagens de satélite, risco ambiental e geração automática de relatórios humanitários.

## Visão Geral

O **Amazônia em Órbita** é uma prova de conceito de inteligência espacial aplicada à Amazônia. A plataforma combina imagem orbital, indicadores ambientais, intensidade de chuva, isolamento logístico e casos sanitários simulados para calcular o **IPHO - Índice de Prioridade Humanitária Orbital**.

A proposta reposiciona a base técnica do antigo SentinelaMSF_Yanomami para um projeto conectado à economia espacial: transformar dados orbitais e IA em inteligência operacional para apoiar decisões humanitárias em regiões remotas.

## Problema

Comunidades isoladas da Amazônia enfrentam riscos combinados: enchentes, doenças, dificuldade logística, variação climática e baixa disponibilidade de dados operacionais. Equipes humanitárias precisam decidir onde agir primeiro, mas dependem de dados dispersos e relatórios manuais.

## Solução

O dashboard entrega quatro frentes principais:

- **Visão geral territorial:** comunidades monitoradas, IPHO médio, áreas em prioridade alta, gráfico e mapa operacional com legenda.
- **Análise orbital:** seleção ou upload de imagem, processamento com OpenCV e detecção de água, vegetação e solo exposto.
- **Priorização humanitária:** cálculo do IPHO com risco ambiental, intensidade de chuva, isolamento logístico, casos sanitários e área afetada pela imagem.
- **Relatório automatizado com IA Generativa:** chamada opcional a uma API LLM compatível com Chat Completions para gerar resumo, prioridade, justificativa, recomendações e próximos passos. Sem chave configurada, o app usa um fallback local para manter a demonstração funcionando.

## IPHO

O índice usa a fórmula recomendada para a nova versão do projeto:

```text
IPHO =
(0.30 x risco ambiental) +
(0.25 x risco sanitário derivado dos casos) +
(0.20 x isolamento logístico) +
(0.15 x intensidade de chuva) +
(0.10 x área afetada por imagem orbital)
```

No MVP, os casos sanitários vêm do CSV `data/communities_orbital.csv` e são normalizados para uma escala de 0 a 100 antes de entrar no índice.

Classificação:

```text
0 a 39   = Baixa prioridade
40 a 69  = Média prioridade
70 a 100 = Alta prioridade
```

## Arquitetura

```text
Dados orbitais / imagem de satélite
          ↓
Processamento de imagem com OpenCV
          ↓
Extração de indicadores ambientais
          ↓
Casos sanitários, intensidade de chuva e dados geográficos
          ↓
Cálculo do IPHO
          ↓
Dashboard Streamlit
          ↓
Relatório humanitário automatizado
```

## Como Executar

Instale as dependências:

```bash
pip install -r requirements.txt
```

Gere novamente a imagem orbital de amostra, se necessário:

```bash
python3 src/orbital/sample_assets.py
```

Execute o dashboard:

```bash
streamlit run src/app.py
```

## IA Generativa com API LLM

Configure um arquivo `.env` na raiz do projeto:

```env
LLM_API_KEY=sua_chave_aqui
LLM_MODEL=nome_do_modelo
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_TIMEOUT_SECONDS=25
```

`LLM_API_URL` aceita endpoints compatíveis com o formato Chat Completions. No dashboard, a aba **Relatório IA** tenta usar a API LLM quando `LLM_API_KEY` e `LLM_MODEL` estão configurados. Se a API estiver indisponível ou sem chave, o sistema gera o relatório local automaticamente.

## Testes

Execute:

```bash
python3 -m pytest
```

Os testes cobrem o cálculo do IPHO, a ordenação da prioridade, a análise simples de imagem orbital, a geração de relatório, o prompt da IA generativa e o cliente de API LLM.

## Estrutura Principal

```text
src/
  app.py
  orbital/
    app.py
    image_analysis.py
    llm_client.py
    priority_index.py
    report_generator.py
    sample_assets.py
data/
  communities_orbital.csv
  sample_images/
  processed/
docs/
tests/
```

## Módulos Legados

A pasta `src/sentinela/` foi mantida como referência técnica do projeto anterior, com ingestão, banco SQLite, scheduler e modelagem sanitária. A interface principal agora é `src/app.py`, voltada ao produto **Amazônia em Órbita**.

## Roteiro Curto para Vídeo

“O Amazônia em Órbita é uma prova de conceito criada para responder ao desafio da economia espacial. A solução mostra como imagens de satélite, dados ambientais e inteligência artificial podem apoiar decisões humanitárias em regiões remotas da Amazônia.

O sistema calcula o IPHO, Índice de Prioridade Humanitária Orbital, combinando risco ambiental, intensidade de chuva, isolamento logístico, casos sanitários simulados e sinais extraídos de imagens orbitais.

Na demonstração, a imagem orbital é processada para identificar água, vegetação e solo exposto. Em seguida, o dashboard cruza essa informação com intensidade de chuva, isolamento logístico e casos sanitários simulados, gerando a prioridade de atendimento. Por fim, a API LLM transforma os dados técnicos em resumo, justificativa, recomendações e próximos passos para equipes de campo.”
