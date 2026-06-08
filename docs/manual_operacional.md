# Manual Operacional

Este manual descreve como executar e demonstrar o Amazônia em Órbita.

## 1. Pré-Requisitos

- Python 3.12 ou compatível.
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

### 4.6 Visão IPHO

Use essa visão para explicar a priorização:

- risco ambiental;
- intensidade de chuva;
- isolamento logístico;
- casos sanitários;
- risco sanitário normalizado;
- área afetada pela imagem;
- IPHO final;
- prioridade baixa, média ou alta.

### 4.7 Visão Relatório IA

Use essa visão para gerar a síntese humanitária.

A navegação mantém a visão ativa mesmo depois do rerun do Streamlit. Portanto, ao clicar em **Gerar relatório humanitário**, o usuário permanece em **Relatório IA** enquanto a resposta é criada.

Se a API LLM estiver configurada:

- deixe **Usar API LLM** ligado;
- clique em **Gerar relatório humanitário**;
- aguarde a resposta da API.

Se a API LLM não estiver configurada:

- o app informa que usará fallback local;
- o relatório é gerado sem interromper a demonstração.

## 5. Como Explicar no Vídeo

Sugestão de sequência:

```text
1. Apresentar o problema de priorização em regiões remotas.
2. Mostrar que a solução usa imagem orbital e dados simulados.
3. Demonstrar o processamento da imagem.
4. Explicar o IPHO e seus pesos.
5. Mostrar mapa e tabela de comunidades.
6. Gerar relatório IA.
7. Concluir com impacto esperado e evoluções futuras.
```

## 6. Problemas Comuns

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

## 7. Validação

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
