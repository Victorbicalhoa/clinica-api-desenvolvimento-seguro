> Registro técnico da etapa indicada. Para resultados atuais e alterações posteriores, consulte o [índice de documentação](README.md).

# Exercício 9 — Correção centralizada de entrada, saída e controles de segurança

**Autor:** Hebert Almeida · **Início:** 24/09/2026 · **Validação final:** 25/09/2026

## 1. Escopo e decisões

Esta etapa parte da aplicação entregue no Exercício 6 e da análise do Exercício 8. O Exercício 7 continua em rascunho externo, sem integrar esta baseline. Não foram incorporados arquivos desse rascunho.

Foram corrigidas as lacunas atuais apontadas no Exercício 8: limitação de autenticação, trilha de auditoria e integridade do agendamento. Também foram centralizados o middleware JWT e os contratos de entrada, ampliada a rejeição de campos extras e preservados SQL parametrizado, ownership e escape HTML.

**Regra de negócio confirmada pelo usuário nesta etapa:** no máximo uma consulta não cancelada por profissional no mesmo instante; transições de agendada para realizada ou cancelada. PUT não pode modificar uma consulta já finalizada, exceto repetir os mesmos dados. DELETE continua permitido ao profissional autorizado e é auditado; não foi estabelecida uma política de retenção clínica nesta etapa.

A BOLA, a rejeição de campos extras no JSON de consultas, a prevenção de SQL injection e o escape de XSS já funcionavam antes da alteração. O relatório não os apresenta como falhas abertas descobertas agora. A comparação usa o mesmo script e os mesmos payloads em bancos fictícios isolados, sem desativar controles para fabricar uma exploração.

## 2. Validação por whitelist e regex

`app/models/entrada.py` define a base Entrada com `extra='forbid'`. ConsultaWrite, MFAWrite, LoginForm, CorpoVazio e filtros administrativos usam contratos explícitos. Os contratos de consulta preservam IDs positivos estritos, enum de status, data/hora com fuso e limite de observacao. MFA aceita apenas challenge_id hexadecimal de 32 posições e code de seis dígitos.

LoginForm define uma allowlist de campos de formulário: grant_type=password, username, password e campos OAuth compatíveis com o Swagger que só podem ser vazios nesta versão. Papéis e identificadores de usuário não são aceitos como campos extras. Username usa a regex ancorada `^[A-Za-z0-9._-]{1,100}$`, compartilhada com o provisionamento local. Senhas são tratadas como SecretStr e limitadas a 72 bytes UTF-8 para bcrypt, sem truncamento.

`app/auth/validation.py` rejeita campos duplicados, parâmetros de URL inesperados no login e Content-Type inadequado. A resposta de erro não devolve o formulário recebido. O handler de RequestValidationError remove valores de input e contexto de exceção, para que senhas, OTPs ou observações não sejam refletidos por erro de validação.

Observacao permanece texto livre limitado, incluindo pontuação e marcação como dados. Não foi criada regex que proíba palavras SQL ou tags como defesa principal: SQL injection depende de parametrização e XSS depende de codificação no contexto de saída. Essa separação segue a [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html).

## 3. Middleware JWT e autorização por recurso

`app/auth/middleware.py` centraliza a validação de JWT para as requisições HTTP. A política padrão exige autenticação; exceções públicas são declaradas por método e caminho. Apenas os endpoints de login/MFA, health, documentação e arquivos estáticos necessários são públicos. Uma rota nova sem Depends não fica anônima automaticamente.

O middleware chama a validação existente de assinatura HS256, expiração, emissor, audiência e sessão persistida. Identidade e sessão só entram em request.state após validação. As dependências reutilizam esse estado, sem decodificar o token novamente. SQL síncrono é executado fora do event loop; a sessão usada para autenticar é encerrada antes de chamar a rota.

