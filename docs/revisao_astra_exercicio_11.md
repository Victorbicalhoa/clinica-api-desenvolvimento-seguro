# Revisão Astra — Exercício 11

Revisor independente: agente `gpt-6-astra`, conforme solicitação do aluno. Data: 25/09/2026. Revisão somente leitura, sem execução própria de testes.

## Escopo

Camada database, configuração BaseSettings, centralização de SessionDep, consumo nas rotas, queries, testes de persistência e relatório técnico. A revisão reconhece que SQLModel e SQLite em arquivo já existiam; a entrega consolida e comprova esses controles.

## Achado corrigido

O teste que carregava `.env` temporário ainda aceitava precedência de DATABASE_URL e JWT_SECRET do ambiente. Isso poderia direcionar o teste a outro banco ou mudar a premissa da chave JWT efêmera. Foi adicionada fixture que remove, durante os testes desta etapa, variáveis correspondentes aos campos de Settings. Os testes também verificam o caminho do engine antes de inserir dados.

Uma execução com DATABASE_URL e JWT_SECRET fictícios exportados confirmou os 13 casos novos aprovados, sem criar o banco sentinela externo ao teste. A mudança de diretório usa contexto restrito, restaurado antes da limpeza de arquivos temporários.

## Parecer

> Código e relatório aprovados, sem outros bloqueadores identificados.

O revisor conferiu o isolamento corrigido e o log dos 13 testes, com dois avisos preexistentes. A execução final da suíte completa foi deixada para o agente principal e seu resultado consta de `evidencias/exercicio_11/pytest.txt` e `checks.json`. A aprovação não afirma suporte a outro SGBD, migração de esquema ou prontidão operacional de produção.
