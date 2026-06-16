# Documentação da Aplicação

## 1. Identificação

**Nome:** Amazônia em Órbita

**Subtítulo:** Sistema inteligente para priorização de áreas vulneráveis usando imagens de satélite, risco ambiental e geração automática de relatórios humanitários.

**Tipo de solução:** Prova de conceito de inteligência espacial aplicada à Terra.

**Contexto da GS:** uso de Inteligência Artificial, visão computacional, análise de dados e dashboard inteligente para gerar impacto positivo na Terra a partir de dados orbitais.

**Repositório:** https://github.com/anakolodji/amazonia-em-orbita

**Vídeo:** https://youtu.be/x0P39spT4ho?si=qQbJYVNmByXvD0Bn

## 2. Resumo Executivo

O Amazônia em Órbita é uma plataforma Streamlit que apoia a priorização de comunidades vulneráveis na Amazônia. A aplicação combina imagem orbital, dados simulados de chuva, isolamento logístico, casos sanitários e risco ambiental para calcular o **IPHO - Índice de Prioridade Humanitária Orbital**.

O sistema também processa imagens com OpenCV para estimar água, vegetação, solo exposto e área afetada. A cena pode vir de amostra local, upload ou NASA GIBS/WMS. Com esses indicadores, o dashboard apresenta mapa, cards, gráficos, tabela de priorização, orquestração multiagente, fluxo de sensores em tempo real e relatório humanitário com RAG local. A etapa de relatório pode chamar uma API de LLM compatível com Chat Completions; quando a API não está configurada, o app usa um fallback local para manter a demonstração funcionando.

## 3. Problema

Regiões remotas da Amazônia enfrentam riscos combinados: eventos climáticos, isolamento logístico, vulnerabilidade sanitária e baixa disponibilidade de dados operacionais. Equipes humanitárias precisam decidir onde agir primeiro, mas muitas vezes lidam com dados dispersos, baixa visibilidade territorial e relatórios manuais.

O problema central tratado pela aplicação é:

```text
Como transformar dados orbitais, indicadores ambientais e IA em inteligência operacional para priorização humanitária?
```

## 4. Objetivos

### Objetivo Geral

Criar um MVP funcional capaz de analisar imagem orbital, calcular prioridade humanitária e gerar relatório operacional para apoiar tomada de decisão em comunidades amazônicas.

### Objetivos Específicos

- Processar imagem orbital com visão computacional.
- Carregar imagem real online via NASA GIBS quando houver rede.
- Detectar água, vegetação e solo exposto.
- Gerar detecções YOLO-ready com classe, confiança e caixa delimitadora.
- Calcular percentual de área afetada.
- Cruzar dados visuais com dados sanitários, climáticos e logísticos.
- Calcular o IPHO para cada comunidade.
- Validar o IPHO com score preditivo complementar.
- Classificar comunidades em prioridade baixa, média ou alta.
- Exibir resultados em dashboard Streamlit.
- Exibir fluxo de sensores em tempo real no dashboard.
- Orquestrar agentes técnicos de imagem, IPHO, ML, relatório, sensores e cloud.
- Recuperar contexto humanitário local por RAG.
- Gerar relatório humanitário com RAG, API LLM ou fallback local.
- Demonstrar automação complementar com API de sensores, simulador e treinamento de rede neural.

## 5. Público-Alvo

- Equipes humanitárias e sanitárias.
- Analistas ambientais.
- Gestores de resposta emergencial.
- Professores e avaliadores da GS.
- Times acadêmicos que precisam demonstrar integração entre IA, visão computacional e análise de dados.

## 6. Funcionalidades

### 6.1 Dashboard Streamlit

A interface principal fica em `src/orbital/app.py` e é aberta por `src/app.py`. Ela contém seis visões acessadas por um seletor persistente:

- **Território:** visão geral, cards, mapa e gráfico de distribuição de prioridade.
- **Imagem orbital:** imagem original, imagem processada, fonte NASA GIBS opcional e métricas extraídas por OpenCV.
- **IPHO:** tabela de priorização com indicadores, score ML e barras de progresso.
- **Orquestração:** agentes técnicos e camadas da arquitetura operacional.
- **Tempo real:** leituras ambientais de `dados_sensores.jsonl`, gráfico temporal e atualização manual ou automática.
- **Relatório IA:** geração de relatório com RAG local, API LLM ou fallback local.

A navegação usa `st.segmented_control` com estado salvo em `st.session_state`. Assim, ações que causam rerun, como gerar relatório por LLM, mantêm o usuário na mesma visão e renderizam apenas o conteúdo ativo.

### 6.2 Análise de Imagem Orbital

O módulo `src/orbital/image_analysis.py` usa OpenCV para:

