# Exercício 3 — Fundamentos de segurança e modelagem inicial

**Aplicação:** API de agendamento de consultas de uma rede de clínicas.  
**Baseline:** código após o Exercício 2, analisado em 22/09/2026.  
**Escopo:** avaliação CIA, mapeamento de referências e DFD inicial. Nenhuma funcionalidade de segurança nova foi implementada nesta etapa.

## 1. Conclusão da avaliação

A aplicação possui controles concretos de validação, exposição de propriedades, consultas parametrizadas e escape HTML. Esses controles reduzem classes específicas de falha, mas **não garantem acesso autorizado aos dados**: atualmente qualquer cliente que alcance o serviço pode consultar, criar, alterar e excluir consultas. A página da recepção também não exige autenticação.

O uso continua restrito ao ambiente local de demonstração e a dados fictícios. A recomendação para uso com dados reais é **não liberar a aplicação enquanto as lacunas de acesso, transporte, armazenamento e operação não forem tratadas**. Esta é uma decisão técnica desta análise, não uma declaração de conformidade legal ou uma pontuação CVSS.

## 2. Ativos, dados e escopo efetivamente existente

| ID | Ativo | Conteúdo e sensibilidade |
|---|---|---|
| A01 | Registro de consulta | id, paciente_id, profissional_id, data_hora, status e observacao. O vínculo paciente–profissional–horário pode revelar atendimento de saúde quando associado a pessoa identificável. |
| A02 | Auditoria interna mínima | criado_em e referencia_interna. São metadados internos protegidos contra exposição nos contratos de saída; não constituem trilha de auditoria de acessos ou alterações. |
| A03 | Persistência | Arquivo SQLite configurado por DATABASE_URL, contendo A01 e A02. Uma cópia do arquivo contorna os response models. |
| A04 | Serviço e agenda | Disponibilidade da API, página HTML, banco, CPU, memória e disco necessários ao agendamento. |
| A05 | Código, configuração e evidências | Templates, modelos, dependências fixadas e arquivos de teste. Evidências atuais são fictícias; evidências futuras com dados reais precisariam de tratamento próprio. |

Não há tabela de pacientes nem de profissionais, nome, CPF, prontuário, credenciais, tokens ou integração M2M implementados. O código apenas referencia IDs positivos; não verifica a existência desses pacientes e profissionais.

Um ID numérico **não equivale a anonimização**. A classificação de A01 como dado de alta sensibilidade é uma decisão de proteção para o contexto pretendido, considerando a possibilidade de ligação à pessoa. A observação é livre: o rótulo “operacional” e o limite de 500 caracteres não impedem que alguém insira informação clínica.

A LGPD inclui informações de saúde ligadas a pessoa natural na categoria de dados sensíveis e exige medidas técnicas e administrativas de proteção (art. 5º, II, e art. 46). Isso justifica o peso adicional da confidencialidade aqui, sem diminuir a importância dos demais pilares. [LGPD — texto oficial](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2018/lei/l13709.htm).

## 3. Avaliação pela tríade CIA

A classificação abaixo é qualitativa e contextual. “Impacto alto” descreve a consequência potencial no uso real; não significa que foi calculada uma severidade CVSS ou comprovado um incidente.

| Pilar | Objetivo e cenário concreto | Controles existentes | Lacunas e conclusão |
|---|---|---|---|
| Confidencialidade | Evitar que terceiros descubram quais pacientes têm consultas, horários e observações. Um cliente sem login pode enumerar GET /consultas e abrir /agenda. Impacto alto, com possibilidade de exposição de atendimento. | ConsultaRead expõe só seis propriedades; auditoria não vai para JSON nem contexto HTML; Jinja2 escapa texto; no-store na agenda. | Não há identidade, papéis ou ownership. TLS e criptografia do SQLite não estão configurados na aplicação. Controle de campos é parcial: os próprios seis campos públicos continuam sensíveis. Confidencialidade insuficiente para dados reais. |
| Integridade | Evitar consultas alteradas, removidas, associadas ao paciente errado ou com horário incorreto. Um cliente sem login consegue PUT/DELETE. Impacto alto para a operação da clínica. | Tipos e limites explícitos, enum de status, fuso obrigatório e UTC; extra='forbid'; SQLModel parametrizado; auditoria inicial gerada pelo servidor; commits em sessões. | Sem autorização, integridade referencial, regra de conflito de agenda, controle de concorrência de negócio ou trilha de alteração. O banco aceita IDs inexistentes. A validação sintática não comprova legitimidade nem consistência clínica. |
| Disponibilidade | Manter consulta e atualização da agenda acessíveis. Muitas requisições ou gravações podem consumir recursos e afetar a recepção. Impacto alto operacional. | Listagem JSON limitada a 100; HTML a 50 linhas por página; observação até 500 caracteres; limites numéricos; sessões encerradas por contexto; rejeição de datas extremas; /health verifica resposta do processo. | Não há rate limiting, limite explícito do corpo HTTP, proteção contra volume total de gravações, backup/restauração testados, redundância ou monitoramento configurados. Offset alto ainda pode ser caro. SQLite pode enfrentar contenção de escrita. Paginação não comprova resistência a DoS. |

