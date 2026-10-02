# Exercício 11 — Persistência segura

**Hebert Almeida — Desenvolvimento Seguro de Aplicações Web**  
Data: 25/09/2026.

## Situação inicial e resultado

A aplicação já utilizava SQLModel e SQLite em arquivo desde a fundação. O banco em memória é usado para isolamento dos testes; não havia uma lista em memória a migrar nesta etapa. Este exercício consolida a configuração, a dependência de sessão e as evidências de persistência e parametrização. Não alegamos uma migração inédita nem suporte a PostgreSQL.

SQLite é o banco relacional adotado, com armazenamento durável no arquivo configurado por DATABASE_URL. A escolha preserva os controles transacionais, o índice parcial de conflitos de agenda e os triggers de auditoria já implementados. Migrar para outro SGBD exigiria adaptar e validar esses controles. Drivers e backends não suportados agora são rejeitados antes de carregar drivers ou conectar ao banco.

## Configuração externa e proteção de informações

`app/core/config.py` usa BaseSettings para carregar `.env` na raiz do projeto. Variáveis do ambiente prevalecem sobre valores do arquivo; parâmetros explicitamente passados ao construir Settings têm precedência maior. O campo `database_url` agora usa SecretStr para ocultar seu conteúdo na representação e na serialização JSON usual. A string é extraída somente em `build_engine`. Erros de parsing da URL têm mensagem genérica, sem o valor recebido. `hide_input_in_errors=True` reduz a exposição na representação textual de erros Pydantic; não autoriza registrar indiscriminadamente `errors()` ou outros objetos internos.

O engine utiliza `echo=False` e `hide_parameters=True`. O segundo evita exibir parâmetros em representações de erros SQLAlchemy e no logging padrão do engine, mas não torna seguro registrar arbitrariamente requisições, SQL literal, objetos de exceção ou configuração.

SQLite local não utiliza usuário/senha de banco: o arquivo e suas permissões de acesso são o recurso protegido. Não inventamos credenciais para simular esse requisito. Não há credencial de banco hardcoded. `.env.example` contém apenas configuração sem segredos; `.env`, bancos e ambientes virtuais ficam fora da entrega. SecretStr mascara representações, sem criptografar arquivo ou memória. ACLs do sistema operacional, backups e criptografia em repouso exigem configuração de implantação.

Para preparar o ambiente local na raiz do Assessment, criar `.env` a partir de `.env.example` **somente se `.env` ainda não existir**, preservando qualquer configuração local anterior:

```powershell
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
New-Item -ItemType Directory -Path data -Force | Out-Null
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

O exemplo mantém `DATABASE_URL=sqlite:///./data/clinica_exercicio09.db`, compatível com a etapa anterior. Não foi criado `.env` permanente por esta entrega. Os testes criam e removem seu próprio arquivo temporário sem credenciais reais, demonstrando a leitura efetiva.

Caminhos relativos do banco agora são resolvidos a partir da raiz do projeto, mesmo quando o processo inicia em outro diretório. Antes, dependiam do diretório corrente. Nenhum banco antigo é movido ou apagado: quem iniciava o comando em outro diretório deve conferir o caminho e configurar um caminho absoluto para preservar o banco desejado. O diretório pai deve existir e ter permissões apropriadas. URLs em memória são preservadas quando explicitamente usadas por testes; o padrão e o exemplo usam arquivo. URLs com parâmetros de query ou URI `file:` são rejeitadas para não alterar implicitamente o modo de conexão.

## Sessões e transações

`app/database/session.py` concentra `get_session` e a definição única de `SessionDep = Annotated[Session, Depends(get_session)]`. Consultas, agenda e autenticação reutilizam essa dependência. FastAPI gerencia o ciclo de vida; o bloco `with Session(...)` fecha a sessão ao terminar a requisição e desfaz transação ainda não confirmada. O teste provoca uma exceção depois de `flush` e comprova que a linha não persiste e `close` foi chamado.

Os serviços mantêm commits explícitos nos limites das operações. Criar/alterar/excluir consulta e registrar a auditoria correspondente continuam na mesma transação. Sessões curtas próprias do middleware de autenticação e auditoria são necessárias porque middlewares não recebem automaticamente dependências de rota; todas usam o engine da aplicação e context managers, sem sessão global compartilhada. O engine criado pela factory é descartado no encerramento; um engine injetado continua sob responsabilidade de quem o forneceu.

## Queries parametrizadas

Consultas usam `select`, filtros `where`, operações SQLModel e expressões SQLAlchemy. Ownership é aplicado na própria seleção. IDs, username, datas, observações e limites são valores vinculados; não são interpolados no texto SQL. A revisão incluiu consultas, agenda, autenticação/MFA, provisionamento, limites e auditoria.

