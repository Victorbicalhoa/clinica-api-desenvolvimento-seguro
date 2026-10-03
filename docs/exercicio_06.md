> Registro técnico da etapa indicada. Para resultados atuais e alterações posteriores, consulte o [índice de documentação](README.md).

# Exercício 6 — Autenticação e autorização

**Autor:** Hebert Almeida · **Data:** 22/09/2026

## Decisão de autorização

Foi adotado **RBAC combinado com autorização por recurso**. RBAC determina as operações de cada papel; o vínculo persistido determina quais pacientes e consultas um profissional pode acessar. RBAC isolado permitiria a qualquer profissional acessar consultas de outro. ABAC completo permitiria regras contextuais adicionais, mas acrescentaria complexidade sem atributos de clínica, turno ou localização definidos nesta etapa.

| Operação | Profissional | Recepcionista | Administrador |
|---|---|---|---|
| POST/GET/PUT/DELETE de consultas | Somente profissional_id da própria conta e paciente vinculado | Negado | Negado |
| Lista JSON de consultas | Filtrada pelos dois vínculos | Negado | Negado |
| Agenda HTML | Somente consultas dentro dos próprios vínculos | Agenda operacional, sem observacao | Negado |
| GET /admin/painel | 403 | 403 | Permitido após MFA simulado |
| Logout da própria sessão | Permitido | Permitido | Permitido |

O requisito “apenas profissionais de saúde” foi aplicado também aos administradores: administrar o sistema não concede poder clínico implícito. A recepção acessa IDs, horário e status para operar a agenda; o texto livre é retirado do contexto do template. Como ainda não existe entidade clínica/lotação, o papel de recepção abrange a agenda desta instalação. Segregação por unidade requer modelagem posterior e não é alegada como implementada.

`Usuario.profissional_id` é único. `VinculoPaciente` relaciona usuário e paciente com chave composta. Para ler uma consulta, devem coincidir o profissional da conta e o paciente vinculado. A mesma consulta parametrizada protege detalhes, listas e agenda; o filtro ocorre antes da paginação no SQL. POST/PUT validam os vínculos antes de escrever. Trocar profissional_id ou paciente_id no payload não concede permissão. Um ID inexistente ou pertencente a outro profissional retorna o mesmo 404. Papel sem acesso à função retorna 403; ausência ou invalidade de autenticação retorna 401.

Os vínculos são provisionados por operador local confiável; não existe cadastro público que permita escolher papel ou pacientes. Ainda não há cadastro completo de pacientes: o vínculo autoriza um ID, sem comprovar a existência de uma entidade paciente ou substituir regras clínicas de agendamento.

## Autenticação, senhas e sessões

`OAuth2PasswordBearer(tokenUrl="auth/token")` extrai o Bearer e descreve o esquema no OpenAPI. POST `/auth/token` recebe formulário OAuth2 com `grant_type=password`, username e password. A aplicação valida a senha e emite JWT; a dependência isolada não executaria esse trabalho. O fluxo foi implementado para a rubrica e o cliente próprio desta demonstração. Não há provedor OAuth completo ou integração M2M nesta etapa. Referência: [FastAPI — OAuth2 e JWT](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/).

