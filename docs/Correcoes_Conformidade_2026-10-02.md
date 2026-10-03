# Correções de conformidade — 02/10/2026

Este relatório registra as correções e a rodada de validação de 02/10. O [índice](README.md) apresenta os resultados posteriores. Os registros intermediários de revisão foram preservados localmente. Critérios: enunciados e 24 perguntas literais da rubrica. Conforme orientação do aluno, o repositório do professor é somente referência comparativa; Python 3.12 e diferenças de organização não constituem reprovação adicional. Não foi exigido copiar o starter ou implementar CRUD de pacientes não solicitado.

## Lacunas corrigidas

| Rubrica | Alteração | Evidência reproduzível |
|---|---|---|
| R12 / Ex7 | Client Credentials, scope, claims humano/máquina e disponibilidade mínima | `docs/exercicio_07.md`, `tests/test_exercicio07.py`, `m2m-evidence.json` |
| R14 / Ex8–9 | BOLA antes/depois em laboratório didático isolado, mesmo usuário e ID | `tests/test_lab_isolado.py`, `lab-before-after.json`: 200 com exposição → 404 |
| R16 / Ex2–9 | Stored XSS persistido; mesmo payload e dados nas duas renderizações | Laboratório: um elemento script antes; zero depois e texto escapado |
| R24 / Ex13 | Sucesso de criação/leitura com Session autospec, além dos testes integrados existentes | `tests/test_sucesso_mock.py`; mocks de entrada/autorização do Ex13 preservados |

O laboratório é **reconstruído**, não uma alegação de vulnerabilidade histórica na aplicação entregue. Existe somente em testes, sem aplicação global executável ou rotas montadas em `app`. A BOLA retira a política de ownership apenas nesse cenário isolado; a XSS usa Jinja2 sem autoescape somente nesse cenário. A aplicação real continua com política centralizada e autoescape. O payload `<script>alert("XSS-LAB")</script>` é persistido pela API real usando dados fictícios. A verificação analisa HTTP/HTML; não se afirma execução de JavaScript em navegador. Esse limite evita apresentar um parser como evidência visual.

## Atualização de dependência e triagem

O novo scan SCA encontrou PyJWT 2.14.0 afetado por **GHSA-42vr-xj54-vc7v / CVE-2026-101918**, corrigido em 2.15.0. CVSS 3.1 **5,3**, vetor `AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:L`; CWE-248. Impacto de negócio: falha de uma requisição pode prejudicar uma integração de agendamento em consumidores que leem payload não verificado. O aviso envolve parsing anterior à verificação, incluindo `verify_signature=False`/PyJWKClient. A API não usa esses caminhos como autorização; não se demonstrou bypass, queda de processo ou exploração da API atual. Ainda assim, a política bloqueia qualquer vulnerabilidade SCA reportada até correção.

Foi fixada a versão 2.15.0 e verificado o SHA-256 do wheel contra metadados oficiais PyPI. Evidências antes/depois: `pip-audit-before-upgrade.json`, `pip-audit.json`, `pyjwt-wheel.json`. [Aviso oficial do mantenedor](https://github.com/jpadilla/pyjwt/security/advisories/GHSA-42vr-xj54-vc7v).

Bandit identifica dois alertas B105 de severidade LOW para strings `token_use: human` e `token_use: machine`. São marcadores públicos de tipo de token, não senhas ou segredos. Triagem: falsos positivos, mantidos no relatório bruto e permitidos pela política de severidade; não foi usado `nosec` para escondê-los.

## Gate e rastreabilidade

O gate continua bloqueando falhas de testes obrigatórios, ferramentas/evidências ausentes, High/Critical, Medium sem triagem e qualquer vulnerabilidade SCA. Os testes M2M, laboratório e mock de sucesso foram adicionados aos testes obrigatórios. A presença de testes não equivale à eliminação de todo risco de uma ameaça.

TH-14 agora possui implementação e testes; TH-02/TH-07 ganham a prova comparativa; TH-09 ganha a atualização de dependência. A rastreabilidade atualizada está em `Exercicio_13_Rastreabilidade_2026-10-02.json`. A política de **NO-GO para produção** permanece: MFA real, TLS/proxy, backup/restauração, controle do banco e operação ainda precisam de validação. Isso é uma decisão justificada do capstone, não uma falha em responder ao enunciado.

## Resultado da rodada final

Evidências em `evidencias/conformidade_2026-10-02/`, com manifesto SHA-256:

| Verificação | Resultado observado |
|---|---|
| pytest | 226 aprovados; dois avisos de depreciação de dependências |
| Ruff e formatação | Aprovados |
| OpenAPI | 74 verificações aprovadas |
| pip-audit e pip check | Sem vulnerabilidades conhecidas reportadas; sem dependências quebradas |
| Bandit | Dois LOW B105, triados acima; nenhum Medium/High |
| ZAP 2.17.0 passivo | 12 respostas esperadas, fila esvaziada, dois informativos |
| actionlint | Exit 0 para o workflow |
| Security gate local | `passed=true`, sem bloqueios; quatro avisos preservados |

O SCA foi repetido após uma falha de rede; a falha não foi tratada como aprovação. O novo registro CVSS do PyJWT foi adicionalmente verificado pelo teste de recálculo do vetor.

| Finding final ZAP | Categoria/ameaça | Controle e decisão |
|---|---|---|
| 10109 — Modern Web Application, `/docs`, Informational | Inventário de superfície, sem vulnerabilidade OWASP confirmada | Swagger local sob CSP/SRI; esperado para interface JavaScript; não demanda remoção da interface |
| 10031 — User Controllable HTML Element Attribute, `/agenda`, Informational/Low confidence | Potencial injeção: A05:2025 / TH-07, não exploração confirmada | Data validada e autoescape Jinja2; teste de payload persistido e comparação do laboratório. Manter triagem e reavaliar se o template mudar |

Os achados históricos Medium de CSP/SRI do Ex12 permanecem correlacionados às correções no relatório do Ex13. Esta rodada amplia o corpus com disponibilidade M2M e as duas negações cruzadas, sem ampliar a afirmação para scan ativo, TLS, browser ou infraestrutura.

## Complemento posterior: execução no GitHub

Em 03/10/2026, o workflow foi executado no repositório próprio, a proteção de main foi verificada e o merge foi bloqueado na prova negativa e liberado após a correção. Consulte a [prova R21](Prova_GitHub_R21_2026-10-03.md), que complementa esta rodada local, e a [matriz atual](Matriz_Rubricas_AT_2026-10-03.csv).

Vídeo pessoal, link do YouTube não listado e ZIP final são requisitos separados. Produção permanece NO-GO conforme o capstone.