- carregar imagem por arquivo ou upload;
- converter a imagem para HSV;
- aplicar máscaras de cor para água, vegetação e solo exposto;
- aplicar k-means não supervisionado aos pixels da cena;
- combinar o resultado HSV com os clusters semânticos;
- limpar ruídos com operações morfológicas;
- calcular percentuais por máscara;
- calcular confiança de segmentação;
- gerar uma tabela YOLO-ready por contornos OpenCV com classe, confiança e caixa delimitadora;
- gerar imagem processada com sobreposição visual.

### 6.3 Fonte Orbital NASA GIBS

O módulo `src/orbital/nasa_gibs.py` integra a aplicação ao NASA Global Imagery Browse Services por WMS. A interface permite selecionar camada, recorte e data. A chamada retorna uma imagem raster que entra no mesmo pipeline de visão computacional das amostras locais.

Referência oficial: https://nasa-gibs.github.io/gibs-api-docs/access-basics/

Camadas configuradas:

- MODIS Terra Corrected Reflectance True Color.
- VIIRS SNPP Corrected Reflectance True Color.
- MODIS Terra Corrected Reflectance Bands 7-2-1.

Recortes configurados:

- Yanomami / Roraima.
- Alto Rio Negro / Amazonas.
- Amazônia Ocidental.

Se a rede ou o serviço externo falhar, a aplicação preserva a demonstração com amostra local ou upload.

### 6.4 IPHO

O módulo `src/orbital/priority_index.py` implementa o índice:

```text
IPHO =
(0.30 x risco ambiental) +
(0.25 x risco sanitário derivado dos casos) +
(0.20 x isolamento logístico) +
(0.15 x intensidade de chuva) +
(0.10 x área afetada por imagem orbital)
```

Classificação:

```text
0 a 39   = Baixa prioridade
40 a 69  = Média prioridade
70 a 100 = Alta prioridade
```

O módulo `src/orbital/ml_risk_model.py` adiciona validação preditiva complementar. Ele calcula `ml_risk_score` por uma função logística calibrada sobre os fatores normalizados e gera `IPHO_validated` com:

```text
IPHO_validated = 0.75 x IPHO + 0.25 x ml_risk_score
```

O IPHO explicável segue disponível, e o IPHO validado é usado para ordenação operacional.

### 6.5 RAG e Relatório com IA Generativa

O módulo `src/orbital/llm_client.py` implementa um cliente para API LLM compatível com Chat Completions. O módulo `src/orbital/report_generator.py` monta o prompt com:

- comunidade;
- território;
- prioridade;
- IPHO;
- risco ambiental;
- intensidade de chuva;
- isolamento logístico;
- casos sanitários simulados;
- risco sanitário normalizado;
- área afetada pela imagem orbital;
- trechos recuperados do corpus local em `docs/rag_corpus/`.

O módulo `src/orbital/rag.py` faz uma recuperação simples por similaridade léxica. Ele busca protocolos humanitários, saúde ambiental e logística nos documentos locais, depois injeta os trechos no prompt da API e no relatório local. Isso demonstra RAG/NLP sem depender de banco vetorial externo durante a apresentação.

O relatório deve conter:

- resumo da situação;
- nível de prioridade;
- justificativa;
- recomendações;
- próximos passos.

Se a API não estiver configurada ou falhar, a aplicação gera um relatório local com a mesma estrutura.

### 6.6 Detector YOLO-Ready

O módulo `src/orbital/yolo_detector.py` entrega uma saída compatível com o formato esperado em detectores YOLO: classe, confiança e caixa delimitadora. Para manter o MVP executável sem downloads pesados, o projeto usa um fallback documentado por contornos OpenCV sobre as máscaras orbitais.

Essa escolha permite demonstrar a etapa de detecção orbital na interface e deixa claro o ponto de substituição por um YOLO treinado com imagens orbitais anotadas.

### 6.7 Orquestração Multiagente

O módulo `src/orbital/mission_agents.py` organiza decisões em agentes especializados:

- Agente orbital: identifica fonte NASA GIBS, upload ou amostra local.
- Agente de visão computacional: resume métricas visuais e confiança.
- Agente IPHO: ordena comunidades por prioridade validada.
- Agente preditivo ML: compara score ML com o IPHO explicável.
- Agente generativo: controla API LLM ou fallback local.
- Agente IoT/sensores: aponta o módulo de sensores/ESP32.
- Agente cloud/distribuído: descreve o processamento em lote e escalabilidade.

Essa camada transforma o dashboard em uma arquitetura operacional mais próxima de sistemas multiagentes e distribuídos.

### 6.8 Sensores, Tempo Real, Automação e Machine Learning Complementar

O módulo `src/sentinela/` permanece no repositório como evidência técnica complementar:

