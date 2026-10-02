# Inspeção final do AT — Desenvolvimento Seguro de Aplicações Web

**Aluno:** Hebert Almeida · **Inspeção:** 30/09/2026 · **Projeto:** `C:\Dev\Infnet\Desenvolvimento Seguro de Aplicações Web\Assessment`.

## Parecer

**A aplicação está alinhada à stack e implementa a maior parte dos controles exigidos, mas os 13 exercícios não estão integralmente concluídos.** O Exercício 7 está ausente da aplicação instalada. Há também diferenças em relação ao material do professor e lacunas de comprovação acadêmica que devem ser resolvidas antes de apresentar a entrega como completa.

A validação atual passou: **190 testes, 65 verificações OpenAPI, Ruff, formatação, Bandit, pip-audit e security gate**. O ZAP passivo real voltou a observar nove respostas e dois alertas informativos. Esses resultados comprovam os cenários cobertos, não os requisitos ausentes. A revisão independente do **Astra** confirmou essa distinção.

Esta inspeção preservou o código, as configurações e os bancos da aplicação. Os testes foram executados em cópia isolada e o ensaio HTTP usou banco e contas fictícios próprios. Não houve publicação em GitHub, alteração de permissões remotas ou criação de ZIP. O usuário confirmou que o AT existe somente localmente.

## 1. Fontes e critério de avaliação

Foram comparados: os 13 enunciados e o formato de entrega fornecidos pelo usuário; as **24 perguntas** de `docs/rubrica_original.txt`; código, testes e evidências do projeto; e o repositório público indicado pelo professor.

