> Registro técnico da etapa indicada. Para resultados atuais e alterações posteriores, consulte o [índice de documentação](README.md).

# Exercício 10 — Hardening de rede e proteção contra abuso

**Assessment: Desenvolvimento Seguro de Aplicações Web — Hebert Almeida**  
Data: 25/09/2026. Aplicação: API de agendamento de consultas. Continuação da baseline do Exercício 9; o rascunho incompleto do Exercício 7 não integra esta entrega.

## Implementação e decisões

### CORS com origens explícitas

`app/core/config.py` declara `CORS_ALLOW_ORIGINS` como lista validada. O exemplo autoriza somente `http://localhost:3000` e `http://127.0.0.1:3000`, destinados ao frontend local. Na implantação, substituir pelos domínios HTTPS reais. Wildcard, credenciais na URL, caminhos, query, fragmentos e HTTP fora de loopback são rejeitados na configuração. Uma lista vazia não autoriza nenhuma origem.

`app/core/network.py` usa `CORSMiddleware` com métodos GET, POST, PUT e DELETE; headers Authorization e Content-Type; exposição de Location, Retry-After e X-Request-ID; cache de preflight de 600 segundos. Os headers simples previstos pelo protocolo também são aceitos pelo middleware. `allow_credentials=False`: o frontend usa Bearer explicitamente e a agenda interna mantém seu cookie na mesma origem. Não habilitamos cookies entre origens.

O preflight permitido responde 200 sem exigir JWT, mas a operação subsequente continua sujeita à autenticação e ao ownership. Origem, método ou header não permitido resulta em preflight 400. Uma requisição simples de origem negada pode chegar ao servidor: a ausência de Access-Control-Allow-Origin impede sua leitura pelo navegador. CORS não substitui autorização nem impede clientes HTTP fora do navegador.

### Cabeçalhos centralizados, inclusive nos erros

`SecurityHeaders`, middleware ASGI, aplica:

| Cabeçalho | Valor | Finalidade |
|---|---|---|
| X-Frame-Options | DENY | Impedir incorporação da página em frames |
| X-Content-Type-Options | nosniff | Evitar interpretação incompatível com o tipo declarado |
| Strict-Transport-Security | max-age=31536000 | Instruir o navegador a preferir HTTPS por um ano após uma resposta HTTPS válida |

HSTS é emitido somente quando o esquema ASGI é HTTPS. HTTP local não anuncia esse cabeçalho. A aplicação não interpreta diretamente X-Forwarded-Proto nem X-Forwarded-For. Atrás de proxy, o servidor ASGI deve confiar exclusivamente nos endereços reais dos proxies autorizados; nunca configurar confiança irrestrita. O proxy deve remover/substituir headers encaminhados recebidos de clientes externos.

Não foram ativados includeSubDomains ou preload porque o projeto não possui inventário e domínio real que permitam assumir esse compromisso. HSTS não instala certificado, não cria um listener TLS nem protege a primeira visita HTTP. Terminação TLS, redirecionamento HTTP e testes reais do domínio continuam sendo tarefas de implantação. O teste de URL HTTPS no TestClient verifica o comportamento ASGI, sem handshake TLS ou certificado.

`HardenedAPI` preserva a interface FastAPI e envolve sua pilha completa: SecurityHeaders → CORS → pilha FastAPI, incluindo ServerErrorMiddleware → demais middlewares e rotas. Isso cobre respostas de preflight e erros gerados fora do middleware JWT. Os testes exercitam 401, 403, 422, 429 e um 500 real induzido em uma aplicação de teste isolada. Não há endpoint de falha na aplicação entregue.

### Rate limiting diferenciado

O mecanismo centralizado do Exercício 9 foi ampliado, sem duplicar contadores nas rotas. `app/auth/limits.py` executa UPSERT atômico parametrizado em SQLite; `app/auth/middleware.py` aplica os novos orçamentos. Chaves pseudonimizadas com SHA-256 e contadores persistidos são compartilhados pelos processos que utilizam o mesmo banco. Isso não anonimiza IPs ou usernames nem fornece proteção de rede distribuída.

| Operação e chave | Limite padrão | Janela |
|---|---:|---:|
| Login, por username normalizado | 5 | 60 s |
| Login, por endereço do cliente ASGI | 20 | 60 s |
| Login e MFA agregados, por endereço do cliente | 60 | 60 s |
| Verificação MFA, por conta | 5 | 60 s |
| Requisições autenticadas protegidas, por ID do usuário | 120 | 60 s |

O primeiro orçamento esgotado retorna 429 com Retry-After. A quota de login por endereço é aplicada antes da validação do formulário e do bcrypt; assim, trocar username não permite tentativas ilimitadas a partir do mesmo endereço. A quota por conta permanece independente do IP. A quota geral ocorre após autenticação e antes do endpoint, contando também operações autenticadas que posteriormente retornem 403/422. Trocar de token não reinicia essa quota.

**POST /auth/logout fica isento da quota geral**, mantendo autenticação, revogação e auditoria. A exceção permite encerramento de sessão mesmo após esgotamento do orçamento. Token revogado passa a retornar 401.

