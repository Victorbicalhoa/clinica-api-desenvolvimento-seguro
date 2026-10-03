# Documentação técnica

## Estado consolidado

API educacional de agendamento com autenticação, autorização por papel e recurso, integração M2M, validação, HTML seguro, hardening e persistência SQLModel. Use dados fictícios. Produção permanece **NO-GO** pelos riscos residuais documentados no capstone.

A execução positiva preservada registrou **226 testes aprovados**, **74 verificações OpenAPI**, ZAP passivo com **dois achados informativos** e gate aprovado. O PR de demonstração também registrou uma falha sentinela, seu bloqueio de merge e a aprovação após remoção. Números menores nos relatórios por exercício pertencem às etapas anteriores.

## Leitura principal

| Documento | Conteúdo |
|---|---|
| [Correções e validação consolidada](Correcoes_Conformidade_2026-10-02.md) | M2M, comparação BOLA/XSS, mocks, dependência corrigida e resultados |
| [Matriz das rubricas](Matriz_Rubricas_AT_2026-10-03.csv) | Requisito → implementação → evidência; não é uma nota ou aprovação do professor |
| [CIA e DFD](exercicio_03.md) | Ativos, dados sensíveis e fronteiras de confiança |
| [Threat model STRIDE](exercicio_04.md) | Misuse cases, ameaças e mitigações |
| [Arquitetura](exercicio_05.md) | Componentes, fluxos e eixos de segurança |
| [Pipeline e priorização](exercicio_12.md) | SDLC, CVSS, impacto de negócio e critério do gate |
| [Prova de bloqueio de merge](Prova_GitHub_R21_2026-10-03.md) | Regra persistida, execução negativa e positiva |
| [Capstone e riscos residuais](exercicio_13.md) | Findings, correções, auditoria OpenAPI e decisão de liberação |
| [Rastreabilidade atualizada](Exercicio_13_Rastreabilidade_2026-10-02.json) | Ameaça → controle → teste → evidência |
| [Roteiro final do vídeo](Roteiro_Final_Executavel_2026-10-03.md) | Preparação, comandos, cliques e sequência de até cinco minutos |
| [Metodologia e limites](metodologia.md) | Ferramentas utilizadas, assistência e alcance das evidências |

## Relatórios por exercício

1. [Fundação da API](exercicio_01.md)
2. [Contratos de saída e templates](exercicio_02.md)
3. [CIA, frameworks e DFD](exercicio_03.md)
4. [STRIDE e misuse cases](exercicio_04.md)
5. [Arquitetura e vetores](exercicio_05.md)
6. [Autenticação e autorização](exercicio_06.md)
7. [Escopos e integração M2M](exercicio_07.md)
8. [Identificação de vulnerabilidades](exercicio_08.md)
9. [Correções de entrada e saída](exercicio_09.md)
10. [Hardening e proteção contra abuso](exercicio_10.md)
11. [Persistência segura](exercicio_11.md)
12. [DevSecOps](exercicio_12.md)
13. [Auditoria final](exercicio_13.md)

Os relatórios preservam decisões e resultados da respectiva etapa. Para o estado atual, leia também os complementos consolidados acima. As revisões de trabalho, acompanhamentos e versões anteriores do roteiro/matriz ficam no arquivo local, fora da árvore atual do repositório.

## Evidências reproduzíveis

- [Rodada de conformidade](../evidencias/conformidade_2026-10-02/)
- [Relatórios reais do GitHub Actions](../evidencias/github_r21_2026-10-03/)
- [Capturas da API e proteção de merge](../evidencias/capturas_2026-10-03/)
- [Workflow](../.github/workflows/security.yml), [política do gate](../security/policy.json) e [registro de riscos](../security/risk-register.json)

O vídeo pessoal e seu link continuam requisitos próprios da entrega. O ZIP final será preparado separadamente.
