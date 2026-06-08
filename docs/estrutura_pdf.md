# Estrutura Sugerida do PDF

## Capa

- Amazônia em Órbita
- Sistema inteligente para priorização de áreas vulneráveis usando imagens de satélite, risco ambiental e geração automática de relatórios humanitários.
- Integrantes
- QUERO CONCORRER, se aplicável

## Introdução

- Economia espacial
- Uso de satélites para impacto positivo na Terra
- Desafio amazônico e humanitário

## Problema

- Regiões remotas
- Dificuldade logística
- Riscos ambientais e sanitários
- Baixa velocidade de tomada de decisão

## Solução

- Dashboard Streamlit
- Seletor de visão persistente para Território, Imagem orbital, IPHO e Relatório IA
- Análise de imagem orbital
- IPHO - Índice de Prioridade Humanitária Orbital
- Mapa com pontos de comunidades, marcadores por prioridade e legenda
- Relatório humanitário automatizado com API LLM

## Arquitetura

```text
Dados orbitais / imagem de satélite
          ↓
Processamento de imagem com OpenCV
          ↓
Extração de indicadores ambientais
          ↓
Casos sanitários, intensidade de chuva, isolamento e dados geográficos
          ↓
Cálculo do IPHO
          ↓
Dashboard Streamlit
          ↓
Relatório humanitário automatizado
```

## Desenvolvimento Técnico

- Python
- Streamlit
- OpenCV
- Pandas
- Folium
- Requests para chamada de API LLM compatível com Chat Completions
- CSV local para dados simulados
- Casos sanitários simulados normalizados para o cálculo do IPHO
- Testes automatizados com Pytest

## Códigos Principais

- `src/orbital/image_analysis.py`: processamento de imagem com OpenCV.
- `src/orbital/priority_index.py`: cálculo do IPHO.
- `src/orbital/report_generator.py`: prompt e relatório local.
- `src/orbital/llm_client.py`: chamada de API LLM.
- `src/orbital/app.py`: dashboard Streamlit.

## Resultados Esperados

- Priorização mais rápida
- Apoio à decisão
- Prevenção de danos
- Uso social da economia espacial

## Conclusão

- Potencial de expansão
- Integração futura com APIs reais
- Uso de sensores e dados orbitais contínuos
- Relatórios com IA generativa conectada a modelos externos
