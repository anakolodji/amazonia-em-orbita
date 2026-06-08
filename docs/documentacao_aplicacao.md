# Documentação da Aplicação

## 1. Identificação

**Nome:** Amazônia em Órbita

**Subtítulo:** Sistema inteligente para priorização de áreas vulneráveis usando imagens de satélite, risco ambiental e geração automática de relatórios humanitários.

**Tipo de solução:** Prova de conceito de inteligência espacial aplicada à Terra.

**Contexto da GS:** uso de Inteligência Artificial, visão computacional, análise de dados e dashboard inteligente para gerar impacto positivo na Terra a partir de dados orbitais.

## 2. Resumo Executivo

O Amazônia em Órbita é uma plataforma Streamlit que apoia a priorização de comunidades vulneráveis na Amazônia. A aplicação combina imagem orbital, dados simulados de chuva, isolamento logístico, casos sanitários e risco ambiental para calcular o **IPHO - Índice de Prioridade Humanitária Orbital**.

O sistema também processa imagens com OpenCV para estimar água, vegetação, solo exposto e área afetada. Com esses indicadores, o dashboard apresenta mapa, cards, gráficos, tabela de priorização e relatório humanitário. A etapa de relatório pode chamar uma API de LLM compatível com Chat Completions; quando a API não está configurada, o app usa um fallback local para manter a demonstração funcionando.

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
- Detectar água, vegetação e solo exposto.
- Calcular percentual de área afetada.
- Cruzar dados visuais com dados sanitários, climáticos e logísticos.
- Calcular o IPHO para cada comunidade.
- Classificar comunidades em prioridade baixa, média ou alta.
- Exibir resultados em dashboard Streamlit.
- Gerar relatório humanitário com API LLM ou fallback local.

## 5. Público-Alvo

- Equipes humanitárias e sanitárias.
- Analistas ambientais.
- Gestores de resposta emergencial.
- Professores e avaliadores da GS.
- Times acadêmicos que precisam demonstrar integração entre IA, visão computacional e análise de dados.

## 6. Funcionalidades

### 6.1 Dashboard Streamlit

A interface principal fica em `src/orbital/app.py` e é aberta por `src/app.py`. Ela contém quatro visões acessadas por um seletor persistente:

- **Território:** visão geral, cards, mapa e gráfico de distribuição de prioridade.
- **Imagem orbital:** imagem original, imagem processada e métricas extraídas por OpenCV.
- **IPHO:** tabela de priorização com indicadores e barras de progresso.
- **Relatório IA:** geração de relatório com API LLM ou fallback local.

A navegação usa `st.segmented_control` com estado salvo em `st.session_state`. Assim, ações que causam rerun, como gerar relatório por LLM, mantêm o usuário na mesma visão e renderizam apenas o conteúdo ativo.

### 6.2 Análise de Imagem Orbital

O módulo `src/orbital/image_analysis.py` usa OpenCV para:

- carregar imagem por arquivo ou upload;
- converter a imagem para HSV;
- aplicar máscaras de cor para água, vegetação e solo exposto;
- limpar ruídos com operações morfológicas;
- calcular percentuais por máscara;
- gerar imagem processada com sobreposição visual.

### 6.3 IPHO

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

### 6.4 Relatório com IA Generativa

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
- área afetada pela imagem orbital.

O relatório deve conter:

- resumo da situação;
- nível de prioridade;
- justificativa;
- recomendações;
- próximos passos.

Se a API não estiver configurada ou falhar, a aplicação gera um relatório local com a mesma estrutura.

## 7. Arquitetura

```text
Imagem orbital / upload
          ↓
OpenCV: máscaras de água, vegetação e solo exposto
          ↓
Métricas visuais: área afetada e risco ambiental
          ↓
CSV de comunidades: chuva, isolamento, casos e coordenadas
          ↓
Cálculo do IPHO
          ↓
Dashboard Streamlit
          ↓
API LLM ou fallback local
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
    priority_index.py
    report_generator.py
    sample_assets.py
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

Contém a lógica de visão computacional com OpenCV.

### `src/orbital/priority_index.py`

Contém o cálculo do IPHO, normalização de casos sanitários e classificação de prioridade.

### `src/orbital/report_generator.py`

Contém o relatório local, o contexto quantitativo e o prompt usado pela API LLM.

### `src/orbital/llm_client.py`

Contém o cliente HTTP para chamada de API LLM compatível com Chat Completions.

### `src/orbital/sample_assets.py`

Gera uma imagem orbital sintética para demonstração sem depender de download externo.

## 10. Decisões Técnicas

### Streamlit

Escolhido para entregar um dashboard funcional rapidamente, com suporte a upload, navegação persistente, tabela interativa e integração com mapas.

### OpenCV

Usado para demonstrar visão computacional aplicada a imagens orbitais. O MVP usa segmentação por faixas HSV, suficiente para uma prova de conceito visual e explicável.

### Folium

Usado para mapa interativo com pontos de comunidades, marcador por prioridade e camada de satélite.

### CSV Local

Usado para simular dados de comunidades e evitar dependência de APIs externas durante a apresentação.

### API LLM com Fallback

O fallback local evita que a apresentação falhe por ausência de chave, internet ou indisponibilidade da API. A integração real permanece disponível quando `LLM_API_KEY` e `LLM_MODEL` são configurados.

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
- geração de relatório local;
- criação de prompt para LLM;
- cliente de API LLM com HTTP falso;
- legenda do mapa.

Os testes legados em `tests/test_ingest.py` cobrem ingestão e deduplicação de CSVs.

## 14. Limitações do MVP

- A imagem orbital de amostra é sintética.
- As faixas HSV são simples e não substituem modelos robustos de segmentação.
- Os dados de comunidades são simulados.
- A API LLM depende de configuração externa.
- Não há autenticação de usuários.
- Não há persistência dos relatórios gerados.
- O IPHO é uma heurística explicável, não uma validação estatística oficial.

## 15. Evoluções Futuras

- Integrar imagens reais de satélite.
- Conectar APIs meteorológicas e hidrológicas.
- Adicionar séries temporais por comunidade.
- Usar modelos de segmentação mais robustos.
- Integrar banco de dados para histórico de relatórios.
- Criar alertas automáticos por prioridade alta.
- Adicionar autenticação e perfis de usuário.
- Exportar PDF diretamente pelo dashboard.
- Incorporar RAG com documentos humanitários e protocolos de resposta.

## 16. Evidências para Apresentação

Durante o vídeo, demonstrar:

- abertura do dashboard;
- seleção de imagem orbital;
- imagem original e processada;
- métricas de água, vegetação, solo exposto e área afetada;
- mapa com legenda;
- tabela IPHO;
- geração do relatório IA;
- fallback local caso a API LLM não esteja configurada.