- `api_sensores.py` expõe uma API Flask em `/sensores` para receber temperatura, umidade e chuva de um simulador ou de um ESP32 real.
- `simulador_sensores.py` envia leituras periódicas para a API, simulando uma borda de coleta ambiental.
- `dados_sensores.jsonl` guarda as leituras recebidas em formato incremental.
- `treina_modelo_rn.py` treina uma rede neural simples com TensorFlow/Keras para estimar risco a partir de chuva, temperatura e umidade.
- `scheduler.py` automatiza ingestões climáticas em intervalo fixo.

Esse bloco não substitui o dashboard orbital, mas demonstra integração com sensores, automação e Machine Learning quando aplicável à proposta.

O módulo `src/orbital/sensor_stream.py` conecta esse histórico ao dashboard. A visão **Tempo real** lê as entradas mais recentes de `dados_sensores.jsonl`, calcula risco por temperatura, umidade e chuva, exibe métricas operacionais e permite atualização manual ou automática.

## 7. Arquitetura

```text
Imagem orbital / upload / NASA GIBS opcional
          ↓
OpenCV: HSV + k-means para água, vegetação e solo exposto
          ↓
Detector YOLO-ready por contornos OpenCV
          ↓
Métricas visuais: área afetada e risco ambiental
          ↓
CSV de comunidades: chuva, isolamento, casos e coordenadas
          ↓
Cálculo do IPHO + score preditivo ML
          ↓
Dashboard Streamlit + fluxo de sensores em tempo real
          ↓
Orquestração multiagente
          ↓
RAG local + API LLM ou fallback local
          ↓
Relatório humanitário automatizado
```

## 8. Estrutura de Pastas

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
    cena_surucucu_orbital.png
  processed/
docs/
tests/
```

## 9. Módulos Principais

### `src/app.py`

Arquivo de entrada do Streamlit. Ajusta o path de importação e chama `orbital.app.main()`.

### `src/orbital/app.py`

Contém a interface Streamlit, o seletor de visão, o mapa Folium, cards, tabela, upload/seleção de imagem e acionamento do relatório.

### `src/orbital/image_analysis.py`

Contém a lógica de visão computacional com OpenCV, HSV, k-means, máscaras morfológicas e confiança de segmentação.

### `src/orbital/nasa_gibs.py`

Contém a integração WMS com NASA GIBS para baixar cenas orbitais por data, camada e recorte.

### `src/orbital/priority_index.py`

Contém o cálculo do IPHO, normalização de casos sanitários e classificação de prioridade.

### `src/orbital/ml_risk_model.py`

Contém o score preditivo complementar usado para validar o IPHO.

### `src/orbital/mission_agents.py`

Contém a orquestração multiagente exibida no dashboard.

### `src/orbital/rag.py`

Contém a recuperação local de trechos humanitários usados como contexto do relatório.

### `src/orbital/yolo_detector.py`

Contém o detector YOLO-ready com fallback por contornos OpenCV.

### `src/orbital/sensor_stream.py`

Contém a leitura do fluxo JSONL de sensores e o cálculo de risco em tempo real.

### `src/orbital/report_generator.py`

Contém o relatório local, o contexto quantitativo, o contexto RAG e o prompt usado pela API LLM.

### `src/orbital/llm_client.py`

Contém o cliente HTTP para chamada de API LLM compatível com Chat Completions.

### `src/orbital/sample_assets.py`

Gera uma imagem orbital sintética para demonstração sem depender de download externo.

### `src/sentinela/api_sensores.py`

API Flask complementar para receber dados ambientais de sensores ou simuladores.

### `src/sentinela/treina_modelo_rn.py`

Script de treinamento de rede neural simples usando leituras ambientais salvas em JSONL.

## 10. Decisões Técnicas

### Streamlit

Escolhido para entregar um dashboard funcional rapidamente, com suporte a upload, navegação persistente, tabela interativa e integração com mapas.

### OpenCV

Usado para demonstrar visão computacional aplicada a imagens orbitais. O MVP usa segmentação por faixas HSV, suficiente para uma prova de conceito visual e explicável.

### Folium

Usado para mapa interativo com pontos de comunidades, marcador por prioridade e camada de satélite.

### CSV Local

Usado para simular dados de comunidades e evitar dependência de APIs externas durante a apresentação.

### NASA GIBS

Usado para demonstrar integração com fonte espacial real. A aplicação mantém fallback local para evitar falha de apresentação por rede indisponível.

### Modelo Preditivo Leve

Usado para complementar a heurística IPHO com uma camada de validação baseada em função logística. O objetivo é didático e operacional: comparar uma regra explicável com um score preditivo.

### API LLM com Fallback

O fallback local evita que a apresentação falhe por ausência de chave, internet ou indisponibilidade da API. A integração real permanece disponível quando `LLM_API_KEY` e `LLM_MODEL` são configurados. O prompt recebe contexto recuperado por RAG para aproximar a resposta de protocolos humanitários documentados.

### Detector YOLO-Ready

Implementado como placeholder funcional e documentado. Ele usa contornos OpenCV para devolver caixas delimitadoras e classes orbitais em formato compatível com uma futura troca por pesos YOLO reais.

### Sensores e Automação

Mantidos como módulo complementar para evidenciar automação inteligente e integração com sensores. A API Flask e o simulador representam uma arquitetura substituível por ESP32; o scheduler representa ingestão periódica; e a rede neural demonstra Machine Learning com dados ambientais.

## 11. Execução

Instalar dependências:

```bash
pip install -r requirements.txt
```

Gerar imagem de amostra, se necessário:

```bash
python3 src/orbital/sample_assets.py
```

Rodar aplicação:

```bash
streamlit run src/app.py
```

Rodar testes:

```bash
python3 -m pytest
```

## 12. Configuração da API LLM

Criar `.env` na raiz do projeto:

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

`LLM_API_URL` pode apontar para qualquer provedor compatível com o formato Chat Completions.

O cliente envia `stream: false` por padrão. Caso `LLM_STREAM=true` seja configurado, ou caso o provedor devolva `text/event-stream` mesmo sem a flag, o cliente acumula os chunks antes de retornar o relatório completo para a interface.

Para Google AI Studio/Gemini, use o endpoint `https://generativelanguage.googleapis.com/v1beta/openai/chat/completions` e `LLM_TIMEOUT_SECONDS=60` em demonstrações. O cliente aplica `LLM_REASONING_EFFORT=low` automaticamente para esse endpoint quando a variável não está definida, pois modelos Gemini podem consumir parte do orçamento em raciocínio. Se a API sinalizar `finish_reason=length`, o cliente solicita uma continuação e valida se as seções obrigatórias do relatório foram preenchidas antes de renderizar a saída.

