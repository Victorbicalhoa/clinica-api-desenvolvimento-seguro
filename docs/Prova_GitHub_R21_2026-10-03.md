# Encerramento da prova GitHub e preparação do vídeo — 03/10/2026

## Resultado

R21 atendida com revisão Astra. A matriz passa a 24/24 rubricas com evidências; isso não substitui a avaliação do professor nem conclui os requisitos pessoais de vídeo e envio.

| Prova | Referência | Resultado |
|---|---|---|
| Main inicial | [37095591151](https://github.com/Victorbicalhoa/clinica-api-desenvolvimento-seguro/actions/runs/37095591151), SHA `99b980b35b4c8f7d847f9ac4de2a90250481c34b` | 226 testes; gate aprovado |
| Negativa controlada | [37095705289](https://github.com/Victorbicalhoa/clinica-api-desenvolvimento-seguro/actions/runs/37095705289), SHA `7ea46644201376cc5a1b5fe25edb7d9667b7ef47` | 226 aprovados + uma falha exclusiva da sentinela; gate reprovado |
| Positiva após remoção | [37120246049](https://github.com/Victorbicalhoa/clinica-api-desenvolvimento-seguro/actions/runs/37120246049), SHA `22caf38475ebb5777727f1fff14e379956afec18` | Nova execução aprovada no HEAD corrigido do PR |

[PR #1](https://github.com/Victorbicalhoa/clinica-api-desenvolvimento-seguro/pull/1). A prova negativa usa um teste propositalmente falho, sem introduzir vulnerabilidade na API. O teste foi removido antes da prova positiva.

## Proteção efetivamente verificada

A regra salva para `main` foi reaberta no GitHub. Exige pull request, status check `security-gate` de GitHub Actions, branch atualizada e aplicação aos administradores (sem bypass). Force push e exclusão não estão autorizados. Por ser projeto individual, não foi imposto revisor externo inexistente.

No estado reprovado, o check estava **Required** e `Merge pull request` desabilitado. Após correção e nova execução aprovada, o botão ficou habilitado. Os arquivos `regra_main_observada.txt`, `pr_reprovado_observado.txt` e `pr_aprovado_observado.txt` preservam snapshots DOM; capturas 06, 07 e 14 preservam as telas reais. Não foi necessário tentar integrar código reprovado nem enfraquecer proteção.

## Evidências preservadas

Em `evidencias/github_r21_2026-10-03`, as pastas `aprovado`, `reprovado` e `pr-aprovado` contêm os artifacts reais: pytest, Bandit, pip-audit, OpenAPI, ZAP e gate. Os ZIPs originais são artifacts do Actions, não o ZIP final de entrega. SHA256 conferidos:

- main: `788d9353da105670ef567bee640564f0ec3d2158d0e0df3e4848c99080997dcb`;
- negativa: `d7d26ce66fc592a53696ade3d10fc17208a38d6acbfe74284bb5734d25c7e055`;
- positiva PR: `901a2825949f8a0c7c02378d2b172231b43106be036b91c92b686afbe3d90258`.

O scan passivo permaneceu com dois achados informativos e a auditoria OpenAPI com 74 verificações aprovadas. A política não confunde os dois LOW B105 triados no Bandit com vulnerabilidade confirmada de senha real.

As novas capturas 08–13 mostram respostas reais de Uvicorn no Swagger sem área de Authorization: leitura 200, criação 201, campo extra 422, administrador 403, recurso alheio 404 e disponibilidade M2M 200 com somente profissional/início. As imagens também podem incluir exemplos estáticos do Swagger abaixo da área Server response; somente a área superior registra a execução. A agenda 05 mostra payload fictício como texto. A nova criação foi ID 2; a leitura/ownership usam ID 1 do mesmo banco de ensaio. Dados são fictícios.

Capturas preliminares que incluíam Authorization de sessão efêmera foram rejeitadas e não integram o projeto/entrega/publicação. As substitutas foram refeitas no navegador, sem reconstrução de respostas ou edição generativa.

## Vídeo e liberação

Use `docs/Roteiro_Final_Executavel_2026-10-03.md`: preparação completa, comandos PowerShell, cliques Swagger, três terminais, cronograma 4min50s, falas e diagnóstico. Inicie até dois minutos após emitir o token M2M; renove a sessão da agenda se expirar. O aluno deve gravar pessoalmente e explicar o gate e as decisões residuais com suas próprias palavras.

Ainda faltam o vídeo de até cinco minutos no YouTube não listado, seu link e o ZIP final `Hebert_almeida_DR2_AT.ZIP`. A decisão de produção continua **NO-GO** conforme capstone: êxito do gate não elimina dependências operacionais e de infraestrutura. O repositório do professor foi usado somente para comparação.