Senhas são armazenadas somente como **bcrypt com salt aleatório e custo 12**, usando bcrypt diretamente. A política exige pelo menos 12 caracteres e no máximo 72 bytes UTF-8, rejeitando entradas maiores sem truncar. O limite é em bytes, não caracteres. O provisionamento usa getpass e confirmação, sem senha nos argumentos do terminal. O login usa mensagem genérica para usuário ausente, senha inválida ou conta desativada, e comparação contra hash fictício quando a conta não existe. Referência do limite: [bcrypt](https://pypi.org/project/bcrypt/).

JWT usa HS256 fixo, sub, jti, iat, nbf, exp, iss, aud e mfa. A assinatura, emissor, audiência e claims obrigatórios são validados; o cliente não escolhe o algoritmo aceito. A validade padrão é de **15 minutos**, configurável entre 1 e 30. Não há refresh token. O token não contém dados de pacientes, observações, senha ou hash. JWT é assinado, não criptografado. Referência: [PyJWT — API de validação](https://pyjwt.readthedocs.io/en/stable/api.html).

Além do JWT, existe sessão persistida com jti, usuário, expiração, estado MFA e revogação. Toda requisição consulta a sessão e a conta atual: logout revoga o jti; desativar a conta bloqueia tokens existentes; promover um usuário não converte token sem MFA em acesso administrativo. Papéis são lidos do banco, não de um campo de entrada ou claim escolhido pelo cliente.

Sem JWT_SECRET configurado, cada processo gera uma chave aleatória em memória. Isso permite demonstração local sem segredo fixo no repositório; reiniciar invalida os tokens daquele processo. Uma implantação com múltiplos workers exigiria chave forte compartilhada, protegida e com rotação planejada. Não há credencial real ou chave de assinatura no pacote.

## MFA simulado

Administradores nunca recebem token somente com senha. Login válido gera desafio de 128 bits e código aleatório de seis dígitos, retornando **202** com challenge_id, sem código e sem access_token. O código expira em 120 segundos e permite no máximo cinco tentativas por desafio. POST `/auth/mfa` recebe challenge_id e code; sucesso consome o desafio e emite sessão com MFA confirmado.

O banco guarda HMAC do código, associado ao desafio, e não o código em texto. UPDATE condicional controla tentativas; consumo e criação da sessão são confirmados na mesma transação. Isso evita que duas confirmações válidas do mesmo desafio criem sessões por uma corrida de leitura seguida de escrita no SQLite. Testes exercitam expiração, limite e replay. Um teste adicional com arquivo SQLite descartável, conexões separadas e duas threads confirmou respostas 200/401 e exatamente uma sessão criada; sua execução está registrada separadamente.

A entrega do código é **simulada no terminal local do servidor**, somente com MFA_SIMULATED=true. O padrão é false e falha fechado para login administrativo. O adaptador é substituído por coletor em memória nos testes. Essa simulação demonstra o fluxo, não prova posse de um segundo fator: alguém com acesso ao terminal pode obter o código. Não coletar essa saída em evidências, logs de produção ou prints. Para uso real, substituir por segundo canal/fator independente, com matrícula, recuperação e política operacional próprias.

## Agenda no navegador

A API de consultas aceita somente Bearer. A agenda aceita Bearer ou cookie de leitura, ambos sujeitos à mesma validação de sessão e às políticas de acesso. POST `/auth/browser-session`, autenticado exclusivamente por Bearer, cria cookie HttpOnly, SameSite=Strict, Path=/agenda e Secure por padrão. Depois disso, a navegação normal para `/agenda` funciona. Tokens não são colocados na URL nem em localStorage.

O cookie não autentica POST, PUT ou DELETE de consultas nem a criação de outra sessão de navegador. Isso evita usar credenciais enviadas automaticamente pelo navegador para as operações de alteração implementadas. Em HTTP local, COOKIE_SECURE=false pode ser definido explicitamente apenas para a demonstração em loopback. O prazo efetivo continua limitado pelo JWT e pela sessão mesmo que o cookie ainda exista. Logout revoga a sessão e remove o cookie.

## Organização e persistência

| Arquivo | Responsabilidade |
|---|---|
| app/auth/security.py | bcrypt, emissão e validação de JWT/sessão |
| app/auth/dependencies.py | Identidade, exigência de papéis e extração de credenciais |
| app/auth/policies.py | Ownership centralizado e autorização dos vínculos na escrita |
| app/auth/provision.py | Provisionamento confiável via CLI, sem cadastro público |
| app/models/usuario.py | Usuário, vínculo, sessão, desafio e contratos Pydantic |
| app/routes/auth.py | Login, confirmação MFA, logout e cookie da agenda |
| app/routes/admin.py | Recurso REST restrito ao administrador |
| tests/test_auth.py | Suíte inicial de autorização e regressões de autenticação |

Os novos modelos são registrados em create_tables. As consultas continuam usando SQLModel/SQLAlchemy com parâmetros, sem concatenação SQL. `create_all` cria as novas tabelas, mas não migra esquemas antigos: use banco novo para a demonstração e preserve o banco anterior. A autenticação não permite transformar consultas antigas em recursos próprios sem provisionamento explícito de identidade e vínculo.

## Reprodução local

Na raiz do projeto, instale as dependências do requirements.txt no ambiente virtual. Para uma demonstração isolada em banco novo, use um nome ainda não utilizado:

```powershell
$env:DATABASE_URL = "sqlite:///./data/clinica_exercicio06.db"
$env:MFA_SIMULATED = "true"
$env:COOKIE_SECURE = "false"
.\.venv\Scripts\python.exe -m app.auth.provision profissional1 --papel profissional --profissional-id 2 --paciente-id 1
.\.venv\Scripts\python.exe -m app.auth.provision profissional2 --papel profissional --profissional-id 4 --paciente-id 100
.\.venv\Scripts\python.exe -m app.auth.provision recepcao --papel recepcionista
.\.venv\Scripts\python.exe -m app.auth.provision admin --papel administrador
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Cada comando de provisionamento solicita uma senha escolhida localmente; os exemplos não definem senha padrão. Abra `/docs`. Um profissional pode usar **Authorize** com username/password. Crie uma consulta com paciente_id=1 e profissional_id=2; autentique profissional2 e confirme que GET do mesmo ID retorna 404. IDs nos exemplos são fictícios.

Para administrador, o fluxo de duas etapas deve ser executado por `/auth/token` e `/auth/mfa`; a janela padrão do Swagger não conclui o desafio MFA automaticamente. Envie grant_type=password no formulário; leia o código simulado no terminal e use-o na confirmação. Utilize o access_token retornado em um cliente HTTP com `Authorization: Bearer <token>` para GET `/admin/painel`. Não salve token/código em arquivos ou no roteiro.

Para a recepção, use Authorize, execute POST `/auth/browser-session` e abra `/agenda` no mesmo navegador. O cookie funciona em HTTP loopback somente com a configuração local explicitada acima. Sem sessão válida, a agenda retorna 401 e não dados clínicos.

## Verificação e rastreabilidade

O teste solicitado pela tarefa é `test_nao_administrador_impedido_de_acessar_rota_admin`: profissional recebe 403 e administrador que concluiu MFA recebe 200. A suíte também verifica ausência de token em todos os métodos, ownership cruzado, adulteração de vínculos, filtragem de lista/HTML, negação por papel, cookie restrito, JWT inválido/expirado, logout, desativação, MFA expirado/reutilizado e hashing.

Os testes antigos agora autenticam um profissional por login real, sem substituir dependências de segurança. O caso antigo de atualização foi ajustado para manter o profissional, pois transferir ownership deixou de ser operação permitida. Dados da paginação HTML foram associados ao profissional autenticado.

| Threat model do Exercício 4 | Controle nesta etapa | Verificação |
|---|---|---|
| TH-01 / MT-01 / VT-01 | Identidade e sessão obrigatórias | Métodos sem token retornam 401 |
| TH-02 / MT-02 / VT-02 | Ownership central, inclusive lista e agenda | Dois profissionais, dois conjuntos de vínculos; acesso cruzado negado |
| TH-13 / MT-03 / VT-13 | RBAC e MFA administrativo | Não administrador recebe 403; MFA necessário para administrador |
| TH-03, TH-06, TH-07, TH-08 | Contratos, escape e SQL parametrizado preservados | Regressões dos exercícios anteriores |

TH-04 (integridade clínica/conflitos), TH-05 (auditoria de negócio), TH-09 (limites globais), TH-10/11 (arquivo e recuperação), TH-12 (implantação TLS) e TH-14 (M2M) não são declaradas resolvidas. Nenhuma alteração retroativa é feita no snapshot do threat model do Exercício 4; esta tabela registra a evolução. Limites por desafio MFA não substituem rate limiting de login, de novas emissões de desafio ou quotas de sessão. Limpeza de sessões/desafios expirados e limite global de tentativas continuam como evolução. Esta etapa não autoriza exposição pública de dados reais.

Resultados reais de 22/09/2026: **70 testes aprovados em 93,62 s**, mais **1 teste concorrente aprovado em 3,39 s** em execução separada. Cada execução apresenta dois avisos de depreciação das dependências Starlette/httpx e AnyIO, sem falhas. Ruff, verificação de formatação dos 27 arquivos Python e pip check aprovados. A sondagem reproduzível validou **20 cenários HTTP**. Esses resultados estão em `evidencias/exercicio_06`, com requisições sanitizadas e hashes dos arquivos alterados.

Dois problemas foram corrigidos e receberam verificação: uso da configuração injetada de banco pela fábrica da aplicação e tratamento de duplicidade durante o flush do provisionamento. Os dois receberam testes de regressão. Os testes de regressão documentam o comportamento esperado.

Para executar a suíte e a sondagem:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m ruff check --no-cache app tests
.\.venv\Scripts\python.exe -m ruff format --check --no-cache app tests
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe evidencias/exercicio_06/reproduzir.py
```

O teste concorrente cria e remove somente seu banco descartável dentro de `.cache/mfa-test-<UUID>`. Isso evita a ACL restritiva dos diretórios temporários do runner Windows; tentativas iniciais com tmp_path falharam na preparação do ambiente, antes do teste, e não foram contadas como aprovação. A sondagem usa banco em memória. Não executa ações contra data/clinica.db.

Não incluir tokens, códigos MFA ou senhas escolhidas pelo operador nas evidências. As senhas literais da suíte são fictícias e usadas exclusivamente em bancos descartáveis. Capturas de tela da demonstração ainda deverão ser feitas sem credenciais visíveis; a evidência desta etapa consiste em testes e requisições HTTP reais, sem imagens simuladas. ZIP somente ao final.

## Roteiro selecionado para o vídeo — cerca de 55 segundos

**0–15 s:** mostrar app/auth/policies.py e explicar: “Escolhi RBAC para limitar as funções de cada papel, combinado com autorização por recurso. Ser profissional não permite acessar qualquer paciente; o vínculo é consultado no banco.”

**15–35 s:** demonstrar criação com profissional1; autenticar profissional2 e mostrar 404 para o mesmo ID e lista filtrada. Não exibir senhas ou tokens na gravação.

**35–55 s:** mostrar o teste de acesso administrativo: profissional recebe 403; administrador só recebe 200 após o desafio simulado. Explicar: “A senha usa bcrypt, o JWT expira em 15 minutos e o logout revoga a sessão. O código no terminal é apenas uma simulação de MFA.”

Reservar o restante do vídeo para os principais resultados e especialmente as decisões do security gate do Exercício 12 e do capstone do Exercício 13.
