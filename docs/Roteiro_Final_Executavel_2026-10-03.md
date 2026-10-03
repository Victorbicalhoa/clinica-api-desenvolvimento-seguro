# Roteiro detalhado de gravação — AT Desenvolvimento Seguro

**Aluno:** Hebert Almeida · **Tempo máximo:** 5 minutos · **Meta:** 4min50s, reservando 10s de margem.

Este guia contém preparação fora da gravação, ensaio técnico, sequência cronometrada, falas sugeridas e checklist de publicação. O aluno deve entender o código e explicar com suas próprias palavras. A gravação pessoal é uma exigência do AT; este roteiro não é um vídeo pronto.

**Versão final de preparação em 03/10/2026.** O código está publicado em https://github.com/Victorbicalhoa/clinica-api-desenvolvimento-seguro. O Actions aprovou a main com 226 testes; o PR #1 reprovou exclusivamente o teste sentinela (226 passaram). A regra persistida de main foi confirmada no navegador: PR e security-gate obrigatórios, branch atualizada e sem bypass administrativo. O PR reprovado mostrou merge desabilitado. Após remover a sentinela, o run 37120246049 aprovou o HEAD 22caf38475ebb5777727f1fff14e379956afec18 e o merge foi habilitado. O Astra revisou essa evidência e aprovou R21; a matriz atual tem 24/24 com evidências, sem substituir a avaliação do professor. O repositório do professor foi usado somente para comparação.

**Comece pelo checklist executável da seção 0 abaixo.** As seções seguintes preservam os comandos completos, explicações e falas. Este documento substitui o roteiro de 02/10 como guia de gravação; os relatórios anteriores permanecem como histórico.

## 0. Checklist executável: da abertura do projeto à gravação

### A. Preparar a mesa de gravação (fora dos cinco minutos)

