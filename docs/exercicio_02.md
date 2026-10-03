> Registro técnico da etapa indicada. Para resultados atuais e alterações posteriores, consulte o [índice de documentação](README.md).

# Exercício 2 — Controle de exposição de dados e templates seguros

## Resultado
A API de consultas mantém uma lista explícita de seis campos públicos. Dois campos internos de auditoria são persistidos, mas não são enviados ao cliente nem ao template. A página GET /agenda mostra as consultas do dia em UTC, com filtro de data e paginação, usando Jinja2 e herança de templates.

## Campos e responsabilidades
| Campo | Entrada POST/PUT | JSON de saída | HTML da agenda | Banco |
|---|---|---|---|---|
| id | Não | Sim | Sim | Gerado pelo banco |
| paciente_id | Sim | Sim | Sim | Sim |
| profissional_id | Sim | Sim | Sim | Sim |
| data_hora | Sim, com fuso | Sim, UTC | Horário UTC | Sim |
| status | Sim | Sim | Sim | Sim |
| observacao | Sim, até 500 caracteres | Sim | Texto com escape HTML | Sim |
| criado_em | Não | Não | Não | Gerado pelo servidor |
| referencia_interna | Não | Não | Não | UUID gerado pelo servidor |

A observação é operacional, por exemplo “Chegar 15 minutos antes”, e não foi criada para registrar prontuários ou informações clínicas. Todos os dados usados nas evidências são fictícios.

ConsultaWrite valida a entrada com extra="forbid". ConsultaRead declara exatamente os campos públicos e usa from_attributes=True para validar o objeto ORM. A entidade Consulta contém também os campos internos. O cliente não pode definir auditoria no POST/PUT; campos adicionais são rejeitados com 422.

POST, GET por ID, GET da coleção e PUT continuam com response_model explícito. DELETE retorna 204 sem corpo. O OpenAPI contém os contratos públicos, sem expor o modelo de persistência.

## Por que response_model importa
Se uma rota serializar o objeto completo do banco sem um contrato de saída restritivo, campos internos atuais ou acrescentados no futuro podem passar a aparecer no JSON. Neste projeto, isso exporia criado_em e referencia_interna. A referência interna permite correlacionar registros com outros sistemas ou logs, algo que não faz parte do contrato público da consulta.

A proteção vem da lista de campos do modelo de saída e do response_model aplicado às rotas. O extra="forbid" da entrada tem outra função: recusar campos não declarados enviados pelo cliente. Não é ele que substitui o controle de saída.

response_model também não substitui autenticação ou autorização: os IDs públicos ainda exigirão regras de acesso nos exercícios correspondentes.

## Página da recepção
- URL: /agenda; sem filtro, usa a data atual em UTC.
- Filtro: /agenda?dia=2030-10-15.
- Paginação: 50 registros por página, com navegação anterior/próxima.
- Consulta parametrizada: intervalo [00:00 UTC do dia, 00:00 UTC do dia seguinte), ordenado por horário e ID.
- O fuso UTC está indicado na interface. É a convenção desta etapa, não uma inferência sobre o fuso de todas as clínicas.
- base.html contém documento HTML, cabeçalho, CSS e rodapé.
- agenda.html usa extends "base.html" e sobrescreve title e content.
- CSS externo em app/static/agenda.css; não há JavaScript na página.
- Cache-Control: no-store evita o armazenamento deliberado da resposta pelo cache HTTP.

Antes de renderizar, a rota projeta os resultados em ConsultaRead. O template recebe apenas esses modelos públicos, sem acesso ao objeto ORM completo e à auditoria.

## Defesa contra XSS persistido
O ambiente Jinja2 é configurado centralmente em app/core/templates.py com select_autoescape, habilitado também por padrão, e StrictUndefined. A observação aparece somente no contexto de texto de uma célula: {{ consulta.observacao }}.

Não são usados filtro safe, Markup para dados de usuário, concatenação de HTML, eventos inline ou interpolação de texto de usuário em JavaScript. O texto armazenado não é usado como fonte de template.

O payload <script>alert("XSS")</script> é aceito como texto de observação e persistido. Na resposta HTML, os delimitadores aparecem codificados, como &lt;script&gt;. O navegador mostra o conteúdo literal e não cria um elemento script. O mesmo vale para <img src=x onerror="alert(1)">.

