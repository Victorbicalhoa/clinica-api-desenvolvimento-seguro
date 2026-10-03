> Registro técnico da etapa indicada. Para resultados atuais e alterações posteriores, consulte o [índice de documentação](README.md).

# Exercício 13 — Capstone: auditoria e rastreabilidade

**Aluno:** Hebert Almeida · **Data:** 25/09/2026 · **Aplicação:** API de agendamento de clínicas, FastAPI/SQLModel/SQLite.

**Conclusão:** os controles implementados passaram na validação local; **deploy em produção bloqueado (NO-GO)** pelos riscos e requisitos pendentes descritos ao final. O resultado autoriza somente demonstração em loopback com dados fictícios. Este relatório não declara conformidade integral com a LGPD nem conclusão de todo o Assessment: o Exercício 7 continua pendente.

## 1. Escopo e evidências

Foi auditada a aplicação consolidada dos Exercícios 1–6 e 8–12, com as correções deste capstone. O threat model original `docs/Exercicio_04_Threat_Model.json` foi preservado; o estado atual está no adendo `docs/Exercicio_13_Rastreabilidade.json`, que relaciona cada TH aos IDs originais de misuse cases, mitigações e verificações, arquivos, testes, evidências e riscos residuais.

As evidências curadas estão em `evidencias/exercicio_13/`: JUnit, resultados de Ruff, Bandit e pip-audit, saída sanitizada do ZAP, contrato OpenAPI, auditoria estrutural, gate, consulta OSV do Swagger, comparação antes/depois e manifesto SHA-256. O scan utiliza contas, consultas e banco descartáveis inteiramente fictícios. Tokens, senhas, cookies, OTP e mensagens HTTP brutas do proxy não integram a saída do ZAP. Os resultados do Exercício 12 são evidências históricas, não foram sobrescritos.

| Verificação executada | Resultado observado |
|---|---|
| pytest completo | 190 aprovados, zero falhas/erros/skip; 15 casos novos do capstone |
| Regressões do gate após ampliar a lista obrigatória | 39 aprovadas novamente |
| Ruff e formatação | aprovados; 49 arquivos Python |
| Bandit sobre `app`, incluindo ocorrências com `nosec` | zero findings, zero erros |
| pip-audit sobre inventário Python fixado | zero vulnerabilidades conhecidas retornadas |
| OSV, consulta adicional `npm/swagger-ui-dist@5.33.0` | zero advisories retornados na consulta desta data |
| Auditoria OpenAPI | 65 verificações estruturais aprovadas |
| OWASP ZAP 2.17.0 passivo | 9 respostas verificadas, fila zerada, 2 alertas informativos |
| Gate final | aprovado, sem exceções Medium configuradas |
| Workflow GitHub Actions | validado localmente com actionlint; execução remota não realizada |

A primeira rodada encontrou uma linha acima do limite do Ruff, corrigida antes da nova verificação. O pip-audit inicialmente falhou por rede restrita, sem produzir evidência válida; após a liberação de rede, foi executado novamente com sucesso. Os códigos finais representam essas execuções reais. Os dois avisos de depreciação de dependências no pytest não são falhas de segurança, mas exigem manutenção futura. O pip-audit recomenda hashes completos das dependências: o inventário atual fixa versões, sem hashes de todos os wheels.

## 2. Consolidação da aplicação e decisões

A API mantém `routes`, `models`, `database`, `auth` e `core` separados. APIRouter publica os recursos; SQLModel e `SessionDep` centralizam persistência e sessões; queries de dados usam parâmetros. `BaseSettings` lê a configuração, `SecretStr` mascara os valores sensíveis e somente `.env.example` sem segredos deve acompanhar a entrega. SQLite é relacional e persistente; outros dialetos são rejeitados explicitamente nesta versão.

JWT é validado em middleware central, com algoritmo, emissor, audiência, expiração e sessão persistida. bcrypt protege senhas. RBAC limita ações por papel; políticas por recurso restringem profissionais e vínculos de pacientes. O administrador não recebe permissão clínica implícita. MFA é simulado e opt-in, adequado ao exercício, não a produção. O cookie HttpOnly/SameSite/Secure tem escopo de leitura da agenda; logout revoga a sessão. O papel efetivo vem do banco, não de um campo arbitrário no token.

Entrada usa whitelist, regex, limites e `extra='forbid'`; formulários rejeitam duplicatas e campos extras. Response models excluem auditoria interna. Jinja2 usa herança e autoescape, sem `safe` aplicado a conteúdo do usuário. CORS possui origens explícitas; limites de login são distintos da quota dos recursos. HSTS é emitido em contexto HTTPS, junto a X-Frame-Options e X-Content-Type-Options. O teste de HSTS em TestClient não comprova uma conexão TLS real.