1. Abra o projeto no editor. No explorador, expanda `app/routes`, `app/models`, `app/database` e `app/auth`.
2. Abra três PowerShells e identifique-os mentalmente como A (servidor), B (demonstração humana) e C (laboratório). O Terminal A ficará rodando até o fim.
3. Execute **2.2 → 2.3 → 2.4 → 2.5 no mesmo Terminal A**, na ordem. Não pule a criação de um banco novo. Nas solicitações de senha, escolha valores exclusivos do ensaio e mantenha-os fora do vídeo. Não use as credenciais de sua conta GitHub.
4. Copie somente o dia UTC da oferta, por exemplo `2026-10-05`; use o valor gerado no seu ensaio, não este exemplo fixo. Deixe-o anotado para o Terminal C.
5. Espere o Uvicorn mostrar `Application startup complete`. No navegador, abra `http://127.0.0.1:8000/health`; depois `http://127.0.0.1:8000/docs`. A página deve carregar e mostrar as rotas.
6. Faça uma execução completa do Terminal B seguindo 2.6. Anote `id` e os dez primeiros caracteres de `data_hora`. Este primeiro ensaio cria um registro que já permite preparar a aba da agenda.
7. Prepare a agenda pelos cliques da sequência B abaixo. Deixe a aba aberta. Na gravação, atualize-a após a terceira pausa do script; o dia é o retornado pelo script. Se o ensaio atravessar meia-noite UTC, ajuste o dia.
8. Deixe abertas duas abas do GitHub: [run aprovado](https://github.com/Victorbicalhoa/clinica-api-desenvolvimento-seguro/actions/runs/37095591151) e [run reprovado controlado](https://github.com/Victorbicalhoa/clinica-api-desenvolvimento-seguro/actions/runs/37095705289). Abra também [PR #1](https://github.com/Victorbicalhoa/clinica-api-desenvolvimento-seguro/pull/1). Se o estado já tiver mudado, use os links das execuções históricas para explicar a prova registrada.
9. No editor, abra `.github/workflows/security.yml`, `security/policy.json`, `security/risk-register.json`, `docs/Exercicio_13_Rastreabilidade_2026-10-02.json` e `docs/exercicio_13.md`. Use Ctrl+P e cole cada caminho. Deixe o trecho relevante visível antes de gravar.
10. Abra os resultados preservados em `evidencias/github_r21_2026-10-03/aprovado/`: `pytest.txt` (última linha), `gate.json`, `zap.json` e `openapi-audit.json`. Esses são resultados reais do GitHub Actions; não é necessário aguardar o scan no vídeo.
11. Ajuste o zoom do editor/terminal para os números ficarem legíveis. Faça uma gravação de dez segundos e confira microfone e texto. Feche notificações e qualquer arquivo de segredo.
12. Execute novamente o script humano no Terminal B e pare no primeiro ENTER. Execute o script M2M no C usando o dia anotado e pare no ENTER. Inicie a gravação até dois minutos após emitir o token: o token M2M dura cinco minutos e será usado por volta de 1min50s. Se demorar na preparação, reinicie o cliente C antes de gravar.

### B. Cliques exatos para abrir a agenda autenticada

1. Na aba `http://127.0.0.1:8000/docs`, clique **Authorize** no topo.
2. Na seção **OAuth2PasswordBearer**, preencha username `video_prof1` e a senha fictícia criada no provisionamento. Deixe client_id/client_secret dessa seção vazios. Clique **Authorize** da seção e depois **Close**. Faça isso fora da gravação.
3. Encontre o grupo **Autenticacao** e expanda **POST /auth/browser-session**. Clique **Try it out** e **Execute**. O resultado esperado é **204**. Esse endpoint cria a sessão da agenda no navegador; autenticar apenas o Swagger não basta para abrir uma aba HTML autenticada.
4. Abra nova aba da mesma origem e digite `http://127.0.0.1:8000/agenda?dia=AAAA-MM-DD`, trocando a data pelo dia UTC retornado pelo script humano.
5. Confira o profissional #901, paciente #9001 e o texto `<script>alert("XSS")</script>` na observação. Não deve surgir popup. O texto específico XSS-AT aparece nas capturas históricas; o script entregue usa XSS. Ambos são payloads fictícios.
6. Se a preparação ultrapassar quinze minutos, renove o login e a sessão da agenda antes de gravar. Mantenha somente a agenda visível na gravação. A área **curl** do Swagger contém Authorization após executar operações; não grave essa área nem o retorno de login/cookie.

### C. Roteiro de operação durante a gravação (4min50s)

| Cronômetro | Faça exatamente na tela | Resultado a apontar |
|---|---|---|
| 0:00 | Inicie o gravador com editor visível; aponte as quatro pastas abertas | Modularização e contexto clínico, sem percorrer os 13 exercícios |
| 0:25 | Alt+Tab para B; pressione ENTER uma vez | 201, 200 e seis campos públicos; destaque ausência de auditoria |
| 0:55 | Em B, pressione ENTER uma vez; depois abra `app/auth/policies.py` no editor | 404 para outro profissional e 403 para rota administrativa; RBAC + ownership |
| 1:25 | Volte a B; pressione ENTER uma vez. Troque para a aba da agenda e atualize | 422, escape e headers; payload visível como texto na página |
| 1:50 | Alt+Tab para C; pressione ENTER uma vez | Disponibilidade 200 com campos mínimos e consultas 401 para token M2M |
| 2:10 | Mostre workflow, policy e risk-register no editor | Justifique fases SDLC, severidade e impacto de dados de saúde |
| 2:50 | Mostre run aprovado; em seguida, run reprovado e etapa Aplicar security gate | Aprovado na main; falha controlada no PR. Mostre também as capturas 07 (bloqueio) e 14 (liberação); sentinela não é vulnerabilidade real |
| 3:20 | Abra `zap.json` aprovado e a rastreabilidade; localize TH-07 | Dois informativos; correlação ameaça → controle → teste → evidência |
| 4:15 | Abra última linha de pytest e resumo OpenAPI; depois riscos residuais | 226 testes, 74 verificações; distinguir demonstração local de produção |
| 4:40 | Volte ao relatório técnico | Conclua a decisão de NO-GO para produção e encerre até 4:50 |

Use as falas da seção 3 como referência. Explique naturalmente o **porquê** do gate e da decisão residual. Não tente ler este checklist durante a gravação; faça um ensaio com cronômetro. Se ultrapassar cinco minutos, reduza navegação e introdução, preservando a explicação dos Exercícios 12 e 13.

### D. Prova de merge concluída: como conferir ou reproduzir

**Concluída em 03/10/2026. Não precisa repetir para gravar.** Abra `docs/Prova_GitHub_R21_2026-10-03.md`, as capturas 06/07/14 em `evidencias/capturas_2026-10-03` e o [run positivo do PR](https://github.com/Victorbicalhoa/clinica-api-desenvolvimento-seguro/actions/runs/37120246049). A sentinela já foi removida. O procedimento abaixo registra como a prova foi feita; se reproduzir, use uma nova branch/PR de demonstração e preserve as evidências históricas. Não procure a sentinela na versão final da main.

1. Entre na sua conta e, se o GitHub mostrar **Confirm access**, confirme diretamente no site. Não coloque senha, OTP ou token no relatório.
2. Abra `https://github.com/Victorbicalhoa/clinica-api-desenvolvimento-seguro/settings/branches`. Verifique se a regra para `main` realmente foi salva. Se estiver ausente, crie uma regra clássica para `main`.
3. Configure **Require a pull request before merging**, **Require status checks to pass before merging**, o check **security-gate** de GitHub Actions e **Require branches to be up to date before merging**. Marque **Do not allow bypassing the above settings**. Não habilite force push/deletion. Neste projeto individual, não exigir uma aprovação de outro revisor inexistente.
4. Salve e reabra a regra para verificar persistência. No PR #1, confirme o check reprovado e a mensagem/botão que impede o merge. Salve uma captura da regra e uma do bloqueio; não basta fotografar um X vermelho no workflow.
5. Só depois de preservar a prova negativa, remova `tests/test_gate_demonstracao.py` **da branch `evidencia/security-gate`**, sem mexer na main. Adicione à mesma branch o relatório da prova ou as evidências sanitizadas, para haver uma alteração útil após remover a sentinela.
6. Aguarde uma execução nova e aprovada no **HEAD atualizado do PR**. A execução aprovada na main comprova o pipeline, mas não substitui essa nova execução positiva do PR.
7. Registre URL, SHA, resultado, data e capturas. Atualize o status de R21 somente após comprovar a regra e o bloqueio. Não use bypass para integrar um commit reprovado.

### E. Finalização do envio

Com a prova acima preservada, grave pessoalmente, publique como **não listado** no YouTube e teste o link sem login. Acrescente o link à entrega. Então faça a revisão final e gere `Hebert_almeida_DR2_AT.ZIP` conforme a seção 7. O vídeo pessoal e o ZIP final não foram produzidos por este roteiro.

## 1. O que vale mostrar em cinco minutos

Não tentar explicar 13 exercícios em ordem, abrir todos os arquivos ou aguardar scans completos durante o vídeo. Priorizar uma sequência que mostre a aplicação funcionando e justifique decisões:

1. Contexto e organização modular — Ex1–5, aproximadamente 30s.
2. Autenticação, autorização, saída e validação com respostas reais — Ex2/6/9/10/11, aproximadamente 80s.
3. Integração M2M — Ex7, 20s, mostrando Client Credentials, scope mínimo e negação de acesso clínico.
4. Critério do security gate e CVSS/impacto de negócio — Ex12, aproximadamente 75s.
5. ZAP, rastreabilidade, mocks/OpenAPI e decisão residual — Ex13, aproximadamente 75s.

Os trechos indispensáveis são o critério do gate e as decisões do capstone, explicitamente destacados no formato de entrega. A quantidade de telas não é o objetivo: cada tela deve comprovar a fala correspondente.

## 2. Preparação fora da gravação

### 2.1 Organizar as janelas

Deixar prontas três janelas: editor com o projeto e arquivos selecionados; terminal com o ensaio HTTP; navegador com a API/agenda e Actions do repositório próprio. Usar fonte legível e tamanho suficiente para mostrar respostas. Fazer um teste de áudio de dez segundos e reproduzi-lo antes de gravar.

Fechar mensagens pessoais, notificações e abas alheias. Não mostrar `.env`, senhas, access tokens, cookies, OTP ou cabeçalho Authorization. Dados do cenário abaixo são fictícios. O script de ensaio oculta as credenciais e imprime somente resultados selecionados.

### 2.2 Abrir o projeto e conferir o Python

No **Terminal A / PowerShell**:

```powershell
Set-Location 'C:\Dev\Infnet\Desenvolvimento Seguro de Aplicações Web\Assessment'
$pythonAT = Join-Path (Get-Location) '.venv\Scripts\python.exe'
& $pythonAT --version
& $pythonAT -m pip check
```

Não é necessário ativar o ambiente: chamar seu executável evita alterar a política de execução do PowerShell. O projeto mantém Python 3.12; a versão do starter comparativo não é uma exigência adicional do enunciado. Os comandos abaixo usam o ambiente `.venv` que estiver efetivamente validado; não substituir bibliotecas durante a gravação.

### 2.3 Criar um banco exclusivo para o vídeo

Ainda no Terminal A:

```powershell
$idEnsaioAT = [guid]::NewGuid().ToString('N')
$env:DATABASE_URL = "sqlite:///./data/video_$idEnsaioAT.db"
$env:MFA_SIMULATED = 'false'
$env:COOKIE_SECURE = 'false'
```

Esse banco é novo a cada preparação e contém somente dados fictícios. Não reutilizar um banco com dados reais, não apagar bancos anteriores e não colocá-lo no ZIP. `COOKIE_SECURE=false` é uma exceção **somente para a demonstração HTTP em 127.0.0.1**, necessária se for abrir a agenda por cookie. O padrão da aplicação continua seguro; produção exige HTTPS e cookie Secure. Essas variáveis duram apenas nessa sessão de terminal.

### 2.4 Provisionar os dois profissionais de demonstração

Executar no mesmo Terminal A:

```powershell
& $pythonAT -m app.auth.provision video_prof1 --papel profissional --profissional-id 901 --paciente-id 9001
& $pythonAT -m app.auth.provision video_prof2 --papel profissional --profissional-id 902 --paciente-id 9002
```

Para cada conta, digitar e confirmar uma senha **nova e exclusiva da demonstração**, com pelo menos 12 caracteres e até 72 bytes UTF-8. O programa lê sem eco. Não reutilizar senha pessoal e não colocá-la no comando, no roteiro ou em um print.

Opcionalmente, para mostrar a agenda mínima da recepção:

```powershell
& $pythonAT -m app.auth.provision video_recepcao --papel recepcionista
```

Resultados esperados: confirmação de criação sem imprimir senha. Os pacientes 9001/9002 são identificadores de vínculo na implementação atual; **não existe cadastro completo de Patient**. Não descrever esse provisionamento como criação de prontuário ou cadastro clínico completo.

### 2.5 Preparar o laboratório parceiro e iniciar a aplicação

Antes do Uvicorn, no Terminal A e no mesmo banco fictício, provisionar o laboratório e uma oferta futura. Usar segredo novo e exclusivo de demonstração, digitado sem eco:

```powershell
& $pythonAT -m app.auth.provision_m2m client laboratorio_demo --profissional-id 901
$ofertaVideoAT = (Get-Date).ToUniversalTime().AddDays(2).ToString('yyyy-MM-ddT14:00:00+00:00')
& $pythonAT -m app.auth.provision_m2m slot --profissional-id 901 --inicio $ofertaVideoAT
$ofertaVideoAT.Substring(0,10)
```

Anotar somente o dia UTC mostrado, para o Terminal C. A oferta explícita não contém paciente e estará em dia diferente da consulta criada no ensaio humano.

No Terminal A, mantendo as mesmas variáveis:

```powershell
& $pythonAT -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

Deixar esse terminal ativo. Não usar `--reload` na gravação: reiniciar o processo pode trocar a chave efêmera e invalidar sessões. Abrir manualmente `http://127.0.0.1:8000/health` e `/docs`. A ausência de HTTPS local é esperada; não contornar avisos de certificado ou expor o servidor em `0.0.0.0` para gravar.

Swagger, Authorize/Try it out, respostas 201/200/404/403/422 e agenda sob CSP foram observados no navegador em 02–03/10/2026. As capturas reais estão em `evidencias/capturas_2026-10-02` e `evidencias/capturas_2026-10-03`. Repita o ensaio na sua sessão antes de gravar: essas capturas registram aquela execução, não substituem a demonstração ao vivo.

### 2.6 Executar o ensaio HTTP sanitizado

Abrir **Terminal B / PowerShell**:

```powershell
Set-Location 'C:\Dev\Infnet\Desenvolvimento Seguro de Aplicações Web\Assessment'
$pythonAT = Join-Path (Get-Location) '.venv\Scripts\python.exe'
& $pythonAT .\docs\video\demonstrar_api_video.py
```

Se estiver usando os arquivos baixados desta conversa, executar o mesmo script pelo caminho em que foi salvo. Ele depende das bibliotecas já instaladas no ambiente do projeto e acessa somente `http://127.0.0.1:8000`.

Digitar as senhas de `video_prof1` e `video_prof2`. A autenticação ocorre antes da primeira pausa. O script guarda os tokens apenas em memória, sem imprimi-los. **Começar a gravação depois dessa preparação**, deixando o terminal parado na primeira mensagem de ENTER.

| Pausa | O que pressionar/observar | Resultado esperado |
|---|---|---|
| “criar e consultar dado fictício” | ENTER; observar JSON da consulta | POST 201, GET próprio 200, seis campos públicos; sem `criado_em`/`referencia_interna` |
| “ownership e restrição administrativa” | ENTER; observar dois códigos | Outro profissional recebe 404 para o mesmo ID; painel administrativo recebe 403 |
| “entrada, escape HTML e cabeçalhos” | ENTER | Campo `papel` extra recebe 422; agenda 200 contém texto escapado; XFO, XCTO e CSP presentes |

O script cria uma consulta para o dia seguinte em UTC, preservando microssegundos para reduzir conflitos entre ensaios. A observação é um payload fictício de XSS. Sua presença literal no JSON é esperada; a obrigação de encoding é contextual na saída HTML. O ensaio validado nesta inspeção executou essas chamadas contra Uvicorn real, não somente TestClient.

Depois do ensaio, anotar o ID e a data retornados. Para uma nova gravação, executar o script novamente e usar os valores novos; não presumir que a consulta sempre será ID 1. Se a agenda ultrapassar 50 consultas fictícias no mesmo dia após muitos ensaios, preparar outro banco exclusivo e reiniciar a demonstração.

### 2.7 Verificar a agenda visualmente, se for incluí-la

Fora da gravação, em `/docs`, clicar **Authorize** e usar o esquema **OAuth2PasswordBearer**, com `video_prof1`; deixar `client_id` e `client_secret` vazios. Não usar o fluxo administrativo no diálogo OAuth padrão, pois MFA é um desafio separado.

Após autenticar, executar **POST `/auth/browser-session`** com corpo vazio ou `{}`. Deve retornar **204**. Em uma nova aba da **mesma origem** `127.0.0.1:8000`, abrir `/agenda?dia=AAAA-MM-DD`, usando a data UTC criada pelo ensaio. A agenda deve mostrar o payload como texto, sem popup ou execução. Capturar a página apenas com dados fictícios e sem o painel de requisição/Authorization.

Para verificar a recepção, sair e autenticar `video_recepcao`, criar a sessão de navegador e abrir a mesma agenda: a observação clínica deve ser omitida. Não trocar `127.0.0.1` por `localhost` entre etapas, pois a origem/cookie mudam. Fazer essa operação antes da gravação ou ocultar a área onde o Swagger apresenta comandos com token.

### 2.8 Preparar testes, gate e relatórios antes de gravar

No editor, deixar abertos:

- `app/auth/policies.py`: predicado de ownership compartilhado.
- `app/models/consulta.py`: contratos de entrada/saída.
- `.github/workflows/security.yml` e `security/policy.json`.
- `security/risk-register.json`: CVSS e impacto de negócio.
- `docs/exercicio_13.md`, `docs/Correcoes_Conformidade_2026-10-02.md` e `docs/Exercicio_13_Rastreabilidade_2026-10-02.json`.
- `evidencias/conformidade_2026-10-02/pytest.txt`, `gate.json`, `zap.json` e `openapi-audit.json`.

No **Terminal C**, antes de começar a gravação, executar o cliente M2M e digitar o segredo sem eco. Substituir o dia abaixo pelo dia UTC impresso no provisionamento; deixar parado no ENTER. O cliente autentica antes da pausa, portanto iniciar a gravação até dois minutos após emitir o token, para usá-lo por volta de 1min50s; se atrasar, refazer o cliente antes de gravar.

```powershell
Set-Location 'C:\Dev\Infnet\Desenvolvimento Seguro de Aplicações Web\Assessment'
.\.venv\Scripts\python.exe .\docs\video\demonstrar_m2m_video.py --dia AAAA-MM-DD
```

Esperado após ENTER: disponibilidade 200 somente com profissional/início e tentativa de `/consultas` com o mesmo token retornando 401. Nenhum token é impresso.

Para refazer toda a rodada, **antes de gravar**, com Java 21 e rede disponíveis:

```powershell
& $pythonAT -m scripts.run_checks
& $pythonAT -m scripts.audit_openapi
& $pythonAT -m scripts.fetch_zap
& $pythonAT -m scripts.run_dast --zap-home .cache/security-tools/ZAP_2.17.0
& $pythonAT -m scripts.security_gate --reports reports
```

O comando `run_checks` remove resultados temporários anteriores, inclusive ZAP; por isso o scan deve vir depois. A suíte desta inspeção levou aproximadamente quatro minutos e o scan também demanda tempo: mostrar os resultados já produzidos, com sua data, e executar somente a demonstração curta durante o vídeo.

Não chamar resultado sintético do teste do gate de scan real. Os testes de gate usam fixtures para provar bloqueios; o `zap.json` real vem da execução do ZAP. Se o código mudar após a rodada, gerar novas evidências e atualizar os números.

## 3. Sequência cronometrada e falas sugeridas

As falas abaixo descrevem a versão efetivamente inspecionada. Reformular naturalmente; não ler todos os nomes de arquivos em voz alta. Praticar uma vez com cronômetro e cortar pausas longas, preservando explicações de gate e capstone.

| Tempo | Tela e ação | Fala sugerida |
|---|---|---|
| **0:00–0:25** | Editor: árvore `app/`, depois DFD/ameaça TH-02 | “Sou Hebert Almeida. Este Assessment implementa uma API de agendamento clínico com FastAPI. Separei rotas, modelos, banco e autenticação. A análise CIA e o threat model orientaram os controles, principalmente a proteção dos vínculos entre profissionais e pacientes.” |
| **0:25–0:55** | Terminal B: primeiro ENTER; destacar 201/200 e JSON | “A aplicação está rodando localmente com dados fictícios. Esta conta profissional cria e consulta um recurso autorizado. A senha é protegida por bcrypt, e o JWT tem expiração e sessão revogável. O response model limita os campos públicos e exclui os metadados internos.” |
| **0:55–1:25** | Segundo ENTER; destacar 404/403; abrir `policies.py` | “RBAC define o tipo de ação, e ownership limita o recurso. Outro profissional, mesmo autenticado, recebe 404 para esta consulta. A conta também recebe 403 ao tentar a área administrativa. Centralizei o predicado para que listas, detalhes e agenda não tenham políticas divergentes.” |
| **1:25–1:50** | Terceiro ENTER; 422 e escape; agenda visual se já verificada | “Campos não declarados são rejeitados. O payload de observação permanece dado e é escapado no HTML pelo Jinja2. CORS usa origens explícitas e há limites distintos para login. O banco usa SQLModel, sessões injetadas e consultas parametrizadas.” |
| **1:50–2:10** | Terminal C: ENTER; disponibilidade e acesso clínico negado | “O laboratório usa Client Credentials, sem conta humana. O token tem audience própria, duração de cinco minutos e scope de disponibilidade. A resposta contém apenas profissional e início; esse mesmo token não acessa consultas clínicas.” |
| **2:10–3:20** | Workflow → política → CVSS → resultado do gate | “No desenvolvimento e no pull request, pytest verifica comportamentos e Bandit faz análise estática. O pip-audit consulta vulnerabilidades de dependências. Com a API em execução, o ZAP faz análise dinâmica passiva. IAST foi posicionado para homologação, mas não foi executado. O gate bloqueia controle obrigatório reprovado, evidência ausente, achados altos e médios sem triagem e vulnerabilidades Python detectadas. CVSS representa gravidade técnica; impacto de negócio orienta prioridade. Por envolver dados de saúde, uma falha de autorização bloqueia mesmo sem alerta do scanner. O gate passou na main no GitHub. No PR de demonstração, um teste sentinela falhou e o gate reprovou. A regra exige esse check também dos administradores. O merge ficou desabilitado na reprovação e foi habilitado após a correção e a nova execução aprovada.” |
| **3:20–4:15** | `zap.json`, comparação histórica e linha TH-07 da rastreabilidade | “O scan passivo observou doze respostas, incluindo a integração M2M. Havia sete registros no Exercício 12; após CSP central, Swagger local e SRI, restaram dois informativos. Um identifica aplicação JavaScript; o outro sinaliza atributo controlável na agenda, analisado junto da validação e do escape. O relatório relaciona ameaça, controle, teste e evidência. Um laboratório reconstruído compara BOLA e XSS antes e depois, sem expor rotas vulneráveis na aplicação.” |
| **4:15–4:40** | Resumo pytest/OpenAPI e riscos residuais | “Nesta versão, 226 testes e 74 verificações OpenAPI passaram, incluindo mocks de sucesso, entrada e autorização. Isso não comprova ausência de todas as falhas. O scan tem corpus limitado e não avalia TLS real. A decisão é permitir a demonstração local e bloquear produção até resolver os riscos residuais.” |
| **4:40–4:50** | Relatório de inspeção, pendências visíveis | “A entrega documenta o que foi comprovado e o que falta. O código, a rastreabilidade e as evidências permitem reproduzir essa avaliação.” |

**R21 encerrada:** use a execução negativa 37095705289 e positiva 37120246049, com as capturas do botão bloqueado e liberado. Se o PR já estiver integrado, apresente essas capturas como registro histórico datado e abra os links reais das execuções. A conclusão deve corresponder ao estado real. A duração proposta é 4min50s; ensaiar com cronômetro e falar naturalmente.

## 4. Como explicar as decisões sem decorar

| Pergunta que sua fala deve responder | Resposta curta a compreender |
|---|---|
| Por que autenticação não basta? | Um usuário pode ser válido e ainda não ter permissão para o recurso de outro profissional |
| Por que usar 404 no recurso alheio? | Evita confirmar sua existência ao usuário não autorizado; papel sem acesso à ação pode receber 403 |
| Por que `extra='forbid'`? | Impede aceitar silenciosamente propriedades que o contrato não permite, como auditoria/papel |
| Por que manter o texto de XSS no JSON? | JSON e HTML têm contextos diferentes. Ao renderizar HTML, Jinja2 codifica caracteres para que o conteúdo não vire markup executável |
| Por que não basta “CVSS maior que 7”? | Regressão de ownership, ausência de evidência e impacto de dados de saúde também precisam bloquear; CVSS não mede todo o risco de negócio |
| Por que o gate aprovado não libera produção? | Ele cobre controles automatizados; integração contratual, infraestrutura, backups e operação exigem outras evidências |
| Por que os dois informativos não foram escondidos? | Precisam de interpretação e limites claros; informativo não é sinônimo de exploração comprovada nem de irrelevância permanente |
| Por que não copiar as permissões do starter? | O Exercício 6 explicitamente autoriza profissionais; a política foi adaptada ao requisito específico, que conflita com o exemplo |

## 5. Capturas de evidência a preparar

Salvar em pasta própria de evidências, com data e descrição. Capturas devem ser **reais**, sem montar respostas ou trocar códigos manualmente.

| Arquivo sugerido | Conteúdo |
|---|---|
| `01_estrutura_e_ambiente.png` | Árvore modular e versão Python efetivamente validada |
| `02_consulta_201_200.png` | Criação/leitura e contrato público, sem Authorization |
| `03_ownership_404_admin_403.png` | Negações obtidas com contas distintas |
| `04_validacao_422.png` | Campo extra rejeitado |
| `05_agenda_escape.png` | Página com conteúdo fictício tratado como texto; sem script executando |
| `06_testes.png` | Resultado atual da suíte e comando/data |
| `07_gate_local.png` | Gate real aprovado e política correspondente |
| `08_zap_e_rastreabilidade.png` | Alertas reais e linha de rastreabilidade |
| `09_actions_merge_bloqueado.png` | Ver capturas reais 06/07/14 em evidencias/capturas_2026-10-03 |
| `10_m2m_disponibilidade.png` | Scope/TTL, disponibilidade mínima e rota clínica negada, sem JWT |

Não fotografar login, OTP ou painel do Swagger com token em comando curl. O cliente de ensaio já evita imprimir esses valores. Captura de teste sintético deve ser rotulada como teste do gate, não como finding real.

## 6. Problemas comuns no ensaio

| Sintoma | Verificação segura |
|---|---|
| Conexão recusada | Confirmar Terminal A ativo em `127.0.0.1:8000`; não alterar firewall ou expor a API publicamente |
| Login 401 | Conferir conta/senha e se o servidor usa o mesmo DATABASE_URL do provisionamento; não imprimir token para depurar |
| Login 429 | Parar as tentativas e aguardar a janela indicada; não desabilitar rate limiting para a apresentação |
| Token deixa de funcionar | Reinício pode trocar chave efêmera; autenticar novamente. Não usar reload durante a gravação |
| POST retorna 403 | Conferir profissional 901 e paciente 9001 vinculados a `video_prof1`; não trocar a política para “liberar tudo” |
| Agenda abre com 401 | Cookie não foi criado, origem mudou, sessão expirou ou Secure está ativo sobre HTTP local; seguir a preparação fictícia e mesma origem |
| Swagger fica vazio | Verificar localmente carregamento de assets/CSP; resolver antes de gravar, sem desabilitar CSP para simular sucesso |
| Relatório ZAP ausente | Executar ZAP após `run_checks`; não copiar silenciosamente resultado antigo para fazer o gate passar |
| Demora maior que o vídeo | Preparar scans/testes antes; durante a gravação executar somente o ensaio HTTP curto |

## 7. Revisão e publicação pelo aluno

Antes de publicar: duração menor que cinco minutos; áudio compreensível; texto legível; API realmente rodando; gate e capstone explicados; limitações coerentes; nenhum segredo visível; nenhuma afirmação de funcionalidade ausente.

Publicar no YouTube com visibilidade **não listado** e testar o link em janela sem login. Registrar esse link na entrega. Não usar “privado”, porque isso pode impedir o professor de assistir. Confirmar novamente a duração depois da edição.

Após resolver as pendências e acrescentar vídeo/prints: revisar os arquivos e gerar **`Hebert_almeida_DR2_AT.ZIP`**. Incluir código completo, requirements, `.env.example`, workflow, relatórios, rastreabilidade, evidências e link. Excluir `.env` real, ambientes virtuais, bancos/arquivos WAL, caches, ferramentas baixadas e credenciais. O código e a prova foram publicados no GitHub; o ZIP final e o vídeo pessoal ainda não foram produzidos.

Ao terminar o ensaio, parar o Uvicorn com Ctrl+C e fechar os terminais de demonstração. As variáveis locais e o banco de ensaio não devem ser promovidos para produção.