O escape é feito na saída HTML, preservando o conteúdo original no banco e no JSON. JSON não precisa virar HTML escapado: um frontend que consuma esse JSON deverá inserir o texto com APIs seguras, como textContent, e não innerHTML. Autoescape protege o contexto usado aqui; não remove confidencialidade de dados e não é uma autorização de acesso.

## Testes e evidências
Suíte completa: 39 testes aprovados, sendo 23 da fundação adaptados ao novo campo público e 16 casos novos.

Os novos testes cobrem:
- existência da auditoria no banco e omissão em POST, GET individual, listagem e PUT;
- rejeição de auditoria enviada pelo cliente;
- omissão da auditoria tanto no HTML final quanto no contexto entregue ao template;
- persistência e renderização de quatro payloads, incluindo script, imagem com onerror, SVG e texto parecido com expressão Jinja;
- ausência de novos elementos executáveis e atributos de evento no HTML;
- agenda do dia padrão, limites de meia-noite em UTC e ordenação;
- herança de template, lista vazia, paginação e parâmetros inválidos;
- campos públicos exatos no OpenAPI e limite da observação.

Verificação adicional com Uvicorn em 127.0.0.1:8765:
- três consultas fictícias criadas com HTTP 201;
- auditoria existente na entidade e ausente na resposta pública;
- agenda com HTTP 200 e payloads escapados;
- inspeção do DOM real: três linhas, zero elementos script, zero elementos img e nenhum atributo de evento inline.

Arquivos em evidencias/exercicio_02:
- pytest.txt e pytest.xml: execução dos testes;
- payloads.json: entradas usadas na demonstração;
- http_exposicao_xss.json: respostas reais e comparação com o registro interno fictício;
- agenda_renderizada.html: HTML real retornado pelo servidor (o CSS depende do servidor local);
- navegador_dom.json: inspeção real do navegador;
- openapi.json: contrato vigente;
- qualidade.json: verificações de dependências e Ruff.

A captura PNG do navegador falhou por timeout, como na etapa anterior. O print permanece pendente; o HTML e o DOM não são apresentados como substitutos de um print. Não foi fabricada uma imagem de evidência.

Permanecem dois avisos de depreciação de dependências no pytest; estão preservados no log. Não houve falhas.

## Validação e limite de migração
A suíte desta etapa registrou 39 testes aprovados para os cenários exercitados. Isso não comprova ausência de todas as vulnerabilidades.

`create_all` cria tabelas, mas não altera tabelas existentes; a preparação de bancos antigos exige migração explícita.

## Banco e compatibilidade
O esquema agora tem três colunas adicionais: observacao, criado_em e referencia_interna. No início deste exercício não existia data/clinica.db. A demonstração usou .cache/exercicio02_demo.db, preservando o banco de demonstração anterior.

Caso você tenha criado um banco no Exercício 1, não o apague nem espere que create_all faça uma migração. Para testar esta etapa com um banco novo e manter o anterior:
```powershell
$env:DATABASE_URL = "sqlite:///./data/clinica_exercicio02.db"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```
Use esse nome apenas se ainda não contiver um esquema antigo. A variável vale para o terminal atual. Evolução com reaproveitamento de dados exige uma migração explícita, ainda não implementada.

## Rastreabilidade da rubrica
| Item | Implementação | Evidência |
|---|---|---|
| Controlar campos expostos com response_model | ConsultaRead nas quatro operações com corpo | teste de campos exatos, auditoria interna e OpenAPI |
| Justificar risco sem response_model | seção de exposição acima | comparação banco versus resposta em http_exposicao_xss.json |
| Jinja2 com herança e autoescape | core/templates.py, base.html e agenda.html | testes de herança e payloads persistidos, HTML e DOM reais |

## Limites
A página é destinada à recepção, mas autenticação e restrição por papel ainda não foram implementadas. Não é uma página “interna protegida” apenas por estar em /agenda. Usar localmente e somente com dados fictícios até os exercícios de acesso.

Os riscos já documentados na fundação (ownership, existência de pacientes/profissionais e conflitos de agenda) continuam fora do escopo desta etapa. Não foi afirmada conformidade integral com LGPD.

## Fontes técnicas
- [FastAPI — response_model e filtragem de saída](https://fastapi.tiangolo.com/tutorial/response-model/)
- [Starlette — templates e autoescape](https://www.starlette.io/templates/)
- [Jinja2 — herança e escape](https://jinja.palletsprojects.com/en/stable/templates/)