Cookie é aceito somente em GET /agenda. Uma credencial Authorization explícita inválida não recai no cookie válido. As demais rotas protegidas exigem Bearer. Erros antes das rotas são convertidos em respostas HTTP com os cabeçalhos necessários, sem expor exceções internas. Referência de integração: [FastAPI — Middleware](https://fastapi.tiangolo.com/tutorial/middleware/).

**Ownership integra a mesma cadeia de segurança, na camada que conhece o recurso:** app/auth/policies.py mantém scope_consultas, owned_consulta e authorize_write. Middleware autentica; dependências exigem papel; políticas filtram paciente/profissional; serviços fazem a alteração autorizada. O middleware não tenta deduzir ownership por uma regex da URL. JWT válido não autoriza por si só a consulta. GET/PUT/DELETE de terceiros retornam 404, e listas/agenda profissional usam o mesmo predicado de vínculos.

Os testes demonstram que o JWT é validado uma vez por requisição e que cabeçalhos como X-User-ID não substituem identidade validada. Novos endpoints com dados de consultas devem reutilizar a política de recurso; autenticação padrão não elimina a necessidade dessa autorização.

## 4. SQL parametrizado e codificação de saída

As consultas e alterações usam expressões SQLModel/SQLAlchemy com parâmetros. O texto `x'); DROP TABLE consulta; --` é persistido como observacao literal; a tabela continua acessível. Não há concatenação de entrada em SQL. Os comandos DDL estáticos de proteção da auditoria não recebem valores fornecidos pelo cliente.

Jinja2 mantém Environment compartilhado, StrictUndefined, herança e select_autoescape habilitado para HTML, XML e strings. ConsultaRead limita os campos do contexto; a recepção recebe observacao vazia. O payload `<img src=x onerror="alert(1)">` permanece texto escapado na célula HTML, sem elemento img executável. A evidência inspeciona o HTML retornado e suas tags; não é uma gravação de execução JavaScript em navegador. Referência: [OWASP XSS Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html).

Não há safe/Markup aplicado a observacao. Se o conteúdo for usado futuramente em JavaScript, CSS ou URL, será necessário tratamento específico desse contexto; o escape de texto HTML não cobre essas transformações.

## 5. Correções das lacunas atuais do Exercício 8

### V08-02 — Orçamento de autenticação persistido

`app/auth/limits.py` mantém contadores SQLite com UPSERT atômico e confirmação da contagem antes da decisão de autenticação. Um erro de senha ou rollback de desafio não devolve o orçamento. As chaves usam hash estável de categoria e identificador, compartilhável entre workers com o mesmo banco; esse hash é pseudônimo e não garante anonimato.

Padrões: cinco tentativas por username no login, cinco confirmações MFA por conta, 60 requisições de autenticação por origem, em janela fixa de 60 segundos. Tanto falhas quanto tentativas bem-sucedidas consomem orçamento. Novos desafios não zeram o orçamento MFA da conta. Ao exceder o limite, a API retorna 429 com Retry-After e registra um evento marcado como alerta. A origem usa o peer visto pela aplicação, sem interpretar X-Forwarded-For fornecido pelo cliente. Em implantação com proxy, configurar explicitamente quais proxies podem influenciar o peer.

Limites são configuráveis em Settings. A janela fixa pode permitir concentração de tráfego perto de sua virada, e o bloqueio temporário por conta pode ser induzido por terceiros; esses são riscos residuais de disponibilidade. Não é proteção completa contra botnets ou substituto de limites de conexão/corpo e controles de infraestrutura.

### V08-03 — Auditoria estruturada e proteção da trilha

`app/auth/audit.py` centraliza eventos com request_id gerado pelo servidor, instante UTC, ator validado quando existente, ação, método, template de rota, identificador tipado do recurso, status e marcação de alerta. Não armazena corpo, query string, senha, hash, token, OTP ou observacao. Falha de login não é atribuída a uma identidade autenticada apenas pelo username enviado.

Criação, atualização e exclusão de consulta gravam mutação e evento na mesma transação. Se não for possível registrar a mutação, o recurso não é confirmado. Leituras, negações e erros são registrados pelo middleware, incluindo erro inesperado 500 com mensagem genérica. Se a auditoria de uma leitura protegida estiver indisponível, o conteúdo não é liberado.

O template de rota e o ID de consulta são obtidos da rota efetivamente processada pelo FastAPI. Falhas anteriores ao despacho, como JWT inválido, não têm necessariamente recurso identificado: usam marcador `<unmatched>`; os endpoints exatos de autenticação são reconhecidos para contabilizar seus alertas. Não se registra uma URL arbitrária para preencher essa lacuna.

GET /admin/auditoria permite consulta paginada somente a administrador com sessão MFA. Triggers SQLite rejeitam UPDATE e DELETE na tabela de eventos. Um operador com controle total do arquivo/banco ainda pode remover triggers ou substituir arquivos; separação de infraestrutura e armazenamento externo protegido são evoluções necessárias.

`alerta=true` identifica limitação de autenticação e pode ser consultado pelo administrador. Isso é detecção e registro local, não entrega de notificações a um SOC, monitoramento contínuo ou SIEM. A lacuna de trilha da aplicação foi tratada; o processo operacional de retenção, revisão periódica e encaminhamento externo de alertas continua pendente.

### V08-04 — Conflito e transições da agenda

`app/auth/consultas_service.py` centraliza POST, PUT e DELETE autorizados, preservando ownership. Novas consultas começam como agendada. PUT permite finalizar uma consulta agendada; não permite reabrir ou modificar os dados de uma consulta terminal. Uma atualização condicional pelo estado lido impede que uma transição concorrente simplesmente sobrescreva o novo estado.

O índice único parcial `uq_consulta_profissional_instante_ativa` impede duplicidade de profissional/data_hora quando status não é CANCELADA. A expressão usa o enum tipado do modelo, evitando confundir o valor público do enum com sua representação persistida. Cancelar libera o instante; realizada continua ocupando aquele instante. O índice também cobre concorrência e PUT que tente mover uma consulta para um horário já ocupado. Conflitos retornam 409 sem texto SQL ou parâmetros sensíveis. Referência: [SQLAlchemy — índices parciais SQLite](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#partial-indexes).

A regra é sobre igualdade de instantes UTC. Não foram inventados duração, intervalos sobrepostos, política de horários de trabalho ou retenção clínica. A integridade referencial de um cadastro completo de pacientes ainda requer a modelagem desse recurso.

## 6. Endpoint adicional não citado no Exercício 8

**POST /auth/browser-session** não foi citado explicitamente na análise anterior e compartilhava um contrato permissivo de entrada: um corpo com `{"usuario_id": 2}` era ignorado e a operação retornava 204. Isso não trocava a identidade nem elevava privilégios — o token continuava determinando o usuário —, mas aceitava campos não declarados.

A dependência compartilhada empty_body agora aplica CorpoVazio com extra=forbid; a mesma requisição retorna 422 antes de emitir cookie. Uma requisição legítima sem corpo continua retornando 204. A correção também foi aplicada a **POST /auth/logout**, impedindo que esse tipo de operação acumule aceitação silenciosa de campos.

GET /admin/auditoria é um endpoint novo criado para a correção de auditoria; não é usado como substituto do requisito de corrigir um endpoint adicional já existente.

## 7. Evidências comparáveis de antes e depois

O script `evidencias/exercicio_09/reproduzir_comparacao.py` foi executado primeiro contra cópia da baseline anterior e depois contra a aplicação corrigida, sempre com SQLite em memória, dados fictícios e credenciais efêmeras não registradas. `antes.json` e `depois.json` identificam os arquivos por SHA-256. O script reutiliza payloads idênticos; não instala rota vulnerável ou desliga autenticação/escape. A cópia de trabalho antiga não integra o código entregue.

| Entrada/ação idêntica | Antes real | Depois real |
|---|---|---|
| Segundo POST para mesmo profissional/instante | 201, duplicidade permitida | 409 |
| PUT realizada → agendada | 200 | 409 |
| Sete senhas incorretas para o mesmo username na janela | Sete respostas 401 | Cinco 401, depois duas 429 |
| Username fora da regex | 401 após caminho de autenticação | 422 por contrato |
| Campo papel extra no formulário de login | 200; campo ignorado, sem elevação | 422 |
| usuario_id extra em /auth/browser-session | 204; campo ignorado, sem troca de identidade | 422 |
| Consulta ao endpoint de auditoria como administrador MFA | 404; endpoint inexistente | 200, eventos reais sem conteúdo clínico |
| GET/PUT de consulta de outro profissional | 404 | 404 — controle preservado |
| Campo criado_em extra no JSON da consulta | 422 | 422 — controle preservado |
| Payload de XSS em observacao | Texto escapado, sem tag img | Mesma proteção |
| Payload de SQL em observacao | Texto literal; tabela acessível | Mesma proteção |

**Limite explícito:** não existe evidência de exploração bem-sucedida de BOLA/SQLi/XSS na baseline, pois esses controles já estavam ativos. As provas de correção inédita estão nas primeiras linhas da tabela; as demais são regressões de segurança. Não confundir um 200 ao armazenar texto de ataque com execução de SQL ou JavaScript.

Os testes também verificam conflito concorrente com conexões SQLite distintas, cancelamento que libera horário, bloqueio de reabertura, rollback de mutação quando a auditoria falha, imutabilidade da trilha, rate limit entre desafios e janela de recuperação. Os resultados finais são registrados em pytest.txt, ruff.txt, format.txt e checks.json na pasta de evidências.

**Resultado final em 25/09/2026:** 90 testes aprovados em 57,74 segundos; Ruff aprovado; 35 arquivos Python com formatação aprovada. Os dois avisos da suíte são depreciações conhecidas de Starlette/httpx e AnyIO. A janela do limitador é fixada pelo relógio injetável somente nos testes/probe para evitar flutuação na virada de minuto; a aplicação normal usa o relógio real, e a expiração JWT não é desativada.

Para reproduzir a versão atual, na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m ruff check --no-cache app tests
.\.venv\Scripts\python.exe -m ruff format --check --no-cache app tests
.\.venv\Scripts\python.exe evidencias/exercicio_09/reproduzir_comparacao.py --root . --out evidencias/exercicio_09/reexecucao_atual.json
```

O comando reproduz o lado atual; antes.json é o registro histórico obtido antes da instalação, com hashes da baseline. Não executar o probe atual e chamá-lo de “antes”. As evidências são respostas HTTP e verificações reais de HTML/SQL em testes, não prints de navegador ou resultados de ZAP. Capturas para a entrega final continuam pendentes e devem ocultar credenciais. O código inseguro didático do Exercício 8 não foi adicionado à aplicação.

## 8. Rastreabilidade e operação

| Referência Ex8 / threat model | Controle / teste |
|---|---|
| V08-01 / TH-02 / MT-02 / VT-02 | Middleware JWT + política de ownership compartilhada; regressões de acesso cruzado e lista/agenda |
| V08-02 / TH-01, TH-09 / MT-09 / VT-09 | Orçamentos persistidos por origem e conta; 429 e recuperação; orçamento entre desafios |
| V08-03 / TH-05 / MT-06 / VT-05 | Eventos sem segredos, ator validado, mutação atômica, proteção contra alteração/exclusão |
| V08-04 / TH-04 / MT-05 / VT-04 | Regra aprovada, índice único parcial e atualização condicional; concorrência e transições |
| TH-03, TH-06, TH-07, TH-08 | Extra forbid, response models, parametrização e autoescape preservados |

As tabelas auxiliares e o índice são aplicados ao iniciar. `create_all` não migra tabelas antigas sozinho: o índice é criado explicitamente também para a tabela existente. Se houver duplicidades incompatíveis, a inicialização falha e preserva as linhas, exigindo saneamento revisado; novas tabelas auxiliares podem já ter sido criadas. Nenhum registro é excluído automaticamente para fazer a migração passar. Use banco novo para a demonstração, mantendo o anterior preservado.

Esta implementação dos controles transacionais é específica para SQLite. Outro dialeto é rejeitado antes de DDL, em vez de simular que índices, triggers e UPSERT terão a mesma semântica. Não há nova dependência externa.

```powershell
# Na raiz do projeto, escolha um nome de banco ainda nao utilizado:
$env:DATABASE_URL = "sqlite:///./data/clinica_exercicio09.db"
.\.venv\Scripts\python.exe -m app.auth.provision profissional1 --papel profissional --profissional-id 2 --paciente-id 1
.\.venv\Scripts\python.exe -m app.auth.provision admin --papel administrador
$env:MFA_SIMULATED = "true"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

As senhas são solicitadas sem eco. O MFA de administrador continua simulado, opt-in e entregue no terminal, conforme Exercício 6; não gravar códigos ou tokens no vídeo. Não foi configurada exposição pública, TLS de implantação, proxy, SIEM, política de retenção ou M2M. Configurações reais e bancos não fazem parte do pacote final.

## 9. Roteiro selecionado — aproximadamente 45 segundos

**0–15 s:** mostrar a tabela antes/depois: “Usei os mesmos payloads em duas versões isoladas. Duplicar horário retornava 201; agora retorna 409. Campos extras antes ignorados agora são rejeitados com 422.”

**15–30 s:** mostrar middleware.py e policies.py: “O JWT é validado uma vez, e as rotas usam uma política compartilhada de ownership. A regex valida campos estruturados; SQL usa parâmetros, e texto livre sai pelo autoescape do Jinja.”

**30–45 s:** mostrar o teste concorrente e um evento de auditoria sanitizado: “Apenas uma reserva vence o conflito concorrente. A mutação e seu evento são confirmados juntos. Não registrei observações clínicas, senhas ou tokens na auditoria.”

Este trecho pode ser combinado com os Exercícios 6 e 8, sem somar todos os roteiros integralmente. Preservar tempo no vídeo de até cinco minutos para o security gate do Exercício 12 e o capstone do Exercício 13. ZIP somente ao final.
