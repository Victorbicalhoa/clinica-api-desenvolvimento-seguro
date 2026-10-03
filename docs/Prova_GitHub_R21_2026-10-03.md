# Prova remota do security gate — 03/10/2026

A main foi aprovada no run [37095591151](https://github.com/Victorbicalhoa/clinica-api-desenvolvimento-seguro/actions/runs/37095591151), commit `99b980b35b4c8f7d847f9ac4de2a90250481c34b`: 226 testes aprovados, auditoria OpenAPI aprovada, ZAP passivo e gate aprovado.

O [PR #1](https://github.com/Victorbicalhoa/clinica-api-desenvolvimento-seguro/pull/1) adicionou exclusivamente um teste sentinela propositalmente reprovado. O run [37095705289](https://github.com/Victorbicalhoa/clinica-api-desenvolvimento-seguro/actions/runs/37095705289) apresentou 226 testes aprovados e uma falha, exclusivamente nessa sentinela; o gate reprovou.

A regra persistida para main foi reaberta no GitHub e conferida: PR obrigatório; status check security-gate de GitHub Actions; branch atualizada; administradores sem bypass; force push e exclusão desabilitados. No PR reprovado, o check estava marcado Required e o botão Merge pull request estava desabilitado. Capturas e snapshot DOM foram preservados localmente.

Este commit remove o teste sentinela e mantém este registro. A execução deste HEAD é a prova positiva após correção; consultar o check do PR antes de integrar. Não integrar sem aprovação do check obrigatório. A sentinela é um teste controlado, não um finding de vulnerabilidade real. Nenhuma proteção foi enfraquecida.

O gate aprovado permite integração do código avaliado; não substitui a avaliação dos riscos residuais do capstone nem autoriza produção.