**Interdependência:** XSS poderia permitir uso indevido da interface e afetar confidencialidade e integridade; uma exclusão indevida compromete integridade e disponibilidade do agendamento. Por isso, a tríade não deve ser tratada como três listas independentes.

## 4. Controles rastreáveis ao código

| Controle | Implementação observada | Evidência existente | Limite do controle |
|---|---|---|---|
| C01 — Lista de propriedades públicas | ConsultaRead e response_model em app/models/consulta.py e app/routes/consultas.py; projeção em app/routes/agenda.py | test_auditoria_persistida_mas_ausente_em_todas_respostas; test_openapi_publica_apenas_contratos_publicos | Limita propriedades, não decide quem pode ler cada consulta. |
| C02 — Validação de entrada | ConsultaWrite, IDs estritos, status enum, data com fuso, observacao limitada e extra='forbid' | test_criacao_invalida_nao_persiste; test_cliente_nao_pode_definir_auditoria; test_observacao_tem_limite | Não valida existência do paciente, ownership ou conflito de agenda. |
| C03 — Dados separados de SQL | Session.get, select, add, sqlmodel_update e delete, com SQLModel; sem concatenação de entrada em comandos SQL | Inspeção de app/routes/consultas.py e app/routes/agenda.py; testes CRUD | Persistência parametrizada não impede uma operação legítima executada por ator indevido. |
| C04 — Escape contextual HTML | select_autoescape centralizado; base.html e agenda.html com herança; observacao somente em texto de célula | test_xss_persistido_renderizado_como_texto; HTML e DOM salvos no Exercício 2 | Não é sanitização universal nem protege automaticamente um futuro frontend que use innerHTML. |
| C05 — Redução de consumo por resposta | limit/offset limitados; agenda com PAGE_SIZE=50; limites da observação e datas | test_paginacao_invalida; test_agenda_vazia_e_paginacao; casos extremos UTC | Não há teste de carga, quotas, rate limiting ou limite do crescimento do banco. |
| C06 — Menor retenção em cache HTML | Cache-Control: no-store em GET /agenda | Verificação do cabeçalho em test_auditoria_persistida_mas_ausente_em_todas_respostas | Não é criptografia, não impede captura de tela e não está aplicado às respostas JSON. |
| C07 — Configuração e isolamento | .venv, requirements.txt, BaseSettings, .env.example sem segredos e .gitignore | evidencias/exercicio_02/qualidade.json e inspeção dos arquivos | .venv isola dependências, não oferece sandbox do processo. Fixar versões não é scan de vulnerabilidades; .gitignore não protege arquivo já rastreado nem filtra ZIP. |
| C08 — Verificação do desenvolvimento | pytest e revisão Astra nos exercícios 1 e 2 | 39 casos aprovados no registro do Exercício 2; revisões em docs | Testes parciais não são auditoria completa, scan ZAP, SAST especializado ou prova de ausência de falhas. |

## 5. Mapeamento dos frameworks

As referências têm funções diferentes: OWASP categoriza riscos de aplicações e APIs; NIST SSDF orienta práticas do ciclo de desenvolvimento; MITRE CWE descreve classes de fraqueza. O mapeamento é uma interpretação técnica dos controles do projeto, não uma certificação. Para MITRE, foi escolhido **CWE**, adequado ao nível de código; não foram atribuídas técnicas ATT&CK sem cenário que as sustente.

Versões adotadas: OWASP Top 10 **2025**, OWASP API Security Top 10 **2023** e NIST SSDF **1.1 / SP 800-218**. Os identificadores são sempre acompanhados de versão para não confundir, por exemplo, A05:2025 Injection com a numeração de edições anteriores.

