# Roteiro do Vídeo

## Abertura

O Amazônia em Órbita é uma prova de conceito criada para responder ao desafio da economia espacial. A proposta mostra como imagens de satélite, dados ambientais e inteligência artificial podem apoiar decisões humanitárias em regiões remotas da Amazônia.

## Demonstração do Índice

A solução calcula o IPHO, Índice de Prioridade Humanitária Orbital, combinando risco ambiental, intensidade de chuva, isolamento logístico, casos sanitários simulados e sinais extraídos de imagens orbitais.

## Demonstração da Imagem

Aqui vemos a imagem original. O sistema processa a cena orbital, identifica possíveis áreas de água, vegetação e solo exposto, e transforma esse dado visual em uma métrica de área afetada.

## Demonstração do Dashboard

O dashboard cruza a análise orbital com casos sanitários, intensidade de chuva e isolamento logístico. O mapa mostra os pontos das comunidades com marcadores coloridos por prioridade e uma legenda simples.

## Fechamento

Por fim, a aba Relatório IA chama uma API LLM, quando configurada, para transformar os dados técnicos em resumo da situação, nível de prioridade, justificativa, recomendações e próximos passos para equipes de campo. Se a chave não estiver configurada durante a demonstração, o sistema mantém um fallback local para não interromper o fluxo.
