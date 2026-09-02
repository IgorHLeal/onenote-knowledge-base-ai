# OneNoteKB — Pipeline de Base de Conhecimento com Python + IA Local

Pipeline para extração, normalização, classificação e geração de artigos de uma base de conhecimento utilizando **Python, Microsoft Graph API e Inteligência Artificial local com Ollama**.

O projeto surgiu a partir de um problema real: transformar diferentes bases de conhecimento armazenadas no OneNote, com estruturas e padrões distintos, em artigos organizados e padronizados.

A solução utiliza uma abordagem híbrida:

- **Python** para processamento determinístico, regras, validações e estruturação dos dados;
- **Ollama + LLM local** para tarefas que exigem interpretação de conteúdo;
- **Microsoft Graph API** para integração com o OneNote;
- **Microsoft Entra ID + MSAL** para autenticação;
- **python-docx** para geração dos documentos finais.

> Este projeto foi desenvolvido com auxílio de Inteligência Artificial Generativa. O código está passando por um processo contínuo de revisão, estudo e refatoração para garantir compreensão integral da implementação e evolução da qualidade técnica da solução.

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


## 🤖 Uso de Inteligência Artificial no desenvolvimento

Este projeto foi desenvolvido com o auxílio de ferramentas de Inteligência Artificial Generativa durante diferentes etapas do processo.

A IA foi utilizada como ferramenta de apoio principalmente para:

- auxiliar na definição da arquitetura inicial do projeto;
- apoiar a implementação e refatoração de código Python;
- analisar erros e resultados durante os testes;
- sugerir melhorias nas regras de processamento;
- auxiliar na criação das validações estruturais;
- apoiar a documentação do projeto;
- estruturar a integração entre Python e o modelo executado localmente através do Ollama.

Além disso, o próprio projeto utiliza um LLM local através do Ollama como parte do pipeline de processamento dos artigos.

### Revisão e aprendizado do código

Como parte da evolução deste projeto, será realizada uma revisão técnica completa do código desenvolvido.

O objetivo dessa etapa é revisar cada módulo, função e regra implementada para:

- compreender detalhadamente o funcionamento do código;
- revisar decisões de arquitetura;
- identificar possíveis simplificações e melhorias;
- validar tratamento de erros e casos extremos;
- melhorar organização, legibilidade e manutenibilidade;
- revisar aspectos de segurança;
- identificar possíveis problemas de performance;
- aumentar a cobertura de testes;
- garantir domínio técnico sobre todas as partes da solução.

A utilização de IA neste projeto não substitui o processo de aprendizado e validação técnica.

O projeto também funciona como um ambiente prático de estudo de Python, APIs, automação, processamento de dados, Microsoft Graph, autenticação, LLMs e engenharia de software.

> **Nota:** o código continuará sendo revisado e refatorado à medida que o projeto evoluir e novas bases de conhecimento forem incorporadas.

## 🚧 Status do projeto

**Em desenvolvimento**

### Concluído

- [x] Autenticação no Microsoft Graph
- [x] Extração de conteúdo do OneNote
- [x] Persistência de cache de autenticação
- [x] Checkpoint de extração
- [x] Normalização dos dados
- [x] Classificação de artigos
- [x] Integração com Ollama
- [x] Processamento híbrido Python + LLM
- [x] Processamento em lote
- [x] Validação estrutural dos artigos
- [x] Geração automática de documentos Word
- [x] Primeira base processada

### Em andamento

- [ ] Generalização da arquitetura para múltiplas bases
- [ ] Processamento dos demais notebooks
- [ ] Revisão técnica completa do código
- [ ] Refatoração dos módulos
- [ ] Criação de testes automatizados
- [ ] Melhoria do tratamento de exceções
- [ ] Documentação da arquitetura
- [ ] Revisão de segurança
- [ ] Otimização de performance
