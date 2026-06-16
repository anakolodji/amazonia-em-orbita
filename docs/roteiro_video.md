# Roteiro do Vídeo

## Abertura

O Amazônia em Órbita é uma prova de conceito criada para responder ao desafio da economia espacial. A proposta mostra como imagens de satélite, dados ambientais e inteligência artificial podem apoiar decisões humanitárias em regiões remotas da Amazônia.

## Demonstração do Índice

A solução calcula o IPHO, Índice de Prioridade Humanitária Orbital, combinando risco ambiental, intensidade de chuva, isolamento logístico, casos sanitários simulados e sinais extraídos de imagens orbitais.

## Demonstração da Imagem

Aqui vemos a imagem original. O sistema processa a cena orbital, identifica possíveis áreas de água, vegetação e solo exposto, e transforma esse dado visual em uma métrica de área afetada. A tabela YOLO-ready mostra como o projeto já organiza classe, confiança e caixa delimitadora para uma futura troca por um detector treinado.

## Demonstração do Dashboard

O dashboard cruza a análise orbital com casos sanitários, intensidade de chuva e isolamento logístico. O mapa mostra os pontos das comunidades com marcadores coloridos por prioridade e uma legenda simples.

## Demonstração da Integração

A visão de orquestração resume os agentes de imagem orbital, visão computacional, IPHO, modelo preditivo, relatório, sensores e cloud. A visão Tempo real lê o fluxo `dados_sensores.jsonl`, calcula risco ambiental por temperatura, umidade e chuva, e pode ser alimentada pelo simulador ou por um ESP32 enviando dados para a API Flask.

## Fechamento

Por fim, a visão Relatório IA usa RAG local com documentos humanitários e chama uma API LLM, quando configurada, para transformar os dados técnicos em resumo da situação, nível de prioridade, justificativa, recomendações e próximos passos para equipes de campo. Se a chave não estiver configurada durante a demonstração, o sistema mantém um fallback local para não interromper o fluxo.
