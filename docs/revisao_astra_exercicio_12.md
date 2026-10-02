# Revisão independente Astra — Exercício 12

Revisor: agente `gpt-6-astra`, conforme solicitação do aluno. Data: 25/09/2026. Revisão somente leitura, sem execução própria de testes.

## Escopo

Workflow GitHub Actions, gate, orquestração dos scanners, obtenção do ZAP, política de severidade, registros CVSS, rastreabilidade TH, testes de autorização/gate e relatório técnico. Evidências finais examinadas em `work/ex12_evidence` antes da instalação na pasta do Assessment.

## Achado corrigido

A primeira revisão identificou que iniciar `run_checks` removia relatórios antigos de testes/SAST/SCA, mas mantinha `zap.json`. Uma falha antes de iniciar DAST poderia combinar checks novos e ZAP antigo em uma avaliação local. O workflow hospedado ainda ficaria vermelho pela falha do passo anterior, mas a garantia local de evidência atual ficava incompleta.

Foi incluída a remoção de `zap.json` e ampliado o teste que simula erro operacional para verificar que o relatório não é reutilizado. O gate também compara versões do inventário e status de cobertura com valores definidos no código, sem permitir que o próprio relatório redefina sucesso autenticado como 401.

## Parecer final

> Aprovado, sem bloqueadores técnicos.

O Astra confirmou a correção e conferiu: 175 testes aprovados, Bandit/SCA sem achados, ZAP real com nove respostas e sete alertas triados, gate aprovado e actionlint sem erros. Considerou adequadas as regressões de autorização, a política conservadora com triagens datadas, as premissas CVSS separadas do impacto de negócio e as permissões/pins do workflow.

O replay do SCA histórico está identificado como comparação, sem alegar execução integral da versão antiga. IAST não foi executado; DAST foi passivo; não houve execução hospedada no GitHub nem configuração de branch protection. A revisão não certifica produção nem encerra as pendências CSP/SRI, infraestrutura ou Ex7. Os resultados finais foram incorporados ao relatório após o parecer.
