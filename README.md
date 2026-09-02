# OneNoteKB — Pipeline de Base de Conhecimento com Python + IA Local

Projeto para extrair conteúdo de blocos do Microsoft OneNote, transformar páginas em uma base JSON estruturada, aplicar regras determinísticas em Python, usar um LLM local via Ollama para interpretação controlada e gerar artigos padronizados em Word.

## Resultado alcançado na primeira base

Na validação da base ECV-MG, o processamento em lote trabalhou com 89 registros: 88 foram aprovados automaticamente e 1 apresentou timeout de comunicação. Os casos com conteúdo atípico podem ser separados para revisão manual antes da publicação final.

## Arquitetura

```text
Microsoft OneNote
      ↓
Microsoft Graph API + MSAL
      ↓
onenote_extractor.py
      ↓
output/base_bruta.json
      ↓
normalizar_base.py
      ↓
output/processamento/base_normalizada.json
      ↓
filtrar_escopo_ecv_mg.py
      ↓
output/processamento/base_normalizada_ecv_mg.json
      ↓
processar_artigos_ollama.py
      ↓
JSONs estruturados e validados
      ↓
gerar_artigos_ollama_word.py
      ↓
Artigos Word (ERRO / PROCEDIMENTO)
```

## Tecnologias

Python, Microsoft Graph API, Microsoft Entra ID, MSAL, BeautifulSoup, JSON, Ollama, Qwen 2.5, PowerShell e python-docx.

## Estrutura do repositório

```text
OneNoteKB-GitHub/
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── config/
│   └── fontes.example.json
├── output/
│   ├── .gitkeep
│   └── processamento/
│       └── .gitkeep
├── onenote_extractor.py
├── normalizar_base.py
├── filtrar_escopo_ecv_mg.py
├── processar_artigos_ollama.py
└── gerar_artigos_ollama_word.py
```

## Segurança antes de publicar

O repositório não deve conter token de autenticação, `.env`, `.token_cache.json`, e-mails internos, páginas extraídas, JSONs reais da empresa nem documentos Word gerados com conteúdo corporativo. Esses itens já estão cobertos pelo `.gitignore` desta versão.

## Instalação

No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Instale também o Ollama e baixe o modelo utilizado no projeto:

```powershell
ollama pull qwen2.5:1.5b-instruct-q5_0
```

## Configuração do Microsoft Graph

1. Copie `.env.example` para `.env`.
2. Informe `ONENOTE_CLIENT_ID` e `ONENOTE_TENANT_ID`.
3. Copie `config/fontes.example.json` para `config/fontes.json`.
4. Informe as contas que possuem os notebooks que serão lidos.
5. A aplicação Microsoft Entra utilizada precisa possuir a permissão necessária para leitura do OneNote (`Notes.Read.All`), conforme a política da organização.

Exemplo:

```powershell
Copy-Item .env.example .env
Copy-Item .\configontes.example.json .\configontes.json
```

## Execução

### 1. Extrair OneNote

```powershell
.\.venv\Scripts\python.exe .\onenote_extractor.py
```

O extrator trabalha com inventário, checkpoint, retry e armazenamento do HTML/texto das páginas.

### 2. Normalizar a base

```powershell
.\.venv\Scripts\python.exe .
ormalizar_base.py
```

### 3. Aplicar o escopo ECV-MG

```powershell
.\.venv\Scripts\python.exe .iltrar_escopo_ecv_mg.py
```

> O filtro ECV-MG representa o escopo validado até aqui. A evolução para múltiplas bases configuráveis está planejada como próxima etapa do projeto.

### 4. Testar o Ollama

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:11434/api/generate" `
  -Method Post `
  -ContentType "application/json" `
  -Body (@{
      model = "qwen2.5:1.5b-instruct-q5_0"
      prompt = "Responda somente com a palavra OK."
      stream = $false
  } | ConvertTo-Json)
```

### 5. Processar um artigo

```powershell
.\.venv\Scripts\python.exe .\processar_artigos_ollama.py 80
```

### 6. Processar a base em lote

```powershell
.\.venv\Scripts\python.exe .\processar_artigos_ollama.py --todos-ecv --reprocessar
```

### 7. Gerar um Word específico

```powershell
.\.venv\Scripts\python.exe .\gerar_artigos_ollama_word.py 80
```

### 8. Gerar todos os Word aprovados

```powershell
.\.venv\Scripts\python.exe .\gerar_artigos_ollama_word.py
```

## Estratégia Python + IA local

A arquitetura evita entregar toda a responsabilidade ao LLM. O Python preserva regras determinísticas, hierarquia, evidências, observações, tickets de referência e validações. O Ollama é utilizado apenas onde interpretação textual agrega valor. O resultado retornado passa novamente por saneamento e validação em Python antes de ser marcado como aprovado.

Essa abordagem reduz alucinações e impede que o modelo reorganize livremente informações que precisam permanecer fiéis à fonte.

## Funcionalidades implementadas

- autenticação Microsoft Entra com MSAL e cache local;
- consulta de notebooks de múltiplas contas via Microsoft Graph;
- inventário de notebooks, seções, grupos e páginas;
- paginação e retry para chamadas Graph;
- checkpoint para retomada da extração;
- armazenamento de HTML e texto das páginas;
- base bruta em JSON;
- normalização e IDs internos estáveis;
- filtro de notebook/seções e preservação do nome retornado pelo Graph;
- classificação estrutural entre ERRO e PROCEDIMENTO pelo escopo da seção;
- pré-segmentação determinística;
- detecção conservadora de etapas e subgrupos;
- tratamento de tickets/protocolos de referência;
- separação de objetivo, relato, causa, evidências, observações e procedimento;
- integração local com Ollama;
- bloqueio de estruturas serializadas em mensagens de erro;
- processamento individual e em lote;
- relatórios de aprovação, revisão e erro;
- geração de Word com numeração persistente ERRO/PRC;
- suporte a revisão manual de artigos fora do padrão.

## Próximas etapas

- generalizar o filtro para as demais bases do OneNote;
- transformar regras de bases em configuração externa;
- consolidar múltiplas bases sem colisão de códigos;
- ampliar a auditoria automática;
- preparar integração futura com outras fontes de conhecimento.

## Observação

Este repositório contém a estrutura e o código do projeto, mas não inclui conteúdo interno, documentos corporativos, credenciais ou dados reais extraídos do OneNote.
