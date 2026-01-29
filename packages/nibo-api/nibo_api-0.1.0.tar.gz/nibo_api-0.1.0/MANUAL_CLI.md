# Manual do CLI - Nibo API

Este manual descreve todos os comandos disponíveis na interface de linha de comando (CLI) unificada para interagir com as APIs Nibo:

- `manage.py obrigacoes` - API Nibo Obrigações
- `manage.py empresa` - API Nibo Empresa

## Índice

1. [Instalação e Configuração](#instalação-e-configuração)
2. [CLI Obrigações](#cli-obrigações)
   - [Escritórios](#escritórios)
   - [Clientes](#clientes)
   - [Obrigações](#obrigações)
   - [Contatos](#contatos)
   - [Departamentos](#departamentos)
   - [Tarefas](#tarefas)
   - [Criar Tarefa](#criar-tarefa)
   - [CNAEs](#cnaes)
   - [Grupos de Clientes](#grupos-de-clientes)
   - [Usuários](#usuários)
   - [Arquivos](#arquivos)
     - [Criar Arquivo](#criar-arquivo)
     - [Upload Arquivo](#upload-arquivo)
3. [CLI Empresa](#cli-empresa)
   - [Organizações](#organizações)
   - [Clientes](#clientes-1)
   - [Criar Cliente](#criar-cliente)
   - [Agendamentos de Recebimento](#agendamentos-de-recebimento)
   - [Agendamentos de Pagamento](#agendamentos-de-pagamento)
   - [Criar Agendamento de Recebimento](#criar-agendamento-de-recebimento)
   - [Criar Agendamento de Pagamento](#criar-agendamento-de-pagamento)
   - [Categorias](#categorias)
   - [Fornecedores](#fornecedores)
4. [Opções Globais](#opções-globais)
5. [Exemplos Práticos](#exemplos-práticos)

---

## Instalação e Configuração

### Pré-requisitos

- Python 3.7 ou superior
- Pacote `requests` instalado
- Arquivo `settings.json` configurado com as credenciais da API

### Configuração

Certifique-se de que o arquivo `settings.json` está configurado corretamente:

```json
{
  "api_tokens": {
    "org_123": "TOKEN_ORGANIZACAO_1",
    "empresa_principal": "TOKEN_ORGANIZACAO_2"
  },
  "organizacoes": {
    "empresa_principal": "org_123"
  },
  "obrigacoes_api_token": "seu-token-obrigacoes",
  "empresa_base_url": "https://api.nibo.com.br/empresas/v1",
  "obrigacoes_base_url": "https://api.nibo.com.br/accountant/api/v1",
  "obrigacoes_user_id": null,
  "tokens_path": null
}
```

**Estrutura de Tokens:**

- `api_tokens`: Dicionário com tokens por organização (ID ou código simplificado)
- `organizacoes`: Mapeamento opcional de código para ID

Ou configure via variáveis de ambiente (prioritário):

**Para API Empresa (múltiplas organizações):**

- `NIBO_API_TOKEN_<ID_OU_CODIGO>`: Token para organização específica
  - Exemplo: `NIBO_API_TOKEN_org_123` ou `NIBO_API_TOKEN_empresa_principal`
- `NIBO_EMPRESA_BASE_URL`

**Para API Obrigações:**

- `NIBO_OBRIGACOES_API_TOKEN`
- `NIBO_OBRIGACOES_BASE_URL`
- `NIBO_OBRIGACOES_USER_ID`

**Segurança:**

- Use variáveis de ambiente para maior segurança
- Tokens podem ser criptografados com prefixo `encrypted:` (requer `NIBO_ENCRYPTION_KEY`)
- Arquivo separado `tokens.json` também é suportado (configure via `tokens_path`)

---

## CLI Obrigações

Esta seção descreve os comandos disponíveis no módulo `manage.py obrigacoes` para interagir com a API Nibo Obrigações.

### Comandos Disponíveis

### Escritórios

Lista todos os escritórios contábeis disponíveis.

**Sintaxe:**

```bash
python manage.py obrigacoes escritorios [--json] [--escritorio ESCRITORIO]
```

**Exemplos:**

```bash
# Listar todos os escritórios
python manage.py obrigacoes escritorios

# Listar em formato JSON
python manage.py obrigacoes escritorios --json
```

---

### Clientes

Lista clientes de um escritório contábil.

**Sintaxe:**

```bash
python manage.py obrigacoes clientes [--nome NOME] [--json] [--escritorio ESCRITORIO]
```

**Parâmetros:**

- `--nome`: Nome do cliente para filtrar (busca parcial, opcional)

**Exemplos:**

```bash
# Listar todos os clientes
python manage.py obrigacoes clientes

# Filtrar por nome (busca parcial)
python manage.py obrigacoes clientes --nome "BR"

# Listar em formato JSON
python manage.py obrigacoes clientes --nome "BR" --json
```

**Nota:** A busca por nome é parcial, então `--nome "BV"` encontrará clientes como "BV - BRAGGION & VILACA LTDA." e "BV 3F MATERIAIS PARA CONSTRUÇÃO LTDA - ME".

---

### Obrigações

Lista obrigações de um ou mais clientes.

**Sintaxe:**

```bash
python manage.py obrigacoes obrigacoes --cliente CLIENTE [--inicio INICIO] [--fim FIM] [--simples] [--json] [--escritorio ESCRITORIO]
```

**Parâmetros:**

- `--cliente` (obrigatório): Nome do cliente ou UUID do cliente
- `--inicio`: Data de início do período (formato: DD/MM/YYYY, padrão: hoje)
- `--fim`: Data de fim do período (formato: DD/MM/YYYY, padrão: 31/12 do ano atual)
- `--simples`: Exibe apenas informações básicas (sem detalhes)

**Exemplos:**

```bash
# Listar obrigações de um cliente (período padrão: hoje até 31/12 do ano atual)
python manage.py obrigacoes obrigacoes --cliente "BR"

# Listar obrigações por ID do cliente
python manage.py obrigacoes obrigacoes --cliente "24ab8c16-83d1-4bef-b4b1-f9e7c8b2e387"

# Com período customizado
python manage.py obrigacoes obrigacoes --cliente "BR" --inicio 01/01/2025 --fim 31/12/2025

# Exibição simples
python manage.py obrigacoes obrigacoes --cliente "BR" --simples

# Em formato JSON
python manage.py obrigacoes obrigacoes --cliente "BR" --json
```

**Comportamento:**

- Se o `--cliente` for um nome, busca todos os clientes que contêm esse nome e retorna obrigações de todos eles
- Se o `--cliente` for um UUID, busca obrigações apenas desse cliente específico
- O período padrão é de hoje até o final do ano atual

---

### Contatos

Lista contatos de um escritório contábil.

**Sintaxe:**

```bash
python manage.py obrigacoes contatos [--json] [--escritorio ESCRITORIO]
```

**Exemplos:**

```bash
# Listar todos os contatos
python manage.py obrigacoes contatos

# Listar em formato JSON
python manage.py obrigacoes contatos --json
```

---

### Departamentos

Lista departamentos de um escritório contábil.

**Sintaxe:**

```bash
python manage.py obrigacoes departamentos [--json] [--escritorio ESCRITORIO]
```

**Exemplos:**

```bash
# Listar todos os departamentos
python manage.py obrigacoes departamentos

# Listar em formato JSON
python manage.py obrigacoes departamentos --json
```

---

### Tarefas

Lista tarefas de um escritório contábil.

**Sintaxe:**

```bash
python manage.py obrigacoes tarefas [--usuario USUARIO] [--usuario-nome USUARIO_NOME] [--incluir-completas] [--json] [--escritorio ESCRITORIO]
```

**Parâmetros:**

- `--usuario` ou `-u`: UUID do usuário para filtrar tarefas (opcional)
- `--usuario-nome`: Nome do usuário para filtrar tarefas (busca parcial, opcional)
- `--incluir-completas`: Inclui tarefas completas (padrão: exclui tarefas com status 3 - Complete)

**Exemplos:**

```bash
# Listar tarefas não completas (padrão)
python manage.py obrigacoes tarefas

# Filtrar por nome do usuário
python manage.py obrigacoes tarefas --usuario-nome "Joao"

# Filtrar por ID do usuário
python manage.py obrigacoes tarefas --usuario "86bc7fa4-a691-4532-8ac6-0a9238faa540"

# Incluir tarefas completas também
python manage.py obrigacoes tarefas --usuario-nome "Joao" --incluir-completas

# Listar em formato JSON
python manage.py obrigacoes tarefas --usuario-nome "Joao" --json
```

**Status das Tarefas:**

- **0 - Undefined**: Nenhum status definido
- **1 - Blocked**: Tarefa bloqueada
- **2 - ToDo**: Tarefa pronta para ser iniciada
- **3 - Complete**: Tarefa concluída (excluída por padrão)

**Frequências:**

- **0 - Sem recorrência**
- **1 - Recorrência diária**
- **2 - Recorrência semanal**
- **3 - Recorrência mensal**
- **4 - Recorrência anual**

---

### Criar Tarefa

Cria uma nova tarefa em um escritório contábil.

**Sintaxe:**

```bash
python manage.py obrigacoes criar-tarefa --nome NOME [--template TEMPLATE] [--deadline DEADLINE] [--usuario-responsavel-id USUARIO_RESPONSAVEL_ID] [--cliente CLIENTE] [--descricao DESCRICAO] [--departamento DEPARTAMENTO] [--arquivos ARQUIVOS ...] [--json] [--escritorio ESCRITORIO]
```

**Parâmetros:**

- `--nome` (obrigatório se não usar template): Nome da tarefa
- `--template`: ID do template para criar tarefa a partir de template (opcional)
- `--deadline`: Data e hora limite (formato: YYYY-MM-DDTHH:MM:SS ou YYYY-MM-DD)
- `--usuario-responsavel-id` ou `-r`: ID do usuário responsável (opcional)
- `--cliente` ou `-cli`: ID do cliente associado (opcional)
- `--descricao`: Descrição da tarefa (opcional)
- `--departamento` ou `-dep`: ID do departamento relacionado (opcional)
- `--arquivos` ou `-a`: IDs de arquivos anexados (separados por espaço, opcional)

**Exemplos:**

```bash
# Criar tarefa simples
python manage.py obrigacoes criar-tarefa --nome "Nova tarefa"

# Criar tarefa com descrição
python manage.py obrigacoes criar-tarefa --nome "Tarefa importante" --descricao "Descrição detalhada da tarefa"

# Criar tarefa com usuário responsável e deadline
python manage.py obrigacoes criar-tarefa --nome "Tarefa urgente" --usuario-responsavel-id "uuid-usuario" --deadline "2025-12-31T23:59:59"

# Criar tarefa a partir de template
python manage.py obrigacoes criar-tarefa --template "uuid-template" --deadline "2025-12-31"

# Criar tarefa com cliente e departamento
python manage.py obrigacoes criar-tarefa --nome "Tarefa cliente" --cliente "uuid-cliente" --departamento "uuid-departamento"

# Criar tarefa com arquivos anexados
python manage.py obrigacoes criar-tarefa --nome "Tarefa com arquivos" --arquivos "uuid-arquivo-1" "uuid-arquivo-2"

# Listar em formato JSON
python manage.py obrigacoes criar-tarefa --nome "Tarefa" --json
```

**Nota:** A API retorna status 202 (Accepted), indicando que a tarefa foi recebida e será criada de forma assíncrona.

---

### CNAEs

Lista CNAEs (Código Nacional de Atividades Econômicas) de um escritório contábil.

**Sintaxe:**

```bash
python manage.py obrigacoes cnaes [--json] [--escritorio ESCRITORIO]
```

**Exemplos:**

```bash
# Listar todos os CNAEs
python manage.py obrigacoes cnaes

# Listar em formato JSON
python manage.py obrigacoes cnaes --json
```

---

### Grupos de Clientes

Lista grupos de clientes (tags) de um escritório contábil.

**Sintaxe:**

```bash
python manage.py obrigacoes grupos-clientes [--json] [--escritorio ESCRITORIO]
```

**Exemplos:**

```bash
# Listar todos os grupos de clientes
python manage.py obrigacoes grupos-clientes

# Listar em formato JSON
python manage.py obrigacoes grupos-clientes --json
```

---

### Usuários

Lista membros da equipe de um escritório contábil.

**Sintaxe:**

```bash
python manage.py obrigacoes usuarios [--nome NOME] [--json] [--escritorio ESCRITORIO]
```

**Parâmetros:**

- `--nome`: Nome do usuário para filtrar (busca parcial, opcional)

**Exemplos:**

```bash
# Listar todos os usuários
python manage.py obrigacoes usuarios

# Filtrar por nome (busca parcial)
python manage.py obrigacoes usuarios --nome "Joao"

# Listar em formato JSON
python manage.py obrigacoes usuarios --nome "Joao" --json
```

---

## Arquivos

### Criar Arquivo

Cria um arquivo na API e retorna ID e URL temporária (sharedAccessSignature) para fazer upload.

**Sintaxe:**

```bash
python manage.py obrigacoes criar-arquivo --arquivo CAMINHO_ARQUIVO [--nome NOME] [--json] [--escritorio ESCRITORIO]
```

**Parâmetros:**

- `--arquivo` (obrigatório): Caminho do arquivo local
- `--nome`: Nome do arquivo (opcional, usa nome do arquivo local se não fornecido)

**Exemplos:**

```bash
# Criar arquivo usando nome do arquivo local
python manage.py obrigacoes criar-arquivo --arquivo "etc/arquivo.pdf"

# Criar arquivo com nome customizado
python manage.py obrigacoes criar-arquivo --arquivo "etc/arquivo.pdf" --nome "documento.pdf"

# Listar em formato JSON
python manage.py obrigacoes criar-arquivo --arquivo "etc/arquivo.pdf" --json
```

**Retorno:**

O comando retorna:

- `id`: ID do arquivo criado
- `sharedAccessSignature`: URL temporária válida por **10 minutos** para fazer o upload

**Importante:** A URL `sharedAccessSignature` é válida por apenas 10 minutos. Use o comando `upload-arquivo` imediatamente após criar o arquivo.

---

### Upload Arquivo

Faz upload de um arquivo usando a URL temporária (sharedAccessSignature) retornada pelo comando `criar-arquivo`.

**Sintaxe:**

```bash
python manage.py obrigacoes upload-arquivo --arquivo CAMINHO_ARQUIVO --shared-access-signature URL [--json] [--escritorio ESCRITORIO]
```

**Parâmetros:**

- `--arquivo` (obrigatório): Caminho do arquivo local
- `--shared-access-signature` ou `-sas` (obrigatório se não usar --file): URL temporária retornada pelo comando `criar-arquivo`
- `--file` ou `-f`: ID do arquivo criado (obrigatório se não usar shared-access-signature, mas requer que você tenha a URL salva)
- 

**Exemplos:**

```bash
# Upload usando sharedAccessSignature retornado
python manage.py obrigacoes upload-arquivo --arquivo "etc/arquivo.pdf" --shared-access-signature "https://..."

# Listar em formato JSON
python manage.py obrigacoes upload-arquivo --arquivo "etc/arquivo.pdf" --shared-access-signature "https://..." --json
```

**Fluxo Completo (Criar + Upload):**

```bash
s# 1. Criar arquivo e obter sharedAccessSignature
python manage.py obrigacoes criar-arquivo --arquivo "etc/arquivo.pdf" --json > resultado.json

# 2. Extrair sharedAccessSignature e fazer upload (Linux/Mac)
python manage.py obrigacoes upload-arquivo --arquivo "etc/arquivo.pdf" --shared-access-signature $(jq -r '.sharedAccessSignature' resultado.json)

# Ou em Windows PowerShell:
$result = python manage.py obrigacoes criar-arquivo --arquivo "etc/arquivo.pdf" --json | ConvertFrom-Json
python manage.py obrigacoes upload-arquivo --arquivo "etc/arquivo.pdf" --shared-access-signature $result.sharedAccessSignature
```

**Nota Importante:**

- A URL `sharedAccessSignature` é válida por apenas **10 minutos** após a criação do arquivo
- O content-type do arquivo é detectado automaticamente
- Se usar `--file`, é necessário ter a URL `sharedAccessSignature` salva, pois a API não retorna essa URL após a criação

---

## CLI Empresa

Esta seção descreve os comandos disponíveis no módulo `manage.py empresa` para interagir com a API Nibo Empresa.

### Organizações

Lista todas as organizações que o usuário administrador tem acesso.

**Sintaxe:**

```bash
python manage.py empresa organizacoes [--org ID_OU_CODIGO] [--json]
```

**Parâmetros:**

- `--org` ou `--org`: ID ou código da organização para autenticação (opcional, usa primeiro token disponível se não especificado)

**Exemplos:**

```bash
# Listar todas as organizações
python manage.py empresa organizacoes

# Listar em formato JSON
python manage.py empresa organizacoes --json
```

**Nota:** Este endpoint retorna as organizações que o usuário administrador tem acesso.

---

### Clientes

Lista clientes da empresa.

**Sintaxe:**

```bash
python manage.py empresa clientes [--org ID_OU_CODIGO] [--nome NOME] [--json]
```

**Parâmetros:**

- `--org` ou `--org`: ID ou código da organização (obrigatório)
- `--nome`: Nome do cliente para filtrar (busca parcial, opcional)

**Exemplos:**

```bash
# Listar todos os clientes
python manage.py empresa clientes --org org_123

# Filtrar por nome (busca parcial)
python manage.py empresa clientes --nome "Empresa" --org org_123

# Listar em formato JSON
python manage.py empresa clientes --nome "Empresa" --org org_123 --json
```

**Nota:** A busca por nome é parcial, então `--nome "Emp"` encontrará clientes que contenham "Emp" no nome.

---

### Criar Cliente

Cria um novo cliente na empresa.

**Sintaxe:**

```bash
python manage.py empresa criar-cliente --nome NOME [--org ID_OU_CODIGO] [--tipo-documento TIPO] [--numero-documento NUMERO] [--json]
```

**Parâmetros:**

- `--nome` (obrigatório): Nome do cliente
- `--org` ou `--org`: ID ou código da organização (obrigatório)
- `--tipo-documento`: Tipo de documento ('cnpj' ou 'cpf', opcional)
- `--numero-documento`: Número do documento (opcional)

**Exemplos:**

```bash
# Criar cliente simples
python manage.py empresa criar-cliente --nome "Nova Empresa LTDA" --org org_123

# Criar cliente com CNPJ
python manage.py empresa criar-cliente --nome "Nova Empresa LTDA" --tipo-documento cnpj --numero-documento "12345678000190" --org org_123

# Criar cliente com CPF
python manage.py empresa criar-cliente --nome "João Silva" --tipo-documento cpf --numero-documento "12345678900" --org org_123

# Listar em formato JSON
python manage.py empresa criar-cliente --nome "Nova Empresa" --org org_123 --json
```

---

### Agendamentos de Recebimento

Lista agendamentos de recebimento (contas a receber).

**Sintaxe:**

```bash
python manage.py empresa agendamentos-receber [--org ID_OU_CODIGO] [--tipo TIPO] [--cliente CLIENTE] [--json]
```

**Parâmetros:**

- `--org` ou `--org`: ID ou código da organização (obrigatório)
- `--tipo`: Tipo de agendamentos ('abertos', 'vencidos', 'todos', padrão: 'abertos')
- `--cliente`: Nome do cliente para filtrar (opcional)

**Exemplos:**

```bash
# Listar agendamentos abertos
python manage.py empresa agendamentos-receber --org org_123

# Listar agendamentos vencidos
python manage.py empresa agendamentos-receber --tipo vencidos --org org_123

# Listar todos os agendamentos
python manage.py empresa agendamentos-receber --tipo todos --org org_123

# Filtrar por cliente
python manage.py empresa agendamentos-receber --cliente "Empresa" --org org_123

# Listar em formato JSON
python manage.py empresa agendamentos-receber --org org_123 --json
```

---

### Agendamentos de Pagamento

Lista agendamentos de pagamento (contas a pagar).

**Sintaxe:**

```bash
python manage.py empresa agendamentos-pagar [--org ID_OU_CODIGO] [--tipo TIPO] [--fornecedor FORNECEDOR] [--json]
```

**Parâmetros:**

- `--org` ou `--org`: ID ou código da organização (obrigatório)
- `--tipo`: Tipo de agendamentos ('abertos', 'vencidos', 'todos', padrão: 'abertos')
- `--fornecedor`: Nome do fornecedor para filtrar (opcional)

**Exemplos:**

```bash
# Listar agendamentos abertos
python manage.py empresa agendamentos-pagar --org org_123

# Listar agendamentos vencidos
python manage.py empresa agendamentos-pagar --tipo vencidos --org org_123

# Filtrar por fornecedor
python manage.py empresa agendamentos-pagar --fornecedor "Fornecedor" --org org_123

# Listar em formato JSON
python manage.py empresa agendamentos-pagar --org org_123 --json
```

---

### Criar Agendamento de Recebimento

Cria um novo agendamento de recebimento.

**Sintaxe:**

```bash
python manage.py empresa criar-agendamento-receber --cliente CLIENTE --categoria CATEGORIA --valor VALOR --data-agendamento DATA_AGENDAMENTO --data-vencimento DATA_VENCIMENTO --descricao DESCRICAO [--org ID_OU_CODIGO] [--referencia REFERENCIA] [--json]
```

**Parâmetros:**

- `--cliente` ou `-cli` (obrigatório): UUID do cliente
- `--categoria` ou `-cat` (obrigatório): UUID da categoria
- `--valor` (obrigatório): Valor do agendamento
- `--data-agendamento` (obrigatório): Data de agendamento (formato: DD/MM/YYYY)
- `--data-vencimento` (obrigatório): Data de vencimento (formato: DD/MM/YYYY)
- `--descricao` (obrigatório): Descrição do agendamento
- `--org` ou `--org`: ID ou código da organização (obrigatório)
- `--referencia`: Referência do agendamento (opcional)

**Exemplos:**

```bash
# Criar agendamento de recebimento
python manage.py empresa criar-agendamento-receber --cliente "uuid-cliente" --categoria "uuid-categoria" --valor 1000.00 --data-agendamento "01/01/2025" --data-vencimento "31/01/2025" --descricao "Recebimento de venda" --org org_123

# Com referência
python manage.py empresa criar-agendamento-receber --cliente "uuid-cliente" --categoria "uuid-categoria" --valor 1000.00 --data-agendamento "01/01/2025" --data-vencimento "31/01/2025" --descricao "Recebimento" --referencia "NF-001" --org org_123

# Listar em formato JSON
python manage.py empresa criar-agendamento-receber --cliente "uuid" --categoria "uuid" --valor 1000.00 --data-agendamento "01/01/2025" --data-vencimento "31/01/2025" --descricao "Recebimento" --org org_123 --json
```

---

### Criar Agendamento de Pagamento

Cria um novo agendamento de pagamento.

**Sintaxe:**

```bash
python manage.py empresa criar-agendamento-pagar --fornecedor FORNECEDOR --categoria CATEGORIA --valor VALOR --data-agendamento DATA_AGENDAMENTO --data-vencimento DATA_VENCIMENTO --descricao DESCRICAO [--org ID_OU_CODIGO] [--referencia REFERENCIA] [--json]
```

**Parâmetros:**

- `--fornecedor` ou `-for` (obrigatório): UUID do fornecedor
- `--categoria` ou `-cat` (obrigatório): UUID da categoria
- `--valor` (obrigatório): Valor do agendamento
- `--data-agendamento` (obrigatório): Data de agendamento (formato: DD/MM/YYYY)
- `--data-vencimento` (obrigatório): Data de vencimento (formato: DD/MM/YYYY)
- `--descricao` (obrigatório): Descrição do agendamento
- `--org` ou `--org`: ID ou código da organização (obrigatório)
- `--referencia`: Referência do agendamento (opcional)

**Exemplos:**

```bash
# Criar agendamento de pagamento
python manage.py empresa criar-agendamento-pagar --fornecedor "uuid-fornecedor" --categoria "uuid-categoria" --valor 500.00 --data-agendamento "01/01/2025" --data-vencimento "31/01/2025" --descricao "Pagamento de fornecedor" --org org_123

# Com referência
python manage.py empresa criar-agendamento-pagar --fornecedor "uuid-fornecedor" --categoria "uuid-categoria" --valor 500.00 --data-agendamento "01/01/2025" --data-vencimento "31/01/2025" --descricao "Pagamento" --referencia "NF-002" --org org_123

# Listar em formato JSON
python manage.py empresa criar-agendamento-pagar --fornecedor "uuid" --categoria "uuid" --valor 500.00 --data-agendamento "01/01/2025" --data-vencimento "31/01/2025" --descricao "Pagamento" --org org_123 --json
```

---

### Categorias

Lista categorias de agendamento.

**Sintaxe:**

```bash
python manage.py empresa categorias [--org ID_OU_CODIGO] [--json]
```

**Parâmetros:**

- `--org` ou `--org`: ID ou código da organização (obrigatório)

**Exemplos:**

```bash
# Listar todas as categorias
python manage.py empresa categorias --org org_123

# Listar em formato JSON
python manage.py empresa categorias --org org_123 --json
```

**Nota:** As categorias são usadas para classificar agendamentos de recebimento e pagamento. Cada categoria tem um tipo ('in' para receita, 'out' para despesa).

---

### Fornecedores

Lista fornecedores da empresa.

**Sintaxe:**

```bash
python manage.py empresa fornecedores [--org ID_OU_CODIGO] [--nome NOME] [--json]
```

**Parâmetros:**

- `--org` ou `--org`: ID ou código da organização (obrigatório)
- `--nome`: Nome do fornecedor para filtrar (busca parcial, opcional)

**Exemplos:**

```bash
# Listar todos os fornecedores
python manage.py empresa fornecedores --org org_123

# Filtrar por nome (busca parcial)
python manage.py empresa fornecedores --nome "Fornecedor" --org org_123

# Listar em formato JSON
python manage.py empresa fornecedores --nome "Fornecedor" --org org_123 --json
```

---

## Opções Globais

Todos os comandos suportam as seguintes opções globais:

### `--json`

Exibe o resultado em formato JSON ao invés do formato tabular padrão.

**Exemplo:**

```bash
python manage.py empresa clientes --json --org org_123
python manage.py obrigacoes clientes --json
```

### `--org` ou `--org` (CLI Empresa)

Especifica a organização a ser usada para autenticação. Pode ser o ID da organização (ex: `org_123`) ou um código simplificado definido no `settings.json` (ex: `empresa_principal`).

**Exemplo:**

```bash
# Usando ID da organização
python manage.py empresa clientes --org org_123

# Usando código simplificado
python manage.py empresa clientes --org empresa_principal

# Com outros parâmetros
python manage.py empresa clientes --org org_123 --nome "Empresa" --json
```

**Nota:** Este parâmetro é obrigatório para todos os comandos do CLI Empresa, exceto `organizacoes` (que usa o primeiro token disponível se não especificado).

### `--escritorio ESCRITORIO` ou `-e` (apenas CLI Obrigações)

Especifica o UUID do escritório contábil. Se não fornecido, usa o primeiro escritório disponível automaticamente.

**Exemplo:**

```bash
python manage.py obrigacoes clientes --escritorio "6ff5e102-0234-4c13-82c9-5b6c910b0a9e"
```

---

## Exemplos Práticos

### CLI Obrigações

#### Exemplo 1: Listar obrigações de um cliente específico

```bash
# Buscar obrigações do cliente "BR EMPRESA LTDA." no período atual
python manage.py obrigacoes obrigacoes --cliente "BR EMPRESA LTDA."
```

#### Exemplo 2: Listar tarefas de um usuário

```bash
# Listar tarefas não completas do usuário "Joao"
python manage.py obrigacoes tarefas --usuario-nome "Joao"
```

#### Exemplo 3: Criar uma nova tarefa

```bash
# Criar tarefa com descrição e deadline
python manage.py obrigacoes criar-tarefa --nome "Revisar documentos" --descricao "Revisar documentos do cliente" --deadline "2025-12-31"
```

#### Exemplo 4: Buscar clientes e suas obrigações

```bash
# 1. Listar clientes que contêm "BR" no nome
python manage.py obrigacoes clientes --nome "BR"

# 2. Listar obrigações de todos os clientes "BR"
python manage.py obrigacoes obrigacoes --cliente "BR"
```

#### Exemplo 5: Exportar dados em JSON

```bash
# Exportar lista de clientes em JSON
python manage.py obrigacoes clientes --json > clientes.json

# Exportar obrigações em JSON
python manage.py obrigacoes obrigacoes --cliente "BR" --json > obrigacoes.json
```

#### Exemplo 6: Filtrar tarefas por usuário e incluir completas

```bash
# Listar todas as tarefas (incluindo completas) do usuário "Joao"
python manage.py obrigacoes tarefas --usuario-nome "Joao" --incluir-completas
```

#### Exemplo 7: Criar e fazer upload de arquivo

```bash
# 1. Criar arquivo na API
python manage.py obrigacoes criar-arquivo --arquivo "etc/arquivo.pdf"

# O comando retorna:
# - ID do arquivo criado
# - sharedAccessSignature (URL temporária válida por 10 minutos)

# 2. Fazer upload usando a URL retornada
python manage.py obrigacoes upload-arquivo --arquivo "etc/arquivo.pdf" --shared-access-signature "https://..."

# Ou em um único fluxo (usando JSON):
# Criar arquivo e salvar resultado
python manage.py obrigacoes criar-arquivo --arquivo "etc/arquivo.pdf" --json > resultado.json

# Extrair sharedAccessSignature e fazer upload (Linux/Mac)
python manage.py obrigacoes upload-arquivo --arquivo "etc/arquivo.pdf" --shared-access-signature $(jq -r '.sharedAccessSignature' resultado.json)
```

### CLI Empresa

#### Exemplo 1: Criar cliente e agendar recebimento

```bash
# 1. Criar um novo cliente
python manage.py empresa criar-cliente --nome "Nova Empresa LTDA" --tipo-documento cnpj --numero-documento "12345678000190" --org org_123

# 2. Listar categorias para obter o ID
python manage.py empresa categorias --org org_123 --json

# 3. Criar agendamento de recebimento
python manage.py empresa criar-agendamento-receber --cliente "uuid-cliente" --categoria "uuid-categoria" --valor 1000.00 --data-agendamento "01/01/2025" --data-vencimento "31/01/2025" --descricao "Recebimento de venda" --org org_123
```

#### Exemplo 2: Listar agendamentos vencidos

```bash
# Listar recebimentos vencidos
python manage.py empresa agendamentos-receber --tipo vencidos --org org_123

# Listar pagamentos vencidos
python manage.py empresa agendamentos-pagar --tipo vencidos --org org_123
```

#### Exemplo 3: Filtrar agendamentos por cliente

```bash
# Listar agendamentos de recebimento de um cliente específico
python manage.py empresa agendamentos-receber --cliente "Empresa" --org org_123
```

#### Exemplo 4: Exportar dados em JSON

```bash
# Exportar lista de clientes em JSON
python manage.py empresa clientes --org org_123 --json > clientes_empresa.json

# Exportar agendamentos em JSON
python manage.py empresa agendamentos-receber --org org_123 --json > recebimentos.json
```

#### Exemplo 5: Criar agendamento de pagamento

```bash
# 1. Listar fornecedores
python manage.py empresa fornecedores --org org_123

# 2. Listar categorias
python manage.py empresa categorias --org org_123

# 3. Criar agendamento de pagamento
python manage.py empresa criar-agendamento-pagar --fornecedor "uuid-fornecedor" --categoria "uuid-categoria" --valor 500.00 --data-agendamento "01/01/2025" --data-vencimento "31/01/2025" --descricao "Pagamento de fornecedor" --referencia "NF-001" --org org_123
```

---

## Códigos de Saída

- **0**: Sucesso
- **1**: Erro na execução

---

## Tratamento de Erros

O CLI trata automaticamente os seguintes erros:

- **Erro de autenticação (401)**: Token inválido ou expirado
- **Recurso não encontrado (404)**: Endpoint ou recurso não existe
- **Erro de validação (400)**: Dados inválidos fornecidos
- **Limite de requisições (429)**: Muitas requisições em pouco tempo
- **Erro do servidor (5xx)**: Erro interno do servidor

---

## Dicas e Boas Práticas

1. **Use `--json` para integração**: Quando precisar processar os dados programaticamente, use `--json` para obter dados estruturados.
2. **Filtros parciais**: A maioria dos filtros por nome usa busca parcial. Use termos curtos para encontrar mais resultados.
3. **Períodos de datas**: O formato de data é `DD/MM/YYYY` para agendamentos e obrigações. O período padrão para obrigações é de hoje até o final do ano atual.
4. **IDs vs Nomes**: Você pode usar tanto UUID quanto nomes para identificar recursos. UUIDs são mais precisos, nomes são mais convenientes.
5. **Tarefas completas**: Por padrão, tarefas completas são excluídas. Use `--incluir-completas` se precisar vê-las.
6. **Categorias**: Antes de criar agendamentos, liste as categorias disponíveis para obter os IDs corretos.
7. **Agendamentos**: Use `--tipo vencidos` para identificar contas em atraso e `--tipo abertos` para contas pendentes.

---

## Suporte

Para mais informações sobre a API Nibo, consulte a documentação oficial:

- [Documentação Nibo](https://nibo.readme.io/)

Para problemas ou dúvidas sobre este CLI, verifique:

- Arquivo `README.md` do projeto
- Código-fonte em `nibo_api/obrigacoes/management/cli.py` e `nibo_api/empresa/management/cli.py`
- Testes em `tests/test_obrigacoes/` e `tests/test_empresa/`