Saúde, documentação, arquivos estáticos e preflight não usam a quota autenticada. Requisições sem identidade válida às rotas protegidas continuam retornando 401; não recebem o orçamento por usuário. Requisições bloqueadas pelos limites de autenticação/API entram na auditoria existente com alerta e respostas sensíveis mantêm no-store. Não há promessa de auditoria para preflights tratados externamente à aplicação.

O algoritmo usa janela fixa, podendo permitir rajadas na virada da janela. Limitar por conta pode ser explorado para bloquear temporariamente um usuário; NAT também agrupa clientes legítimos. Os valores são configuráveis e devem ser calibrados com métricas. Ataques volumétricos, crescimento de auditoria/contadores, limites de corpo, timeouts e tráfego não autenticado exigem controles adicionais no proxy e operação. A implementação não representa proteção completa contra DoS.

## Configuração e reprodução

`.env.example` contém apenas valores de demonstração, incluindo:

```dotenv
CORS_ALLOW_ORIGINS=["http://localhost:3000","http://127.0.0.1:3000"]
LOGIN_IP_LIMIT=20
API_REQUEST_LIMIT=120
HSTS_MAX_AGE=31536000
AUTH_LOGIN_LIMIT=5
AUTH_MFA_LIMIT=5
AUTH_IP_LIMIT=60
AUTH_WINDOW_SECONDS=60
```

Não houve alteração do esquema de persistência nesta etapa: o banco compatível com o Exercício 9 pode ser reutilizado. Permanecem as instruções anteriores de migração para bancos mais antigos. Não há contas ou senhas padrão.

Na raiz do Assessment, com o ambiente virtual preparado:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m ruff check --no-cache app tests
.\.venv\Scripts\python.exe -m ruff format --check --no-cache app tests
.\.venv\Scripts\python.exe evidencias/exercicio_10/reproduzir.py --root . --out evidencias/exercicio_10/reexecucao.json
```

O script de evidências cria banco em memória, gera uma credencial efêmera e salva somente status e cabeçalhos selecionados, sem senha, token ou dados clínicos. Usa relógio fixo apenas para a janela dos limites; não altera o relógio do JWT. O resultado de referência está em `evidencias/exercicio_10/http.json`; a reexecução preserva esse registro histórico.

## Verificação e rastreabilidade

`tests/test_exercicio10.py` cobre allowlist, preflight, configuração inválida, headers HTTP/HTTPS e erros, spoofing de headers encaminhados, login por endereço, isolamento entre quotas, logout após bloqueio, renovação de token e reinício da janela. A suíte completa também verifica ownership, bcrypt/JWT/MFA, validação, XSS, auditoria, concorrência e conflitos de agenda das etapas anteriores.

Resultados finais e quantidades estão registrados em `checks.json` e no log integral `pytest.txt`; Ruff e formatação têm logs separados. Os dois avisos de depreciação do TestClient/httpx e BlockingPortal são de dependências existentes, sem falha de teste. `alteracoes_sha256.json` identifica arquivos modificados; `http.json` registra hashes do código usado nas sondagens.

| Requisito | Implementação | Evidência |
|---|---|---|
| CORS explícito | Settings + CORSMiddleware | Preflight 200/400 e ausência de ACAO para origem negada |
| HSTS, XFO, XCTO | SecurityHeaders externo | Headers em respostas normais, preflight e erros |
| Login mais restritivo | Orçamentos de conta/IP menores que quota de API | Cinco falhas 401, sexta 429, consulta autenticada 200 |
| Centralização e regressão | auth/limits, auth/middleware, core/network | Suíte completa e testes de regressão |

Na modelagem anterior, o rate limiting contribui para TH-09/MT-09/VT-09 (abuso/disponibilidade). HSTS contribui parcialmente para TH-12/MT-11/VT-12 (transporte), sem encerrar o risco enquanto TLS real não for implantado. O exercício concretiza controles na fronteira externa descrita no Exercício 5. Autorização de recursos permanece vigente; integração M2M do Exercício 7 continua pendente.

## Trecho opcional para o vídeo — aproximadamente 25 segundos

Mostrar `core/network.py` e a allowlist: “Autorizei somente as origens do frontend e mantive Bearer e ownership nas operações.” Exibir a evidência da sexta tentativa de login com 429 e Retry-After: “O login tem limites menores que os recursos autenticados; trocar token não reinicia a quota do usuário.” Finalizar nos headers: “HSTS é enviado em HTTPS; nos testes validei o cabeçalho, e a implantação ainda precisa de TLS real.”

Este trecho integra o vídeo único de até cinco minutos, reservando tempo para os Exercícios 12 e 13. Prints e gravação pessoal permanecem pendentes; logs e testes não são apresentados como capturas de tela. Não foi criado ZIP.

## Referências primárias

- [FastAPI — CORS](https://fastapi.tiangolo.com/tutorial/cors/): configuração e conceito de origem.
- [Starlette — middleware](https://www.starlette.io/middleware/): aplicação externa de CORS para cobertura de erros.
- [OWASP — HTTP Headers Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Headers_Cheat_Sheet.html): cabeçalhos defensivos.
- [OWASP — HSTS Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTTP_Strict_Transport_Security_Cheat_Sheet.html): requisitos e alcance do HSTS.