## 13. Testes

Os testes em `tests/test_orbital.py` cobrem:

- cálculo do IPHO;
- normalização de casos sanitários;
- ordenação por prioridade;
- detecção simples de água e vegetação;
- detecções YOLO-ready;
- recuperação RAG;
- leitura do fluxo de sensores;
- geração de relatório local;
- criação de prompt para LLM;
- cliente de API LLM com HTTP falso;
- legenda do mapa.

Os testes legados em `tests/test_ingest.py` cobrem ingestão e deduplicação de CSVs.

## 14. Limitações do MVP

- A imagem orbital de amostra é sintética.
- A integração NASA GIBS depende de rede e disponibilidade do serviço externo.
- As faixas HSV são simples e não substituem modelos robustos de segmentação.
- O k-means melhora a segmentação, mas ainda não equivale a um modelo supervisionado como YOLO ou U-Net.
- O detector YOLO-ready é um placeholder funcional por contornos OpenCV, não um modelo treinado com pesos reais.
- O RAG é local e léxico; não usa embeddings nem banco vetorial.
- Os dados de comunidades são simulados.
- O fluxo de sensores em tempo real depende do arquivo JSONL gerado pelo simulador/API.
- A API LLM depende de configuração externa.
- Não há autenticação de usuários.
- Não há persistência dos relatórios gerados.
- O IPHO é uma heurística explicável, não uma validação estatística oficial.

## 15. Evoluções Futuras

- Integrar imagens reais de satélite.
- Conectar APIs meteorológicas e hidrológicas.
- Adicionar séries temporais por comunidade.
- Usar modelos de segmentação mais robustos.
- Substituir o YOLO-ready por modelo YOLO treinado com imagens orbitais anotadas.
- Executar processamento em fila cloud/distribuída.
- Integrar banco de dados para histórico de relatórios.
- Criar alertas automáticos por prioridade alta.
- Adicionar autenticação e perfis de usuário.
- Exportar PDF diretamente pelo dashboard.
- Evoluir o RAG local para embeddings, banco vetorial e fontes humanitárias versionadas.

## 16. Evidências para Apresentação

Durante o vídeo, demonstrar:

- abertura do dashboard;
- seleção de imagem orbital;
- carregamento NASA GIBS, se houver rede;
- imagem original e processada;
- métricas de água, vegetação, solo exposto e área afetada;
- tabela YOLO-ready com caixas delimitadoras;
- score ML e IPHO validado;
- visão de orquestração multiagente;
- visão Tempo real com sensores e atualização;
- mapa com legenda;
- tabela IPHO;
- geração do relatório IA com contexto RAG;
- fallback local caso a API LLM não esteja configurada.
