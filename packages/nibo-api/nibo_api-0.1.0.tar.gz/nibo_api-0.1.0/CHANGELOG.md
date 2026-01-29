# Changelog

Todas as mudanças notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/),
e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [1.0.0] - 2025-01-24

### Adicionado
- Cliente Python completo para API Nibo Empresa
- Cliente Python completo para API Nibo Obrigações
- Sistema de configuração flexível (settings.json, variáveis de ambiente, tokens criptografados)
- CLI unificado para interagir com ambas as APIs
- Suporte a múltiplas organizações na API Empresa
- Suporte completo a filtros OData
- Tratamento de erros com exceções customizadas
- Documentação completa (README.md e MANUAL_CLI.md)
- Scripts de console para uso via terminal
- Aliases curtos para parâmetros e comandos CLI
- Empacotamento Python (pyproject.toml)
- Testes automatizados
- GitHub Actions para CI/CD

### Módulos Implementados

#### Nibo Empresa
- Contatos (Clientes, Fornecedores, Funcionários, Sócios)
- Categorias
- Agendamentos (Recebimentos, Pagamentos)
- Centro de Custo
- Organizações
- Contas & Extratos
- Conciliação
- Parcelamentos
- Arquivos
- Nota Fiscal
- Relatórios
- Cobranças

#### Nibo Obrigações
- Escritórios
- Usuários
- Arquivos e Conferência
- Contatos
- Clientes
- CNAEs
- Grupos de Clientes (Tags)
- Departamentos
- Tarefas e Templates
- Responsabilidades
- Relatórios de Obrigações

[1.0.0]: https://github.com/ismaelnjr/nibo-api/releases/tag/v1.0.0
