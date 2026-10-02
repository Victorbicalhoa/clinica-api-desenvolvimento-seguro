# Revisão Astra — Exercício 6

**Data:** 22/09/2026. **Revisor:** agente astra_exercicio2, modelo gpt-6-astra, reutilizado para esta etapa.

Escopo: implementação OAuth2PasswordBearer/bcrypt/JWT/MFA, RBAC e ownership, agenda, provisionamento, testes e relatório. Revisão independente somente leitura; o agente não editou os arquivos nem executou novamente os testes.

## Achados e resolução

1. A fábrica da aplicação ignorava database_url de Settings injetado quando não recebia engine. Corrigido: build_engine e app.state compartilham a mesma instância. Teste de fábrica com configuração isolada em memória aprovado.
2. O flush do provisionamento estava fora do tratamento de IntegrityError. Corrigido: inserção, flush, vínculos e commit estão no mesmo bloco com rollback. Teste de profissional duplicado confirma erro amigável, sem traceback nem hash.
3. Limite MFA de cinco tentativas é por desafio, não global. Limitação documentada explicitamente; login e emissão de desafios ainda precisam de rate limiting futuro.
4. Recomendado teste concorrente de confirmação MFA. Implementado com SQLite descartável e duas threads: um 200, um 401, uma única sessão criada.

## Parecer final

**Exercício 6 aprovado no escopo definido, sem pendências desta revisão.** O revisor conferiu nos registros 70 testes aprovados e mais um teste concorrente separado, Ruff, formatação e pip check aprovados, além de 20 cenários HTTP sanitizados.

A aprovação preserva as limitações do relatório, sobretudo MFA simulado, ausência de rate limiting global e controles de implantação ainda futuros. Não equivale a certificação para uso em produção com dados reais de saúde.
