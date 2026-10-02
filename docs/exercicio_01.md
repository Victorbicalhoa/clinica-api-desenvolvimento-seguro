# Exercício 1 — Fundação da API de agendamento

## Objetivo e resultado
A fundação da API foi organizada em módulos e recebeu o CRUD de consultas via APIRouter. O ambiente virtual é próprio do projeto, com Python 3.12.14 e versões fixadas em requirements.txt. O primeiro conjunto de testes usa pytest e TestClient, com banco SQLite em memória independente por teste.

## Organização
- app/main.py: fábrica da aplicação, registro dos routers e ciclo de vida.
- app/routes/consultas.py: operações HTTP do recurso consultas.
- app/models/consulta.py: entidade SQLModel, contratos Pydantic de entrada e saída e enum de status.
- app/database/session.py: engine, criação inicial de tabelas e sessão por requisição.
- app/core/config.py: configuração via BaseSettings.
- app/auth: reservado para centralizar autenticação e autorização nos próximos exercícios.
- tests/conftest.py: fixtures de cliente e dados fictícios.
- tests/test_consultas.py: primeiro arquivo de testes automatizados.

## Contrato REST
| Método | Rota | Resultado esperado |
|---|---|---|
| POST | /consultas | 201, recurso criado e cabeçalho Location |
| GET | /consultas?offset=0&limit=20 | 200, lista ordenada por ID |
| GET | /consultas/{consulta_id} | 200 ou 404 |
| PUT | /consultas/{consulta_id} | 200 ou 404; substituição completa |
| DELETE | /consultas/{consulta_id} | 204 sem corpo ou 404 |

O corpo de entrada contém paciente_id, profissional_id, data_hora e status. Os três primeiros são obrigatórios. Status permite agendada, cancelada e realizada; seu padrão é agendada. PUT exige todos os campos obrigatórios, e omitir status restaura o padrão agendada. Não há atualização parcial nesta etapa.

Exemplo fictício:
```json
{
  "paciente_id": 1,
  "profissional_id": 2,
  "data_hora": "2030-10-15T09:00:00-03:00",
  "status": "agendada"
}
```

A resposta inclui o id gerado pelo banco e normaliza o horário para 2030-10-15T12:00:00Z.

## Decisões técnicas e de segurança
1. Isolamento: .venv evita mistura de dependências com outros projetos; requirements.txt permite recriar o ambiente. Não entregar a .venv no ZIP.
2. Modularização: main registra routers, models define contratos e persistência, database controla sessões. A camada de autenticação permanece separada e ainda sem implementação.
3. Validação: IDs do corpo são inteiros estritos positivos com teto de 2.147.483.647; campos extras e ID fornecido no corpo são recusados com 422. Status usa enum. A data exige fuso e não aceita timestamp numérico.
4. Horários: a entrada é normalizada para UTC. A versão instalada do SQLModel (0.0.46) trata datetime com UTCDateTime, preservando o fuso no retorno do SQLite. Não é necessário retirar tzinfo manualmente. Conversões além dos limites de datetime são recusadas com 422.
5. Respostas: response_model declara os campos expostos; a entidade de persistência e o contrato HTTP são separados para permitir evolução sem exposição automática de novos campos.
6. Persistência: SQLModel usa Session.get, select, add e delete. Valores são vinculados por parâmetros; não há SQL construído por concatenação de entrada. A tabela é criada no lifespan para a fundação local; migrações versionadas serão necessárias caso o esquema evolua sobre bancos existentes.
7. Paginação: listagem padrão de 20, máximo de 100, ordenada por ID. Offset tem limite superior compatível com os IDs adotados para impedir overflow no SQLite.
8. Sessões: cada requisição recebe sessão encerrada por contexto. A fábrica aceita engine injetada para testes isolados; não cria banco no momento do import.
9. Dados mínimos: a consulta armazena IDs, horário e status. Não foram adicionados nome, CPF ou prontuário.
10. Segredos: configuração sem credenciais embutidas; apenas .env.example sem segredos integra o material.