| Referência | Controle ou lacuna concreta | Avaliação |
|---|---|---|
| OWASP API3:2023 — Broken Object Property Level Authorization | C01 e C02 restringem propriedades expostas e alterações nos campos internos. | Mitigação parcial de exposição e atribuição indevida de propriedades. Ainda faltam políticas por usuário/recurso. [Fonte](https://owasp.org/API-Security/editions/2023/en/0xa3-broken-object-property-level-authorization/) |
| OWASP A05:2025 — Injection | C03 separa parâmetros de SQL; C04 escapa a observação em HTML. | Controles implementados para os caminhos atuais de SQL e HTML, sem alegar imunidade a toda injeção. [Fonte](https://top10.owasp.org/2025/A05_2025-Injection/) |
| OWASP API4:2023 — Unrestricted Resource Consumption | C05 limita dados por resposta, porém não limita volume de requisições. | Redução parcial de consumo; disponibilidade ainda requer controles adicionais. [Fonte](https://owasp.org/API-Security/editions/2023/en/0xa4-unrestricted-resource-consumption/) |
| OWASP A01:2025 — Broken Access Control | GET/POST/PUT/DELETE e /agenda não verificam usuário ou permissão. | Lacuna prioritária, não um controle implementado. [Fonte](https://top10.owasp.org/2025/A01_2025-Broken_Access_Control/) |
| NIST SSDF PW.5.1 — práticas de codificação segura | C01–C04: validação, contrato explícito, SQL parametrizado e escape. | Evidência de adoção parcial no código atual. |
| NIST SSDF PW.7.2 — revisão/análise do código e registro dos problemas | C08: revisões Astra documentadas; correções de offset e UTC no Exercício 1. | Análise assistida por IA; não equivale a revisão humana independente ou a SAST completo. |
| NIST SSDF PW.8.2 — testes e documentação dos resultados | C08: testes de endpoints e payloads, com logs e regressões. | Cobertura observável, ainda sem autenticação, testes de carga ou pipeline de segurança. |
| NIST SSDF PW.1.1 — modelagem de riscos | Este inventário, avaliação CIA e DFD. | Base inicial para o threat model posterior, não um STRIDE completo. |
| MITRE CWE-200 — exposição de informação sensível | C01 restringe metadados internos e C06 reduz cache HTML. | Acesso sem autorização aos dados públicos continua possível. [Fonte](https://cwe.mitre.org/data/definitions/200.html) |
| MITRE CWE-79 — XSS | C04; payload persistido permanece texto ao renderizar. | Defesa verificada no contexto HTML usado. [Fonte](https://cwe.mitre.org/data/definitions/79.html) |
| MITRE CWE-89 — SQL Injection | C03; chamadas SQLModel parametrizadas. | Controle no acesso atual ao banco. [Fonte](https://cwe.mitre.org/data/definitions/89.html) |
| MITRE CWE-862 — ausência de autorização | Nenhuma política aplicada às rotas atuais. | Lacuna identificada e relacionada a A01:2025. [Fonte](https://cwe.mitre.org/data/definitions/862.html) |
| MITRE CWE-400 — consumo não controlado de recursos | C05 ajuda por resposta; não há limite global de requisições/gravações. | Lacuna residual de disponibilidade. [Fonte](https://cwe.mitre.org/data/definitions/400.html) |

As associações SSDF acima usam a publicação de referência [NIST SP 800-218, versão 1.1](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-218.pdf). São correspondências entre práticas e evidências locais, não declaração de que todos os requisitos dessas práticas foram cumpridos.

## 6. DFD básico — baseline e notação

Veja **dfd_exercicio_03.png**, a versão editável **dfd_exercicio_03.mmd** e a tabela de fluxos abaixo.

- **E:** entidade externa; **P:** processo lógico; **D:** armazenamento; **F:** fluxo; **TB:** fronteira de confiança.
- Linhas contínuas representam o estado implementado. Linhas tracejadas no quadro inferior representam somente a integração futura.
- P1 e P2 executam no mesmo processo FastAPI. P3 representa a camada compartilhada de persistência, não um serviço de rede separado.
- O SQLite é um arquivo local: TB2 não implica um banco remoto ou conexão SQL via rede.
- Os papéis recepcionista, profissional de saúde e administrador pertencem ao contexto de negócio, mas ainda não são identidades reconhecidas pelo sistema.
- Pacientes são titulares dos dados referenciados, não um quarto cliente implementado.
- O frontend dedicado e o laboratório ainda não foram construídos. E1 representa hoje clientes JSON como Swagger/TestClient; o futuro frontend usará esse contrato.

![DFD da API de agendamento](dfd_exercicio_03.png)

### Elementos

| ID | Elemento | Estado |
|---|---|---|
| E1 | Cliente JSON, operado por usuário ou atacante; frontend dedicado previsto | Contrato JSON existente |
| E2 | Navegador da recepção exibindo /agenda | Página existente, sem restrição por papel |
| P1 | CRUD /consultas: validação e contratos JSON | Implementado |
| P2 | Agenda: filtro por dia, projeção pública e renderização Jinja2 | Implementado |
| P3 | SQLModel / Session: persistência compartilhada | Implementado |
| D1 | SQLite: consultas com propriedades públicas e auditoria interna | Implementado |
| E3 | Laboratório parceiro, organização externa | Previsto, sem integração |
| P4 | Consulta de disponibilidade para cliente M2M | Previsto, sem endpoint, credencial ou política definidos |

### Fronteiras de confiança

| ID | Transição | Tratamento atual e exigência futura |
|---|---|---|
| TB1 | Cliente externo → processo da aplicação; fluxos F01–F04 | Corpo, parâmetros e cabeçalhos não são confiáveis. Validação existe; identidade e autorização não. O teste local usa HTTP em loopback, não HTTPS. TLS deverá ser definido para tráfego real. |
| TB2 | Processo da aplicação ↔ armazenamento em arquivo; F09–F10 | SQL parametrizado existe. Permissões específicas de sistema operacional, criptografia em repouso, backup e recuperação não foram implementados nem auditados neste Assessment. O mesmo host não elimina essa fronteira lógica. |
| TB3 | Dado persistido → conteúdo interpretado no navegador; trecho final de F04 | É uma fronteira de interpretação, sobreposta ao retorno através de TB1. Observações recuperadas do banco continuam não confiáveis e são escapadas no contexto HTML. Não representa um segundo servidor. |
| TB4 | Organização parceira ↔ clínica; F11–F12 previstos | A confiança na recepção não se transfere ao laboratório. O futuro cliente M2M precisará de identidade e escopo próprios e deve receber disponibilidade sem dados de pacientes. Ainda não implementado. |

As caixas e fronteiras documentam pressupostos; sua existência no desenho não significa que há firewall, TLS, ACL ou autenticação efetivamente configurados.

### Fluxos e dados sensíveis

| ID | Origem → destino | Dados e finalidade | Sensibilidade / controle |
|---|---|---|---|
| F01 | E1 → P1 | POST/PUT com paciente_id, profissional_id, data_hora, status e observacao; GET/DELETE com IDs e paginação conforme o método | Pode conter dados de paciente ou texto clínico. C02; não há autorização. |
| F02 | P1 → E1 | JSON público de consulta/lista; códigos de resultado e erros; DELETE 204 sem corpo | IDs, horário e observação permanecem sensíveis no contexto real. C01; não sai A02 nas respostas de sucesso. Erros de validação podem refletir entradas enviadas pelo próprio cliente. |
| F03 | E2 → P2 | GET /agenda com dia e pagina | Parâmetros de busca, sem corpo de prontuário. Validação de data/página; sem autenticação. |
| F04 | P2 → E2 | HTML com consulta, IDs de paciente/profissional, horário, status e observação | Dados sensíveis renderizados; C01, C04 e C06. Cruza TB1 e TB3. Escape não decide quem pode ver a página. |
| F05 | P1 → P3 | Operações CRUD e valores validados | Entrada em memória para persistência; não há uma chamada HTTP interna. |
| F06 | P3 → P1 | Entidade(s) com propriedades públicas e auditoria, ou ausência de registro | Confidencial dentro do servidor; C01 filtra antes de F02. |
| F07 | P2 → P3 | Intervalo de datas e paginação para leitura | Consulta somente leitura, parametrizada. |
| F08 | P3 → P2 | Registros do dia com observação original e auditoria | P2 projeta ConsultaRead antes do template; texto continua não confiável. |
| F09 | P3 → D1 | Comandos parametrizados de leitura/gravação/exclusão | Em gravações, inclui A01 e metadados internos gerados pelo servidor. |
| F10 | D1 → P3 | Resultados, registros persistidos e resultado das operações | Inclui A01/A02; acesso direto ao arquivo contornaria C01 e C02. |
| F11 | E3 → P4 | **Previsto:** solicitação de horários disponíveis | Contrato e autenticação M2M ainda serão definidos. Nenhum envio real. |
| F12 | P4 → E3 | **Previsto:** apenas disponibilidade mínima necessária | Não incluir paciente_id, observações ou auditoria; requisito futuro, não comportamento testado. |

**Caminho de paciente:** F01 → F05 → F09 persiste dados; F10 → F06 → F02 devolve JSON; F10 → F08 → F04 apresenta a agenda. C01 reduz propriedades e C04 trata HTML, mas sem autorização esses caminhos continuam acessíveis a um cliente que alcance a API.

**Caminho de XSS persistido:** uma observação controlada pelo cliente atravessa F01/F05/F09, permanece como dado em D1 e retorna em F10/F08/F04. O escape em P2/TB3 é necessário mesmo quando a origem imediata parece ser “o banco”.

### Superfícies de apoio fora do desenho principal

/health informa que o processo responde, sem testar disponibilidade do banco. /docs e /openapi.json expõem o contrato. /static entrega o CSS. O Swagger padrão utiliza recursos externos de documentação; não se tratou esse carregamento como fluxo de pacientes no DFD central, mas ele merece revisão na implantação.

O Uvicorn pode registrar metadados de requisições, inclusive caminho e query string. Isso não constitui auditoria de negócio. A política de retenção e acesso a logs e às evidências ainda não está definida; não colocar dados clínicos em URLs. Essas superfícies devem entrar no inventário ampliado do threat model seguinte.

## 7. Prioridades para a modelagem posterior

| Prioridade contextual | Lacuna / cenário | Relação com DFD e CIA | Próxima decisão necessária |
|---|---|---|---|
| Alta | Leitura, edição e exclusão sem identidade ou autorização | TB1, F01–F04; C/I/D | Definir autenticação, papéis e autorização por recurso; criar testes de acesso indevido. |
| Alta | Dados em trânsito e no arquivo sem proteção criptográfica configurada | TB1/TB2; C | Definir TLS, acesso ao arquivo, proteção em repouso e gestão de segredos. |
| Alta | Operação com IDs inexistentes, conflitos e exclusão sem histórico | F05/F09; I/D | Definir integridade referencial, regras de agenda e política de auditoria/retenção. |
| Alta | Consumo de requisições, disco ou bloqueios de escrita | P1–P3/D1; D | Definir limites, rate limiting, monitoramento e recuperação testada. |
| Antes da integração M2M | Parceiro recebendo dados de pacientes além do necessário | TB4, F11/F12; C | Contrato mínimo de disponibilidade, escopos e credenciais próprias. |

A ordem é uma recomendação local baseada no contexto. O critério formal de severidade do security gate será definido no Exercício 12; esta tabela não o antecipa nem o substitui.

## 8. Evidências, revisão e rastreabilidade

A avaliação foi baseada nos arquivos app/models/consulta.py, app/routes/consultas.py, app/routes/agenda.py, app/core/templates.py, app/database/session.py, app/main.py, app/core/config.py e nos testes atuais. O manifesto em evidencias/exercicio_03 registra hashes dos arquivos analisados, para ligar o desenho a esta baseline.

Os 39 testes e os registros HTTP/DOM do Exercício 2 são evidências preexistentes reaproveitadas, não uma nova execução da suíte neste exercício documental. Uma sondagem isolada em memória foi usada para registrar os contratos, as rotas sem autenticação e os controles de saída, sem dados reais e sem modificar o banco local.

A revisão Astra deste artefato está registrada em docs/revisao_astra_exercicio_03.md. O DFD é um diagrama técnico gerado a partir da análise, não um print da aplicação; as pendências de captura dos exercícios anteriores continuam separadas.

| Exigência | Onde é atendida |
|---|---|
| Avaliação CIA | Seção 3, cenários concretos e riscos residuais |
| Frameworks ligados a controles reais | Seções 4 e 5, códigos C01–C08 e fontes oficiais |
| DFD básico | Diagrama PNG e fonte Mermaid, com elementos E/P/D |
| Trust boundaries | TB1–TB4, com pressupostos e limites explícitos |
| Fluxos sensíveis de pacientes | Tabela F01–F12 e caminhos descritos |
| Base para próximas análises | Identificadores estáveis e prioridades da seção 7 |

## 9. Vídeo — trecho de aproximadamente 25 segundos

Mostrar o DFD e apontar o caminho cliente → API → banco → agenda.

“Na análise CIA, identifiquei que limitar campos e escapar HTML ajuda, mas ainda não substitui autenticação e autorização. O DFD registra onde os dados de pacientes entram, são armazenados e voltam ao navegador. Também separa o laboratório, que futuramente deverá receber somente horários disponíveis. Relacionei esses controles e lacunas a OWASP, NIST SSDF e MITRE CWE.”

Este trecho é de apoio; manter o vídeo completo em até cinco minutos e reservar tempo para os exercícios 12 e 13.