Neste capstone foram acrescentados:

- **CSP central:** `default-src 'none'`, scripts/estilos/conexões na própria origem, sem `unsafe-inline` ou `unsafe-eval`, `frame-ancestors 'none'`, `object-src 'none'` e `base-uri 'none'`. A camada externa cobre também erros e respostas CORS.
- **Swagger local com integridade:** bundle e CSS 5.33.0 provenientes do registro oficial npm, tarball verificado por SHA-512, arquivos inventariados em `security/vendor-assets.json` e atributos SRI SHA-384 no HTML. LICENSE/NOTICE foram preservados. A inicialização está em JS externo; `/redoc` redireciona para `/docs`. O único fluxo OAuth implementado é password, sem necessidade de callback OAuth de redirecionamento.
- **Limite de corpo:** `MAX_REQUEST_BODY_BYTES=65536`, contabilizando os bytes efetivamente recebidos, sem confiar em Content-Length. Excesso retorna 413 antes do parser, mantendo CSP/CORS/headers. A configuração permite ajuste explícito entre 1 KiB e 1 MiB. Não é solução completa contra DoS.
- **Contrato OpenAPI corrigido:** formulário de login, resposta 202 de MFA, alternativas Bearer/cookie e erros foram descritos de acordo com o comportamento implementado.

Self-hosting evita carregar JavaScript de terceiros na sessão do usuário, mas transfere à equipe a responsabilidade de atualizar os assets. SRI não substitui avaliação de vulnerabilidades. A consulta OSV dos assets foi adicional e manual; o pip-audit do pipeline cobre Python, não o pacote npm vendorizado.

## 3. Scan passivo real com OWASP ZAP

`scripts/run_dast.py` inicia API e ZAP em portas locais temporárias, prepara duas contas de teste e uma consulta, autentica os clientes e envia o corpus pelo proxy. O ZAP somente observa as respostas: **não houve active scan, spider, Ajax spider ou exploração automatizada**. A fila passiva foi aguardada até esvaziar. Login e preparação ocorrem diretamente; seus corpos de resposta não fazem parte do corpus inspecionado.

| Corpus | Perfil | HTTP observado |
|---|---|---|
| `/health`, `/docs`, `/openapi.json` | público | 200 em cada rota |
| `/consultas`, `/consultas/1` | profissional | 200 em cada rota |
| `/agenda?dia=2030-10-15` | profissional e recepção, separadamente | 200 em ambos |
| `/admin/painel` | profissional sem papel administrativo | 403 |
| `/consultas` | sem credencial | 401 |

O corpus é deliberadamente finito. Não examina todas as mutações, login/MFA, assets estáticos, infraestrutura, concorrência ou todos os estados de autorização. Os testes complementam essas lacunas, sem equivaler a um pentest. A ausência de finding não demonstra ausência de vulnerabilidade.

### Correlação de todos os findings históricos e atuais

