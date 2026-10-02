# Revisão independente — Exercício 10

Revisor: agente Astra (`gpt-6-astra`), solicitado pelo aluno. Data: 25/09/2026.

Escopo: configuração CORS, pilha ASGI, cabeçalhos, orçamentos de requisições, testes, relatório e evidências. Revisão somente leitura; o revisor conferiu os resultados existentes, sem executar novamente a suíte.

## Achado e resolução

Na primeira leitura, a quota geral também impediria logout após esgotamento. A implementação foi corrigida para isentar POST /auth/logout dessa quota, preservando autenticação, auditoria e revogação. Teste comprova esgotamento → logout 204 → token rejeitado com 401.

Também foi incluído teste de duas sessões do mesmo usuário: obter outro token não reinicia o orçamento por ID de usuário. A janela seguinte volta a permitir acesso.

## Parecer final

> Exercício 10 aprovado, sem bloqueadores desta revisão.

O Astra confirmou a correção do logout, a cobertura de quota entre sessões, 114 testes aprovados com dois avisos, Ruff aprovado e 37 arquivos com formatação aprovada. Considerou adequada a posição externa das camadas de CORS e cabeçalhos, incluindo erros do ServerErrorMiddleware. O relatório distingue CORS de autorização e teste do esquema HTTPS de implantação TLS real.

A aprovação refere-se ao código e às evidências desta etapa; não certifica implantação em produção, TLS real, proteção volumétrica ou conclusão dos exercícios pendentes.