## Validação executada
23 casos pytest aprovados:
- criação com 201 e Location, leitura e equivalência de dados;
- normalização do fuso e roundtrip pelo banco;
- lista inicialmente vazia e paginação;
- atualização persistida e exclusão com 204 sem corpo;
- 404 nos métodos de leitura, atualização e exclusão;
- IDs inválidos, status inválido, datas inválidas ou sem fuso;
- campos extras e tentativa de definir ID no corpo;
- PUT incompleto sem alterar o registro;
- paginação inválida e casos extremos de conversão UTC.

Esses testes integram API, validação e banco em memória; não são testes unitários com mocking. Essa cobertura poderá ser ampliada nos exercícios posteriores.

O CRUD também foi exercitado por HTTP com Uvicorn em 127.0.0.1:8765, usando banco descartável em .cache. Foram observados 201, 200, 204, 404 e 422 nos caminhos correspondentes. pip check, Ruff check e Ruff format --check passaram.

Dois avisos de depreciação vêm das dependências Starlette/httpx e Starlette/AnyIO. Não houve falha nos testes. Os avisos foram preservados no log; não foram ocultados.

## Revisão Astra
Modelo: gpt-6-astra, revisão independente em modo somente leitura.
Dois achados foram corrigidos antes da aprovação:
- offset excessivo causava erro 500: limite superior e teste de regressão;
- conversão de data extrema para UTC causava OverflowError: captura e ValueError, resultando em 422, com testes para os extremos inferior e superior.

Parecer final: aprovado para o escopo do Exercício 1, sem achados pendentes no código. O revisor confirmou os 23 testes aprovados.

## Rastreabilidade
| Requisito | Implementação | Evidência |
|---|---|---|
| Ambiente Python isolado | .venv e requirements.txt | evidencias/exercicio_01/ambiente.json |
| Módulos padrão | app/routes, app/models, app/database | arquivos-fonte e estrutura descrita acima |
| Recurso RESTful completo | router /consultas e registro em main | evidencias/exercicio_01/http_crud.json e openapi.json |
| Teste pytest de sucesso | test_criar_e_buscar_consulta | evidencias/exercicio_01/pytest.txt e pytest.xml |
| Validação explícita e saída controlada | ConsultaWrite e ConsultaRead | testes e contrato OpenAPI |

## Limitações desta etapa
Ainda não há login, verificação de ownership, regras por papel, validação de existência de paciente/profissional, chaves estrangeiras, prevenção de conflito de agenda ou restrição de data passada. As rotas são abertas neste esqueleto; usar somente dados fictícios no ambiente local. Os exercícios futuros deverão implementar os controles de segurança sobre esta base, sem tratar o CRUD inicial como aplicação pronta para dados reais.

DELETE realiza exclusão física, definida aqui para demonstrar CRUD. Política de retenção, cancelamento e trilha de auditoria deverão ser revistas com os requisitos posteriores.

O print do Swagger permanece pendente: a documentação foi aberta e suas rotas verificadas no navegador, mas a ferramenta retornou timeout/falha ao capturar a imagem. Não foi produzido um print artificial. Os registros HTTP, testes, esquema OpenAPI e ambiente foram salvos normalmente.

## Trecho de vídeo sugerido — cerca de 25 segundos
Mostrar rapidamente as pastas app/routes, app/models e app/database; depois o Swagger com POST /consultas e a saída do pytest.

“Comecei isolando as dependências em um ambiente virtual. Separei as rotas, os modelos e o acesso ao banco, e implementei o CRUD de consultas com APIRouter. Os dados são validados com Pydantic e persistidos pelo SQLModel. Os testes usam um banco em memória separado e verificam tanto o caminho de sucesso quanto entradas inválidas.”

Este trecho serve como introdução do vídeo de até cinco minutos. Reservar a maior parte do tempo para autorização, security gate do Exercício 12 e decisões do capstone no Exercício 13.

## Referências técnicas
- [FastAPI: aplicações com múltiplos arquivos](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [FastAPI: lifespan](https://fastapi.tiangolo.com/advanced/events/)
- [SQLModel: testes com FastAPI](https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/)
- [Pydantic: tipos padrão](https://docs.pydantic.dev/latest/api/standard_library_types/)
