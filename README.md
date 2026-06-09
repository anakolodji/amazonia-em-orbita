# FIAP - Faculdade de Informática e Administração Paulista

<p align="center">
<a href= "https://www.fiap.com.br/"><img src="assets/logo-fiap.png" alt="FIAP - Faculdade de Informática e Admnistração Paulista" border="0" width=40% height=40%></a>
</p>

<br>

# 🎓 Graduação ON em Inteligência Artificial  

---

# Amazônia em Órbita

Sistema inteligente para priorização de áreas vulneráveis usando imagens de satélite, risco ambiental e geração automática de relatórios humanitários.

## Visão Geral

O **Amazônia em Órbita** é uma prova de conceito de inteligência espacial aplicada à Amazônia. A plataforma combina imagem orbital, indicadores ambientais, risco sanitário, isolamento logístico e intensidade climática para calcular o **IPHO - Índice de Prioridade Humanitária Orbital**.

A proposta reposiciona a base técnica do antigo SentinelaMSF_Yanomami para um projeto conectado à economia espacial: transformar dados orbitais e IA em inteligência operacional para apoiar decisões humanitárias em regiões remotas.

## Problema

Comunidades isoladas da Amazônia enfrentam riscos combinados: enchentes, doenças, dificuldade logística, variação climática e baixa disponibilidade de dados operacionais. Equipes humanitárias precisam decidir onde agir primeiro, mas dependem de dados dispersos e relatórios manuais.

## Solução

O dashboard entrega quatro frentes principais:

- **Visão geral territorial:** comunidades monitoradas, IPHO médio, áreas em prioridade alta e mapa operacional.
- **Análise orbital:** seleção ou upload de imagem, processamento com OpenCV e detecção de água, vegetação e solo exposto.
- **Priorização humanitária:** cálculo do IPHO com classificação baixa, média ou alta.
- **Relatório automatizado:** geração de um relatório humanitário com justificativa, prioridade, recomendações e próximos passos.

## IPHO

O índice usa a fórmula recomendada para a nova versão do projeto:

```text
IPHO =
(0.30 x risco ambiental) +
(0.25 x risco sanitário) +
(0.20 x isolamento logístico) +
(0.15 x intensidade climática) +
(0.10 x área afetada por imagem orbital)
```

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
Dados sanitários, climáticos e geográficos
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

## Testes

Execute:

```bash
python3 -m pytest
```

Os testes cobrem o cálculo do IPHO, a ordenação da prioridade, a análise simples de imagem orbital e a geração de relatório.

## Estrutura Principal

```text
src/
  app.py
  orbital/
    app.py
    image_analysis.py
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