As duas chamadas `text(...)` de criação dos triggers contêm somente DDL constante, sem entrada de usuário. A concatenação de literais pelo Python nesses comandos não monta uma query com dados recebidos. Os nomes das tabelas, colunas e ordenação são definidos pelo código, não pelo cliente.

O teste injeta o payload fictício `x'); DROP TABLE consulta; --` em observação, cria e atualiza uma consulta e confirma que a tabela continua acessível. Um listener `before_cursor_execute` verifica o comando e os parâmetros separados no driver: INSERT e UPDATE da consulta e SELECT de usuário contêm placeholders `?`, enquanto o payload aparece somente nos parâmetros. O SELECT por username malicioso retorna lista vazia. Esse SELECT é uma sondagem direta da camada de dados; a rota de login também possui validação de username que rejeitaria esse formato antes do banco.

## Evidências e reprodução

Validação final: **127 testes aprovados**, incluindo os 13 novos; Ruff aprovado e 38 arquivos com formatação aprovada. A suíte completa foi executada novamente depois da correção solicitada pelo Astra.

Os 13 casos novos de `tests/test_exercicio11.py` verificam:

- Duas instâncias da aplicação com engines distintos acessando o mesmo arquivo SQLite: consulta criada na primeira é lida na segunda após nova autenticação. O token antigo é rejeitado porque a chave JWT efêmera muda.
- Leitura de `.env`, precedência do ambiente e ocultação da URL nas representações usuais.
- Preservação explícita das URLs em memória e rejeição sanitizada de URLs não suportadas.
- Estabilidade do caminho ao mudar de diretório e configuração de logs sem parâmetros.
- INSERT/UPDATE/SELECT parametrizados, rollback e fechamento da dependência.

Na raiz do projeto:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider
.\.venv\Scripts\python.exe -m pytest -v -p no:cacheprovider tests/test_exercicio11.py
.\.venv\Scripts\python.exe -m ruff check --no-cache app tests
.\.venv\Scripts\python.exe -m ruff format --check --no-cache app tests
```

Os testes usam dados fictícios e diretórios exclusivos; o teste de disco remove somente seus arquivos conhecidos depois de fechar os engines. Uma fixture isola variáveis de Settings e o caminho do engine é conferido antes de inserir dados, evitando herdar DATABASE_URL do ambiente. Isso foi verificado também com DATABASE_URL e JWT_SECRET fictícios exportados. O banco de demonstração não é alterado. Logs integrais, resultado final e hashes das alterações estão em `evidencias/exercicio_11`. A revisão independente está em `docs/revisao_astra_exercicio_11.md`. Dois avisos preexistentes do TestClient/httpx e BlockingPortal não representam falhas de teste.

| Requisito | Entrega verificável |
|---|---|
| Persistência SQLModel relacional | Consulta recuperada de arquivo SQLite após encerrar e recriar a aplicação |
| Queries parametrizadas | Captura no driver de INSERT, UPDATE e SELECT com payload separado |
| Sessão por DI | Definição central, consumo nas rotas, rollback e fechamento testados |
| BaseSettings e `.env` | Arquivo temporário efetivamente carregado, precedência e `.env.example` sem segredos |

Não há migração de esquema nesta etapa. `create_all` não substitui ferramenta de migração de versões; bancos anteriores ao Exercício 9 seguem exigindo a revisão já documentada. Testes de persistência local não comprovam backups, recuperação após falha de disco, isolamento de produção ou suporte a outro SGBD. Prints e gravação pessoal permanecem pendentes. ZIP somente ao final.

## Roteiro opcional — 20 segundos no vídeo único

Mostrar `get_session` e um filtro SQLModel: “A sessão é injetada por requisição e os valores entram como parâmetros, sem concatenar SQL.” Mostrar o teste de persistência: “Criei a consulta, encerrei a aplicação e recuperei o mesmo registro do arquivo SQLite.” Encerrar em `.env.example`: “A conexão vem da configuração externa; o pacote não inclui `.env` real ou banco.” Reservar o tempo principal do vídeo de até cinco minutos para as decisões dos Exercícios 12 e 13.

## Referências

- [SQLModel — sessão com dependência FastAPI](https://sqlmodel.tiangolo.com/tutorial/fastapi/session-with-dependency/).
- [Pydantic Settings — fontes e precedência](https://docs.pydantic.dev/latest/concepts/pydantic_settings/).
- [SQLAlchemy — configuração do engine e ocultação de parâmetros](https://docs.sqlalchemy.org/en/20/core/engines.html#hiding-parameters).