A taxonomia abaixo usa [OWASP Top 10:2025](https://top10.owasp.org/2025/). O mapeamento é uma análise deste relatório, não uma classificação automática do ZAP. A numeração mudou em relação a 2021; para BOLA também se aplica API1:2023 do OWASP API Security Top 10.

| ZAP / ocorrência | OWASP e ameaça | Antes: Ex12 → depois: Ex13 | Correção ou disposição e evidência |
|---|---|---|---|
| 10038, CSP ausente em `/docs` | A02:2025, TH-07 | Medium → não observado no mesmo corpus | `app/core/network.py`, CSP externa; teste `test_docs_locais_csp_e_integridade_de_assets`; ZAP final |
| 10038, CSP ausente em `/agenda` | A02:2025, TH-07 | Medium → não observado | mesma camada CSP; autoescape já existente; `test_xss_persistido_renderizado_como_texto`; ZAP final |
| 90003, SRI ausente em `/docs`, duas ocorrências | A08:2025, TH-07; relação com cadeia de fornecimento A03:2025 | 2 Medium → não observados | SRI no CSS e JS; assets locais e hashes testados; `app/templates/docs.html`, `security/vendor-assets.json` |
| 10017, JavaScript externo em `/docs` | A03:2025, TH-07 | Low → não observado | bundle hospedado pela aplicação; nenhuma URL CDN no HTML; manifesto e consulta OSV |
| 10109, Modern Web Application em `/docs` | sem categoria de vulnerabilidade aplicável | Informational → Informational | indica aplicação dependente de JavaScript; não há falha a corrigir nem CVSS atribuído. Limita a cobertura de scan sem navegador |
| 10031, atributo HTML controlável em `/agenda` | associação potencial com A05:2025, TH-07 | Informational, confiança Low → permanece igual | filtro `dia` validado como data e renderizado em atributo com escape. Alerta heurístico, sem XSS demonstrado. Validadores e teste de XSS sustentam a aceitação local; reavaliar se o template mudar |

O total passou de sete para dois registros. As cinco ocorrências removidas correspondem a quatro Medium e uma Low. A comparação utiliza plugin, rota e multiplicidade, não apenas contagem global. O alerta 10031 não foi omitido ou promovido a exploração comprovada. Os informativos são aceitos no gate; a proteção é mantida e deve ser reavaliada a cada alteração de template.

As exceções temporárias CSP/SRI do Exercício 12 foram removidas de `security/policy.json`. Atualmente qualquer Medium do ZAP sem triagem válida bloqueia; não há triagem Medium vigente. High/Critical, SAST bloqueante, qualquer vulnerabilidade Python detectada e ausência/falha de evidência bloqueiam. Regressões obrigatórias bloqueiam independentemente de severidade. CVSS e impacto de negócio dos findings históricos permanecem justificados em `docs/exercicio_12.md` e `security/`; não se inventou score CVSS para um alerta meramente informativo.

## 4. Testes unitários com mocking e integração

`tests/test_exercicio13.py` acrescenta 15 casos parametrizados. `MagicMock`, `AsyncMock` e `create_autospec(Session, instance=True)` isolam os pontos de entrada e autorização:

| Unidade / cenário | Resultado exigido |
|---|---|
| Login com username duplicado, campo de papel extra ou scope não permitido | 422 |
| Tipo multipart indevido | 415, parser de formulário não chamado |
| Formulário válido | contrato preservado, senha tratada como segredo |
| Profissional diferente ou paciente sem vínculo | 403, sem commit |
| Consulta não possuída | 404; expressão SQL contém parâmetros de consulta, profissional e vínculo |
| Papel não administrativo | 403 |
| Corpo maior que limite com Content-Length ausente, menor ou maior que o real | 413, aplicação interna não executada |

TestClient complementa os mocks com resposta 413 contendo CORS/headers, contrato OpenAPI e assets locais/SRI/CSP. Os mocks não comprovam persistência ou a ausência de SQL injection sozinhos: continuam passando os testes reais de driver SQL, transações, vínculos, conflito concorrente e persistência entre instâncias. O teste de sucesso `test_criar_e_buscar_consulta`, iniciado no Exercício 1, e a negação administrativa do Exercício 6 permanecem na suíte.

`security/threat-tests.json` exige também os controles do capstone no gate. Remover ou pular testes obrigatórios reprova a validação; testes sintéticos do avaliador de gate não são apresentados como scans reais.

## 5. Auditoria OpenAPI

O problema identificado era a diferença entre implementação e documentação: o login validado manualmente por `Request` não descrevia seu formulário, e uma união de respostas não explicitava corretamente o desafio MFA em HTTP 202. Isso dificultava o uso correto por clientes e a auditoria dos contratos.

`app/core/openapi.py` mantém o schema gerado por FastAPI e acrescenta o contrato faltante: `application/x-www-form-urlencoded`, campos obrigatórios e extras proibidos, senha `writeOnly`, 200 com `TokenRead` e 202 com `DesafioRead`. OAuth2PasswordBearer e JWTBearer são alternativas nas rotas protegidas; AgendaCookie aparece somente em GET `/agenda`. O JWTBearer permite usar o token obtido após MFA, pois o diálogo OAuth password padrão não automatiza o desafio administrativo em duas etapas.

O auditor `scripts/audit_openapi.py` verifica contratos públicos, allowlist de campos de saída, ausência de modelos ORM internos, operationIds únicos, esquemas de segurança, respostas relevantes e ausência de rotas de debug/seed. São 65 verificações aprovadas. O workflow inclui essa auditoria e salva o schema nos artifacts; o teste correspondente é obrigatório no gate. O schema não atribui claims M2M inexistentes.

**Limite:** documentação de segurança não impõe autorização; essa função continua no middleware e nas políticas testadas. A auditoria é estrutural, não um validador universal da especificação OpenAPI. A interface Swagger sob CSP não foi verificada em navegador: o inventário retornou zero navegadores e a criação do navegador integrado falhou com `Browser is not available: iab`. Os testes comprovam contrato, bytes e respostas dos assets, mas não substituem Authorize/Try it out no navegador. Prints dessa demonstração continuam pendentes; não foram fabricados.

## 6. Reprodução

Com Python 3.12 no ambiente virtual do projeto, dependências instaladas e Java 21 disponível:

```powershell
python -m pip install -r requirements.txt -r requirements-security.txt
python -m scripts.run_checks
python -m scripts.audit_openapi
python -m scripts.fetch_zap
python -m scripts.run_dast --zap-home .cache/security-tools/ZAP_2.17.0
python -m scripts.security_gate --reports reports
```

`run_checks` inicia uma rodada e remove resultados anteriores, inclusive ZAP; execute o scan depois dele. Scanners precisam de acesso às fontes oficiais. Erro de ferramenta não equivale a aprovação. As evidências desta execução Windows utilizaram ZAP/Java portáteis oficiais e um ajuste local de diretórios temporários para o sandbox; esse ajuste não integra a aplicação nem o pipeline Ubuntu. Não incluir ferramentas, bancos descartáveis, caches, `.env` ou `.venv` no ZIP.

## 7. Riscos residuais e decisão de liberação

| Risco residual | Aceitação / condição de encerramento |
|---|---|
| **TH-14: M2M do laboratório não implementado** | **Bloqueia produção e conclusão integral do Assessment.** Implementar Exercício 7: client credentials, escopos/claims distintos e acesso mínimo a disponibilidade; validar negações cruzadas |
| **TH-01/13: MFA apenas simulado** | **Bloqueia contas administrativas em produção.** Provedor/fator real, recuperação e operação segura; terminal com OTP só em demonstração fictícia |
| **TH-12: TLS real não implantado/verificado** | **Bloqueia produção.** Certificado, terminação TLS e confiança restrita no proxy; HSTS isolado não protege tráfego HTTP |
| **TH-10/11: proteção e recuperação do banco** | **Bloqueia uso com dados reais.** Comprovar ACL, criptografia apropriada, backup, restauração, retenção e migrações. Arquivo SQLite não protege contra administrador do host comprometido |
| **TH-09: abuso de rede e conexões lentas** | **Bloqueia exposição pública sem limites operacionais.** Corpo de 64 KiB e quotas não controlam volume, simultaneidade ou slowloris; configurar proxy/servidor e testar carga/recuperação |
| **TH-05: observabilidade operacional incompleta** | Eventos internos existem; 413 do limitador externo ocorre antes da auditoria e não contém X-Request-ID. Exigir logs no proxy, redaction, retenção, alertas e proteção externa da trilha antes de produção |
| **TH-02: revogação durante requisição em andamento** | Verificação ocorre na requisição, mas uma revogação concorrente após o check, especialmente no delete ORM, não garante interrupção instantânea. Aceitável só para a demonstração; definir semântica e proteção transacional antes de alegar revogação imediata |
| **TH-07: Swagger/CSP sem verificação visual** | Aceitação limitada aos testes estruturais. Pendentes Authorize/Try it out e prints reais. Sem navegador não se declara usabilidade comprovada |
| **Cadeia de fornecimento** | Zero advisories é retrato temporal. Fixação de versões e SRI reduzem riscos, mas não garantem origem íntegra para sempre. Incluir assets npm na monitoração contínua; hashes completos e política de atualização antes de produção |
| **CI e IAST** | Não houve execução remota, branch protection/ruleset obrigatório ou IAST instrumentado. Configurar e comprovar o job requerido antes de depender do gate para impedir merge. IAST é etapa planejada/justificada no Ex12, não evidência realizada |

**Decisão final: NO-GO para produção.** O gate passou no escopo automatizado, mas não verifica sozinho requisitos de produto e controles operacionais. Os bloqueadores acima não são aceitos para dados de saúde reais. A demonstração local com dados fictícios pode prosseguir.

## 8. Entrega e vídeo

O roteiro consolidado está em `docs/Roteiro_Final_Executavel_2026-10-03.md`, com 4min50s e prioridade para autorização, gate do Exercício 12 e decisões deste capstone. A gravação deve ser feita pelo aluno, com suas próprias palavras, demonstração funcionando e sem segredos visíveis. Link do YouTube não listado ainda não fornecido. Na etapa histórica deste relatório, prints, Exercício 7 e vídeo estavam pendentes. As capturas e a integração M2M foram concluídas posteriormente, conforme o índice atual; o vídeo pessoal permanece separado. O ZIP `Hebert_almeida_DR2_AT.ZIP` permanece para o final, conforme solicitado.

## Referências técnicas

- [OWASP Top 10:2025 — categorias usadas no mapeamento](https://top10.owasp.org/2025/).
- [FastAPI — servir assets próprios da documentação](https://fastapi.tiangolo.com/how-to/custom-docs-ui-assets/).
- [OWASP — Content Security Policy Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Content_Security_Policy_Cheat_Sheet.html).
- [ZAP — documentação de scan passivo](https://www.zaproxy.org/docs/desktop/start/features/pscan/).
- [Registro oficial npm — swagger-ui-dist](https://registry.npmjs.org/swagger-ui-dist/5.33.0).