O repositório foi obtido em 30/09/2026, no commit **`2b0a2060d11092850a702cda2469f6f8c123381d`**. A comparação usa esse snapshot, evitando que alterações posteriores mudem silenciosamente a referência. O [README principal](https://github.com/fabiano-domingues-prof-infnet-edu-br/desenvolvimento-seguro/blob/2b0a2060d11092850a702cda2469f6f8c123381d/README.md) encaminha o Assessment para `clinica-api-assessment`.

Ordem adotada: requisito explícito do enunciado/rúbrica prevalece sobre comportamento conflitante de um exemplo didático. Uma exigência expressa no README é registrada como divergência, mesmo quando nosso código funciona. Sem esclarecimento do professor, não se presume que nomes de rotas, versões antigas de bibliotecas ou todas as decisões do starter sejam obrigatórios.

Classificações: **atendido** significa evidência técnica suficiente no escopo inspecionado; **parcial** significa controle presente com requisito ou comprovação faltante; **não atendido** significa requisito ausente. A matriz é parecer técnico, não nota ou garantia de aprovação pelo professor.

## 2. O que foi executado nesta inspeção

| Verificação | Resultado em 30/09/2026 | Alcance |
|---|---|---|
| Snapshot e hashes | 71 arquivos de implementação/configuração copiados e conferidos | Nenhum `.env` real ou banco copiado |
| Python | 3.12.14 | Diverge do README do starter; 3.11 não foi testado |
| pytest | **190 passed**, 2 warnings, 243,90 segundos | Nenhum teste novo da aplicação foi acrescentado nesta inspeção |
| Ruff / format | aprovados; 49 arquivos Python formatados | Estilo e verificações estáticas básicas |
| Bandit | zero findings/erros | Código `app`; não equivale a análise de negócio completa |
| pip-audit | zero vulnerabilidades conhecidas retornadas | Dependências Python fixadas; não cobre automaticamente JS vendorizado |
| pip check | aprovado | Compatibilidade declarada das dependências instaladas |
| OpenAPI | **65 verificações aprovadas** | Auditoria estrutural e contratual |
| ZAP 2.17.0 | 9 respostas; fila passiva zero; 2 informativos | Corpus autenticado finito, sem active scan/spider/TLS real |
| Security gate | aprovado; sem exceções Medium | Execução local, sem comprovação de bloqueio de merge |
| actionlint | aprovado | Sintaxe/estrutura do workflow, não execução GitHub |
| Ensaio do vídeo em HTTP real | 201/200, 404, 403, 422 e agenda 200 com escape | API em processo Uvicorn, loopback, contas fictícias |
| Navegador | indisponível: `Browser is not available: iab` | Nenhum print novo nem validação visual do Swagger produzidos |

Os relatórios da inspeção estão em `evidencias/inspecao_final_2026-09-30/`. Resultados anteriores de 25/09 foram preservados. Os warnings do pytest são depreciações de dependências; não foram contados como vulnerabilidades. As versões e o resultado SCA devem ser novamente verificados depois de qualquer alteração de runtime ou dependência.

Os 97 arquivos do manifesto do Ex13 continuaram com hashes correspondentes, sem diferenças. A busca textual limitada por formatos comuns de chave privada, token GitHub e chave AWS não encontrou ocorrências nos 71 arquivos selecionados; não havia `.env` na raiz. Isso não substitui um scanner completo de segredos nem autoriza incluir bancos, caches ou ambientes no ZIP. O registro está em `higiene-entrega.json`.

## 3. Comparação com o repositório do professor

| Aspecto | Referência do professor | Nosso projeto | Parecer |
|---|---|---|---|
| Organização | `routes`, `models`, `database`, `auth` | Mesmos módulos sob `app/`, mais `core`, templates, testes e scripts | **Alinhado.** Subdiretório `app/` e nomes em português não prejudicam o objetivo modular |
| Framework/persistência | FastAPI, SQLModel e SQLite | FastAPI, SQLModel, SQLite persistente e SessionDep | **Alinhado.** SQLite é banco relacional real |
| Python | README exige 3.10 ou 3.11 | Ambiente e workflow usam 3.12; Ruff `py312` | **Divergência expressa.** Priorizar validação em 3.11; não declarar compatibilidade sem executar |
| Dependências | Pydantic 1, Passlib/bcrypt e python-jose antigos | Pydantic 2, bcrypt direto, PyJWT e versões fixadas atualizadas | **Adaptação justificável**, mantendo os requisitos de comportamento. Não copiar versões antigas sem análise |
| Rotas REST | `/appointment/new` e listagem `/appointment/` | CRUD completo em `/consultas`, GET/POST/PUT/DELETE | **Alinhado ao enunciado.** Não há exigência de manter os nomes ingleses |
| Papéis para criação | Starter permite admin/recepção e nega profissional | Somente profissional vinculado cria/gerencia consultas | **Conflito do material.** Nossa política segue o texto explícito do Exercício 6 e deve ser justificada |
| Modelo de pacientes | `Patient` com cadastro; Appointment declara FKs para paciente/usuário | IDs de paciente e profissional, Usuario e VinculoPaciente; sem entidade Patient/cadastro | **Simplificação funcional relevante.** Não há comprovação de existência do paciente em cadastro mestre. A rubrica não exige nominalmente CRUD de Patient, mas o contexto tem três recursos centrais |
| RBAC e ownership | RoleChecker; listagem de consultas sem filtro por dono | Papel mais predicado central por profissional/vínculo | Nossa proteção por recurso atende melhor ao Exercício 6; preservar |
| Cadastro de usuários | Signup recebe modelo User | Provisionamento local sem signup público livre | Decisão justificável para evitar autoatribuição de papel; explicar no vídeo |
| JWT e configuração | Chave didática fixa e expiração manual | Segredo configurável/efêmero, claims padrão e sessão revogável | Proteções adicionais coerentes; não copiar a chave do exemplo |
| SAST/SCA | Exemplos Bandit e Trivy | Bandit, pip-audit, testes, OpenAPI e ZAP | Ferramentas podem variar; o enunciado pede escolha e justificativa do gate |
| Keycloak/OpenID | Exemplo de login humano com OIDC/PKCE | OAuth password humano próprio | Não exige Keycloak por si só; o exemplo não substitui M2M/client credentials do Ex7 |

Fontes específicas: [README do starter](https://github.com/fabiano-domingues-prof-infnet-edu-br/desenvolvimento-seguro/blob/2b0a2060d11092850a702cda2469f6f8c123381d/clinica-api-assessment/README.md), [rotas de consultas](https://github.com/fabiano-domingues-prof-infnet-edu-br/desenvolvimento-seguro/blob/2b0a2060d11092850a702cda2469f6f8c123381d/clinica-api-assessment/routes/appointments.py), [modelos](https://github.com/fabiano-domingues-prof-infnet-edu-br/desenvolvimento-seguro/blob/2b0a2060d11092850a702cda2469f6f8c123381d/clinica-api-assessment/models/appointments.py), [testes do starter](https://github.com/fabiano-domingues-prof-infnet-edu-br/desenvolvimento-seguro/blob/2b0a2060d11092850a702cda2469f6f8c123381d/clinica-api-assessment/tests/test_appointments.py), [exemplo SCA](https://github.com/fabiano-domingues-prof-infnet-edu-br/desenvolvimento-seguro/blob/2b0a2060d11092850a702cda2469f6f8c123381d/github-actions/sca/.github/workflows/security-gate-sca.yaml) e [exemplo OIDC](https://github.com/fabiano-domingues-prof-infnet-edu-br/desenvolvimento-seguro/blob/2b0a2060d11092850a702cda2469f6f8c123381d/openid-oauth2-keycloak/main.py).

O starter é material de partida, não um padrão final de segurança. A presença de chave didática fixa, listagem sem ownership e modelo User aceito diretamente no signup não autoriza reproduzir essas decisões na entrega final. Tampouco o teste do starter que verifica apenas “diferente de 403” demonstra criação bem-sucedida; nossos testes exigem os códigos e efeitos esperados.

## 4. Situação dos 13 exercícios

| Ex. | Situação | Evidência principal e ressalva |
|---|---|---|
| 1 | Atendido tecnicamente | `.venv`, APIRouter modular, CRUD e `tests/test_consultas.py`. Alinhar versão Python com README e obter prints |
| 2 | Atendido | ConsultaRead/response_model; `base.html`, `agenda.html`, autoescape e testes de exposição/XSS |
| 3 | Atendido | `docs/exercicio_03.md`, DFD PNG/Mermaid e controles CIA/OWASP/NIST/MITRE. É análise histórica, não descrição de todos os controles atuais |
| 4 | Atendido | Threat model com 14 ameaças, 10 misuse cases e quatro componentes STRIDE |
| 5 | Atendido | Oito partições, fluxos/fronteiras e 12 vetores nos três eixos; arquitetura histórica preservada |
| 6 | Atendido | bcrypt, OAuth2PasswordBearer, JWT, ownership, RBAC, MFA simulado e teste administrativo |
| 7 | **Não atendido** | Sem client credentials, escopos/claims M2M ou acesso do laboratório a disponibilidade |
| 8 | **Parcial** | Três categorias analisadas; BOLA é reconstrução didática, não instância vulnerável executada da aplicação |
| 9 | **Parcial na comprovação** | Controles e endpoint adicional existem; BOLA 404→404 e XSS escapado→escapado comprovam regressão, não exploração antes/correção depois |
| 10 | Atendido | CORS explícito, headers e limites diferenciados. HSTS testado por contexto HTTPS; TLS real não é evidência local |
| 11 | Atendido no estado final | SQLModel/SQLite, DI, BaseSettings e parametrização demonstrados. Persistência foi adotada antecipadamente, não houve migração tardia de dicionário em memória |
| 12 | **Parcial na rúbrica de merge** | Workflow, gate, CVSS e testes existem e passam. Falta execução GitHub e check obrigatório impedindo merge |
| 13 | **Parcial na leitura estrita da rúbrica** | ZAP real, rastreabilidade, OpenAPI e mocks existem; falta mock específico do sucesso inicial do Ex1. Prints/verificação visual continuam pendentes |

O detalhamento literal das 24 rúbricas está em `Matriz_Rubricas_AT_2026-09-30.csv`: **19 com evidência suficiente, quatro parciais e uma não atendida**, sob o critério descrito. Essa contagem não é nota e não inclui requisitos gerais de vídeo/ZIP como novas perguntas da rúbrica.

## 5. Achados prioritários e como encerrá-los

### A-01 — Exercício 7 ausente: prioridade alta

Evidência: `app/models/entrada.py` aceita somente `grant_type='password'` e scope vazio; `app/auth/security.py` usa audiência humana; `app/core/openapi.py` declara que M2M não existe. Não se trata apenas de um relatório desatualizado. O rascunho externo `work/ex7` não faz parte da entrega e não foi considerado implementação concluída.

Encerramento: implementar client credentials para cliente confidencial do laboratório, segredo protegido, escopo mínimo de disponibilidade e claims que distingam cliente de usuário. O laboratório deve consultar horários sem receber pacientes/observações. Testar scope ausente, token humano na rota M2M, token M2M em consultas/admin, expiração e cliente inválido. Atualizar OpenAPI, threat model, relatório, roteiro, scans e revisão Astra.

### A-02 — Runtime diferente do exigido pelo starter: prioridade média

Evidência: README oficial `clinica-api-assessment/README.md:21`; `.github/workflows/security.yml` define Python 3.12 e `pyproject.toml` usa `py312`. Os 190 testes em 3.12 não comprovam 3.11. O código utiliza recursos como `StrEnum`/`datetime.UTC`, disponíveis em 3.11, portanto 3.11 é o candidato mais direto.

Encerramento: criar ambiente **separado** Python 3.11, validar instalação e suíte/scanners, ajustar versões apenas se necessário e então alinhar README, workflow e alvo Ruff. Alternativamente obter aceite explícito do professor para 3.12. Não substituir o ambiente validado às cegas, nem copiar todas as dependências antigas do starter.

### A-03 — Gate local sem bloqueio efetivo de merge: prioridade alta de comprovação

Evidência: o usuário confirmou projeto somente local; `docs/exercicio_12.md` também registra ausência de run remoto e proteção de branch. O gate retorna falha para resultados bloqueantes, mas um YAML sozinho não torna esse status obrigatório para merge.

Encerramento: publicar em repositório próprio após revisar segredos, executar Actions e configurar proteção/ruleset para exigir o check **security-gate**, com política de bypass coerente. Produzir um PR de prova que falhe por controle obrigatório, mostrar o merge impedido, corrigir e mostrar aprovação. Não introduzir uma vulnerabilidade na branch principal para demonstrar. [Documentação oficial de checks obrigatórios](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).

### A-04 — BOLA/XSS antes e depois insuficientemente demonstrados: prioridade moderada/alta

Evidência: `docs/exercicio_08.md` qualifica BOLA como exemplo didático. `docs/exercicio_09.md` e sua comparação registram negação/escape antes e depois. Os controles atuais são válidos; a lacuna é a comprovação pedida pela narrativa e pelas rúbricas 14/16.

Encerramento recomendado: adicionar laboratório de teste isolado, explicitamente reconstruído para fins didáticos, com dados falsos e sem rota vulnerável montada na aplicação final. Executar o **mesmo** identificador/payload contra baseline vulnerável e controle corrigido; salvar resultado, código comparado e teste. Não reescrever a história dizendo que esse defeito esteve na versão entregue, nem tratar 404→404 como correção executada.

### A-05 — Mock do caminho de sucesso inicial: prioridade média

Evidência: `tests/test_consultas.py` cobre criação/busca usando SQLite em memória; `tests/test_exercicio13.py` possui mocks de entrada e negações de autorização, mas não um teste mockado do sucesso do Ex1. A tarefa do Ex13 está bem coberta; a última rúbrica é mais específica ao mencionar o teste inicial.

Encerramento: acrescentar teste unitário com Session autospec/fixture de usuário autorizado para criação e leitura bem-sucedidas, verificando contrato e chamadas relevantes. Preservar o teste integrado, porque mock não prova SQL ou transação. Reexecutar a suíte e atualizar sua contagem.

### A-06 — Evidências de apresentação e pacote: prioridade alta para entrega

Faltam prints reais da aplicação, vídeo pessoal com até cinco minutos e link não listado, além do ZIP final. O navegador da sessão de inspeção não está disponível; não se inventaram capturas. O roteiro detalhado e o cliente de ensaio foram preparados, mas não substituem a gravação do aluno.

Encerramento: verificar Swagger/agenda manualmente, capturar evidências sem credenciais, gravar e publicar o vídeo, testar acesso ao link e só então compactar a lista revisada de arquivos em `Hebert_almeida_DR2_AT.ZIP`. `.gitignore` não filtra compactação automaticamente.

### A-07 — Cadastro/integridade de pacientes simplificados: prioridade de alinhamento

O projeto não possui entidade Patient nem FK de Consulta para cadastro de pacientes. VinculoPaciente restringe quem pode operar determinado ID, mas não comprova sua existência em um cadastro mestre. O starter possui esse modelo; o contexto menciona pacientes, profissionais e consultas como recursos centrais.

A rubrica não exige nominalmente um CRUD completo de pacientes, por isso o achado não foi classificado como reprovação certa. Recomenda-se modelar o cadastro e a integridade referencial, ou documentar claramente essa limitação e confirmar o escopo. Não afirmar no vídeo que o sistema gerencia cadastro completo de pacientes/profissionais.

## 6. Pontos que estão corretos e devem ser preservados

- Políticas centralizadas por papel e recurso, com consultas parametrizadas e vínculos verificados no banco.
- Pydantic com contratos explícitos, tipos/limites e rejeição de campos extras; auditoria interna não exposta.
- Jinja2 com herança e escape contextual; recepção não recebe observação clínica no contexto HTML.
- Hash bcrypt, expiração/revogação de sessão, claims validados e MFA simulado opt-in.
- CORS sem wildcard, headers externos e quotas persistidas diferenciadas; logout continua acessível após esgotamento da quota geral.
- Auditoria transacional, conflitos de agenda e transições conforme regra aprovada pelo usuário.
- ZAP real com limites declarados, triagem dos informativos e rastreabilidade sem alegação de “zero risco”.
- Dependências fixadas e correção documentada do python-multipart; evidências históricas preservadas.

As diferenças de nomes/organização ou de biblioteca JWT não justificam desfazer esses controles para copiar o starter.

## 7. Riscos acadêmicos versus riscos de produção

**Acadêmicos/entrega:** M2M ausente, Python divergente do README, demonstração de merge, antes/depois BOLA/XSS, mock específico, prints/vídeo/ZIP e esclarecimento de modelagem de pacientes.

**Operacionais:** MFA real, TLS/proxy, proteção/backup/restauração do banco, SIEM/retenção, volume/conexões lentas, semântica de revogação concorrente e monitoração de assets vendorizados. Esses riscos sustentam o NO-GO de produção, mas não devem ser transformados automaticamente em requisitos acadêmicos não pedidos.

Em particular: **MFA simulado atende ao Exercício 6**; **IAST explicado e posicionado no SDLC atende ao tipo de justificativa exigido pelo Ex12**, sem autorizar afirmar que foi executado. **Decidir bloquear produção por risco residual é uma resposta válida e expressamente permitida pelo Exercício 13.**

## 8. Decisão e ordem recomendada

**Não apresentar ainda a entrega como “13 exercícios finalizados sem pendências”.** Prioridade: concluir Ex7; alinhar Python; fechar as demonstrações BOLA/XSS e mock; publicar/validar gate obrigatório; atualizar a auditoria final; obter prints e gravar o vídeo; revisar e gerar ZIP.

É possível ensaiar agora com o roteiro e o cliente HTTP, mas as falas e números devem ser atualizados após as correções. O roteiro distingue explicitamente afirmações comprovadas de afirmações condicionadas a trabalho futuro. Nenhum trecho orienta ocultar uma pendência ou atribuir ao aluno evidência inexistente.

Parecer Astra e evidências acompanham este relatório. O histórico de aprovações dos exercícios refere-se à incorporação e ao escopo local documentados em cada etapa; não equivale a aceite do professor nem a autorização de produção.
