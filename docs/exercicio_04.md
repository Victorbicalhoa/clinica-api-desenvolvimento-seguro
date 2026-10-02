# Exercício 4 — Threat model da API de agendamento

**Referência:** TM-CLINICA · versão 1.0 · 22/09/2026.  
**Baseline:** código após Exercício 2; inventário CIA e DFD do Exercício 3.  
**Artefatos oficiais para os próximos exercícios:** este documento e Exercicio_04_Threat_Model.json, mantidos juntos em docs.  
**Escopo:** modelagem e documentação; nenhum controle futuro foi implementado nesta etapa.

## 1. Resultado e método

O modelo registra **14 ameaças**, **10 misuse cases**, **12 ações de mitigação/manutenção** e **14 critérios de verificação**. STRIDE foi aplicado separadamente a quatro componentes existentes: P1 (CRUD), P2 (agenda), P3 (persistência) e D1 (SQLite). E3/P4 é avaliado à parte como integração futura.

A principal lacuna é o acesso sem identidade, autorização por recurso ou controle por função. São problemas relacionados, mas exigem verificações distintas; seus scores não devem ser somados como incidentes independentes.

A sequência adotada foi: arquitetura/ativos → intenção e sequência de abuso → ameaça STRIDE → controles/lacunas → mitigação → critério observável. O documento será atualizado junto ao sistema, seguindo a orientação de [threat modeling da OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Threat_Modeling_Cheat_Sheet.html). Os misuse cases descrevem como uma função legítima pode ser abusada, conforme a referência de [abuse cases da OWASP](https://cheatsheetseries.owasp.org/cheatsheets/Abuse_Case_Cheat_Sheet.html).

STRIDE: **S**, falsificação de identidade; **T**, adulteração; **R**, negação de autoria; **I**, divulgação indevida; **D**, negação de serviço; **E**, elevação de privilégio. Uma ameaça pode ter vários efeitos; as letras não indicam severidade. [Microsoft — categorias STRIDE](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats).

## 2. Pressupostos e limites

- DFD preservado: E1 cliente JSON; E2 navegador da recepção; P1 CRUD; P2 agenda; P3 SQLModel; D1 SQLite; E3 laboratório e P4 disponibilidade previstos.
- TB1: cliente/aplicação. TB2: processo/arquivo. TB3: dado/interpretação HTML no retorno F04. TB4: parceiro/clínica. F01–F10 existem; F11/F12 são futuros.
- Pacientes/profissionais são apenas IDs. Não há autenticação, papéis, ownership, JWT, sessão ou M2M implementados.
- A demonstração usa dados fictícios e HTTP loopback. Cenários de rede/host são condicionais, não provas de exposição pública.
- Não houve carga hostil, interceptação, corrupção de banco, cópia de dados reais ou exploração de parceiro.
- Controles C01–C08 são os registrados no Exercício 3. Evidências de 39 testes do Exercício 2 e da sondagem do Exercício 3 são anteriores, não nova execução desta etapa.
- BOLA entre sujeitos autenticados e escalada entre papéis serão verificadas quando existirem identidades. Hoje está comprovada a ausência de controle de acesso, não o bypass de um JWT inexistente.
- Este inventário não esgota a segurança do projeto. Dependências, pipeline, cadeia de fornecimento, operação do host e logs deverão receber expansão específica. A05 está inventariado sem alegação de cobertura completa.

**Decisões pendentes:** matriz de papéis; ownership/escopo usuário–clínica–consulta; duração/conflito de horários; retenção da auditoria; limites de consumo; topologia TLS; RPO/RTO; contrato M2M. Propostas de testes não substituem essas decisões.

## 3. Ativos e superfícies

| Ativo | Conteúdo |
|---|---|
| A01 | Consultas: IDs de paciente/profissional, horário, status e observacao; potencialmente sensíveis quando ligados à pessoa. |
| A02 | Metadados internos criado_em/referencia_interna; não são trilha de eventos. |
| A03 | Arquivo SQLite e eventuais cópias; backups ainda não implementados. |
| A04 | Disponibilidade da API, agenda e capacidade operacional. |
| A05 | Código, configuração, dependências e evidências do projeto. |

IDs vinculados a atendimento não são automaticamente anônimos. Observacao pode receber texto clínico apesar da finalidade operacional; os exemplos usam apenas dados fictícios.

| Superfície | Entrada/acesso | Componentes / fronteiras |
|---|---|---|
| AS01 | HTTP /consultas e /consultas/{id}: JSON, parâmetros, IDs, leitura/criação/edição/exclusão. | P1 / TB1 |
| AS02 | HTTP /agenda: dia/pagina, consulta ao banco e interpretação do HTML. | P2 / TB1, TB3 |
| AS03 | Operações SQLModel/Session e limites transacionais; não é endpoint de rede separado. | P3, D1 / TB2 |
| AS04 | Arquivo SQLite, diretório, configuração e cópias acessíveis pelo host; requer privilégio adicional. | D1 / TB2 |
| AS05 | /docs e /openapi.json expõem contrato; /health e /static são superfícies auxiliares. | P1, P2 / TB1 |
| AS06 | Transporte cliente/servidor e futura terminação TLS; atualmente apenas HTTP loopback observado. | P1, P2 / TB1 |
| AS07 | Futuro cliente parceiro E3 e endpoint P4 de disponibilidade; nenhuma chamada implementada. | P4 / TB4 |

AS05 permite descobrir o contrato, o que não é automaticamente uma vulnerabilidade. AS04 requer acesso ao host; não há fluxo direto cliente → SQLite na API.

### Controles atuais reaproveitados

- **C01:** Whitelist de propriedades JSON/contexto HTML.
- **C02:** Validação explícita e extra='forbid'.
- **C03:** SQLModel parametrizado.
- **C04:** Autoescape Jinja2.
- **C05:** Limites de campos/paginação/datas.
- **C06:** no-store em /agenda.
- **C07:** Configuração, dependências fixadas, .env.example.
- **C08:** Testes e revisões dos exercícios anteriores.

C01 controla propriedades, não acesso a objetos; C02 não valida legitimidade de negócio; C05 não é rate limiting; C07 não equivale a sandbox nem scan de dependências. A implementação e evidência detalhadas constam no Exercício 3.

## 4. Critério de prioridade

Pontuação qualitativa e autoral para a operação pretendida com dados de pacientes, considerando a arquitetura atual e o atacante que alcance a superfície. Não mede dano na demonstração fictícia; **não é CVSS, DREAD nem o gate do Exercício 12**.

- **P=1:** controle atual bloqueia o vetor ou seria necessária regressão; **P=2:** condição adicional, privilégio local, posição de rede ou volume não medido; **P=3:** oportunidade direta ao alcançar uma rota sem a barreira pertinente.
- **I=1:** efeito limitado/reversível; **I=2:** efeito limitado em dados, agenda ou rastreabilidade; **I=3:** exposição de pacientes, operação indevida importante ou interrupção relevante.
- **P × I:** 1–2 baixa; 3–4 moderada; 6 alta; 9 crítica. P/I são inteiros entre 1 e 3.
- Controles planejados não reduzem o score. Os pré-requisitos, cenário e evidência de cada registro justificam a estimativa.
- Score condicional não transforma integração inexistente em vulnerabilidade ativa. Reavaliar quando a arquitetura mudar.

## 5. Misuse cases

### MC-01 — Agir como funcionário e acessar consultas alheias

**Ator:** Cliente sem autenticação hoje; sujeito de baixo privilégio no futuro.  
**Pré-condição:** Alcança API; variante futura exige conta válida.  
**Sequência de abuso:** 1. Chama CRUD sem credencial; 2. escolhe ID; 3. lê/altera recurso alheio; 4. futuramente tenta ação acima do papel.  
**Resultado / situação atual:** Acesso sem identidade, ownership ou permissão.  
**Ameaças:** TH-01, TH-02, TH-13.

### MC-02 — Adulterar consulta e atributos internos

**Ator:** Cliente malicioso.  
**Pré-condição:** Envia POST/PUT JSON.  
**Sequência de abuso:** 1. Usa IDs positivos inexistentes e horário conflitante; 2. em tentativa separada, acrescenta criado_em/referencia_interna; 3. verifica persistência/rejeição.  
**Resultado / situação atual:** Negócio inconsistente; tentativa contra auditoria já é rejeitada.  
**Ameaças:** TH-03, TH-04.

### MC-03 — Extrair dados pelo contrato de saída

**Ator:** Cliente que consulta API/agenda.  
**Pré-condição:** Alcança GET /consultas ou /agenda.  
**Sequência de abuso:** 1. Lista consultas; 2. inspeciona JSON/HTML/OpenAPI; 3. procura auditoria e dados de pacientes; 4. amplia busca por IDs/páginas.  
**Resultado / situação atual:** Auditoria omitida hoje; dados públicos continuam sem autorização.  
**Ameaças:** TH-01, TH-02, TH-06.

### MC-04 — Executar observação persistida

**Ator:** Cliente que grava texto.  
**Pré-condição:** Pode gravar observacao; outra pessoa abre a agenda do dia.  
**Sequência de abuso:** 1. Persiste `<img src=x onerror=alert(1)>` em dado fictício; 2. recepção abre /agenda; 3. espera transformação em HTML ativo.  
**Resultado / situação atual:** Se escape regredir, controle da página e possível uso futuro dos privilégios da vítima. Hoje texto é escapado e não há sessão autenticada a roubar.  
**Ameaças:** TH-07.

### MC-05 — Transformar entrada em SQL

**Ator:** Cliente malicioso.  
**Pré-condição:** Pode enviar corpo/parâmetros.  
**Sequência de abuso:** 1. Envia ID malformado ou sintaxe SQL em observacao; 2. tenta mudar comando executado; 3. busca leitura/alteração extra.  
**Resultado / situação atual:** Vetor contido por validação/parametrização atuais; regressão a prevenir.  
**Ameaças:** TH-08.

### MC-06 — Excluir ou alterar e negar autoria

**Ator:** Cliente ou operador malicioso.  
**Pré-condição:** A ação alcança o endpoint; hoje não exige identidade.  
**Sequência de abuso:** 1. Executa PUT/DELETE em consulta fictícia; 2. nega autoria; 3. exige prova de quem agiu.  
**Resultado / situação atual:** UUID/criado_em e access log não demonstram autoria confiável.  
**Ameaças:** TH-05.

### MC-07 — Consumir capacidade da agenda

**Ator:** Cliente automatizado.  
**Pré-condição:** Alcança serviço, sem acesso ao host.  
**Sequência de abuso:** 1. Repete leituras/paginação/gravações; 2. aumenta custo e banco; 3. disputa capacidade com usuários legítimos.  
**Resultado / situação atual:** Consumo de CPU/disco/conexões ou contenção. Não foi executado ataque de carga.  
**Ameaças:** TH-09.

### MC-08 — Copiar ou danificar banco fora da API

**Ator:** Ator com acesso local indevido/processo comprometido.  
**Pré-condição:** Privilégio adicional de leitura/escrita em arquivo/diretório/backup, não comprovado remotamente.  
**Sequência de abuso:** 1. Copia SQLite para contornar filtros; ou 2. altera/apaga banco; 3. explora ausência de restauração testada.  
**Resultado / situação atual:** Exposição total, alteração ou perda de dados; ACL real é desconhecida.  
**Ameaças:** TH-10, TH-11.

### MC-09 — Interceptar futura implantação HTTP

**Ator:** Adversário no caminho de rede.  
**Pré-condição:** Serviço exposto em rede sem TLS válido.  
**Sequência de abuso:** 1. Observa tráfego; 2. tenta obter/modificar consulta; 3. tenta imitar servidor.  
**Resultado / situação atual:** Vazamento/alteração/servidor falso no cenário condicional; não alegamos interceptação do loopback.  
**Ameaças:** TH-12.

### MC-10 — Usar parceiro como acesso humano

**Ator:** Cliente M2M comprometido.  
**Pré-condição:** Integração futura ativa e credencial do parceiro comprometida.  
**Sequência de abuso:** 1. Usa credencial M2M; 2. pede mais que disponibilidade; 3. tenta CRUD/agenda humana; 4. testa escopos/audiência indevidos.  
**Resultado / situação atual:** Exposição/ações além do escopo; integração ainda não existe.  
**Ameaças:** TH-14.

## 6. STRIDE por componente

As seis categorias foram consideradas. Células sem identidade/papel próprio explicam a condição, sem inventar autenticação para um arquivo.

| Componente | S | T | R | I | D | E |
|---|---|---|---|---|---|---|
| P1 | TH-01, TH-12 | TH-02, TH-03, TH-04, TH-08, TH-12 | TH-05 | TH-02, TH-06, TH-08, TH-12 | TH-09 | TH-13 |
| P2 | TH-01, TH-12 | TH-07, TH-12 (conteúdo interpretado/transporte) | TH-05 | TH-02, TH-06, TH-07, TH-12 | TH-09 | TH-13; TH-07 se contexto da vítima adquirir privilégios |
| P3 | Não possui identidade própria: herda sujeito de P1/P2. Lacuna de origem: TH-01. | TH-04, TH-08, TH-11 | TH-05 | TH-08; dados íntegros podem ser devolvidos a solicitante indevido por P1/P2. | TH-09, TH-11 | Sem fronteira autônoma de papéis: privilégios do processo/host são pré-condição de TH-10/TH-11. |
| D1 | Não autentica usuário humano; alteração/substituição de arquivo é T, em TH-11. | TH-04, TH-11 | TH-05, TH-11 | TH-10 | TH-09, TH-11 | Arquivo não eleva privilégio sozinho; acesso local adicional condiciona TH-10/TH-11. |

P3 executa no mesmo processo de P1/P2; não requer uma autenticação duplicada por módulo. O sujeito e as políticas devem ser estabelecidos centralmente.

**P4 futuro:** TH-14 considera S/I/E em TB4. T/R/D do parceiro deverão ser detalhados ao definir contrato, auditoria e limites, antes de liberar a integração.

## 7. Ameaças consolidadas

| ID | Ameaça | STRIDE | P × I | Prioridade | Estado |
|---|---|---|---|---|---|
| TH-01 | Ausência de identidade confiável | S | 3 × 3 = 9 | Crítica | Aberta |
| TH-02 | Acesso a recurso alheio / falta de ownership | I/T | 3 × 3 = 9 | Crítica | Aberta |
| TH-03 | Atribuição de auditoria pelo cliente | T | 1 × 2 = 2 | Baixa | Controlada no vetor atual |
| TH-04 | Associação inválida e conflito de agenda | T | 3 × 2 = 6 | Alta | Aberta |
| TH-05 | Negação de autoria sem trilha | R | 3 × 2 = 6 | Alta | Aberta |
| TH-06 | Exposição de propriedades internas | I | 1 × 2 = 2 | Baixa | Controlada no vetor atual |
| TH-07 | XSS persistido por regressão | T/I/E | 1 × 3 = 3 | Moderada | Controlada no vetor atual |
| TH-08 | Injeção SQL por consulta insegura futura | T/I | 1 × 3 = 3 | Moderada | Controlada no vetor atual |
| TH-09 | Esgotamento e contenção SQLite | D | 2 × 3 = 6 | Alta | Parcialmente mitigada |
| TH-10 | Leitura de arquivo SQLite/backup | I | 2 × 3 = 6 | Alta | Condicional — infraestrutura |
| TH-11 | Adulteração/perda do armazenamento | T/R/D | 2 × 3 = 6 | Alta | Condicional — infraestrutura |
| TH-12 | Interceptação/servidor falso sem TLS | S/T/I | 2 × 3 = 6 | Alta | Condicional — implantação em rede |
| TH-13 | Funções acima do papel permitido | E | 3 × 3 = 9 | Crítica | Aberta |
| TH-14 | Confusão de acesso M2M/humano | S/E/I | 2 × 3 = 6 | Alta | Planejada — integração futura |

“Controlada no vetor atual” significa defesa no caminho observado e regressão a manter; não significa ausência de risco em todos os contextos. “Condicional” exige condição adicional não comprovada no ambiente.

### TH-01 — Ausência de identidade confiável

**STRIDE:** S · **componentes:** P1, P2 · **ativos:** A01, A04.  
**Superfícies:** AS01, AS02 · **fluxos:** F01, F02, F03, F04 · **fronteiras:** TB1.  
**Misuse cases:** MC-01, MC-03.

**Cenário:** Cliente alcançável opera como usuário legítimo. Não existe login/JWT: requisito de identidade ausente, não quebra de autenticação existente.  
**Evidência / fundamento:** Sondagem do Exercício 3 mostrou operações sem credencial.  
**Controles existentes:** Nenhum controle específico suficiente demonstrado para este vetor.  
**Mitigações:** MT-01 · **verificação:** VT-01.  
**Prioridade:** Crítica (P=3, I=3, score=9). **Estado:** Aberta.  
**Risco residual / limite:** Autenticar sozinho não resolve TH-02/TH-13.

### TH-02 — Acesso a recurso alheio / falta de ownership

**STRIDE:** I, T · **componentes:** P1, P2 · **ativos:** A01.  
**Superfícies:** AS01, AS02 · **fluxos:** F01, F02, F03, F04, F05, F06 · **fronteiras:** TB1.  
**Misuse cases:** MC-01, MC-03.

**Cenário:** Busca por ID, edição e listas não verificam relação sujeito–recurso. Depois de login, lacuna pode persistir como BOLA/IDOR.  
**Evidência / fundamento:** Inspeção: nenhum filtro/dependência de autorização. Contas A/B ainda não existem para provar variante autenticada.  
**Controles existentes:** C01 (Whitelist de propriedades JSON/contexto HTML); C02 (Validação explícita e extra='forbid')  
**Mitigações:** MT-02, MT-01 · **verificação:** VT-02.  
**Prioridade:** Crítica (P=3, I=3, score=9). **Estado:** Aberta.  
**Risco residual / limite:** Contrato de saída não impede acesso aos campos públicos alheios.

### TH-03 — Atribuição de auditoria pelo cliente

**STRIDE:** T · **componentes:** P1 · **ativos:** A02.  
**Superfícies:** AS01 · **fluxos:** F01, F05, F09 · **fronteiras:** TB1.  
**Misuse cases:** MC-02.

**Cenário:** Cliente tenta definir auditoria/campo extra via POST/PUT; entrada recusa propriedades não declaradas.  
**Evidência / fundamento:** Testes do Exercício 2 confirmam 422; metadados gerados pelo servidor.  
**Controles existentes:** C01 (Whitelist de propriedades JSON/contexto HTML); C02 (Validação explícita e extra='forbid')  
**Mitigações:** MT-04 · **verificação:** VT-03.  
**Prioridade:** Baixa (P=1, I=2, score=2). **Estado:** Controlada no vetor atual.  
**Risco residual / limite:** Reabrir se novo schema/rota aceitar auditoria; negócio inválido é TH-04.

### TH-04 — Associação inválida e conflito de agenda

**STRIDE:** T · **componentes:** P1, P3, D1 · **ativos:** A01, A04.  
**Superfícies:** AS01, AS03 · **fluxos:** F01, F05, F09 · **fronteiras:** TB1, TB2.  
**Misuse cases:** MC-02.

**Cenário:** IDs positivos inexistentes e gravações concorrentes de horários conflitantes podem passar pela validação sintática.  
**Evidência / fundamento:** Não há FK/regra de conflito; concorrência não foi exercitada como prova de ataque.  
**Controles existentes:** C02 (Validação explícita e extra='forbid'); C03 (SQLModel parametrizado)  
**Mitigações:** MT-05 · **verificação:** VT-04.  
**Prioridade:** Alta (P=3, I=2, score=6). **Estado:** Aberta.  
**Risco residual / limite:** Regra exata depende do negócio; checagem sem atomicidade pode falhar em corrida.

### TH-05 — Negação de autoria sem trilha

**STRIDE:** R · **componentes:** P1, P2, P3, D1 · **ativos:** A01, A02.  
**Superfícies:** AS01, AS02, AS03 · **fluxos:** F01, F03, F05, F07, F09 · **fronteiras:** TB1, TB2.  
**Misuse cases:** MC-06.

**Cenário:** Ator nega leitura/alteração/exclusão sem identidade e histórico por ação.  
**Evidência / fundamento:** criado_em/UUID são criação; DELETE remove registro. Sem auditoria de negócio.  
**Controles existentes:** Nenhum controle específico suficiente demonstrado para este vetor.  
**Mitigações:** MT-06, MT-01 · **verificação:** VT-05.  
**Prioridade:** Alta (P=3, I=2, score=6). **Estado:** Aberta.  
**Risco residual / limite:** Access log/UUID não provam autoria; proteger também dados dos eventos.

### TH-06 — Exposição de propriedades internas

**STRIDE:** I · **componentes:** P1, P2 · **ativos:** A01, A02.  
**Superfícies:** AS01, AS02, AS05 · **fluxos:** F02, F04, F06, F08 · **fronteiras:** TB1, TB3.  
**Misuse cases:** MC-03.

**Cenário:** Serializar ORM completo futuramente poderia expor auditoria; hoje ConsultaRead/projeção a omitem.  
**Evidência / fundamento:** Testes de campos/contexto/OpenAPI e HTTP/DOM existentes.  
**Controles existentes:** C01 (Whitelist de propriedades JSON/contexto HTML); C06 (no-store em /agenda)  
**Mitigações:** MT-04 · **verificação:** VT-06.  
**Prioridade:** Baixa (P=1, I=2, score=2). **Estado:** Controlada no vetor atual.  
**Risco residual / limite:** Dados públicos sensíveis permanecem sem acesso controlado: TH-01/TH-02.

### TH-07 — XSS persistido por regressão

**STRIDE:** T, I, E · **componentes:** P2 · **ativos:** A01, A04.  
**Superfícies:** AS01, AS02 · **fluxos:** F01, F05, F09, F10, F08, F04 · **fronteiras:** TB1, TB3.  
**Misuse cases:** MC-04.

**Cenário:** Observação vira código se escape regredir ou frontend usar innerHTML. Elevação refere-se aos privilégios futuros da vítima, não a sessão já existente.  
**Evidência / fundamento:** Quatro payloads escapados; DOM sem script/img/eventos. Não há XSS explorável demonstrado hoje.  
**Controles existentes:** C04 (Autoescape Jinja2); C01 (Whitelist de propriedades JSON/contexto HTML)  
**Mitigações:** MT-07 · **verificação:** VT-07.  
**Prioridade:** Moderada (P=1, I=3, score=3). **Estado:** Controlada no vetor atual.  
**Risco residual / limite:** Novos contextos JS/URL exigem nova avaliação; CSP não substitui escape.

### TH-08 — Injeção SQL por consulta insegura futura

**STRIDE:** T, I · **componentes:** P1, P3 · **ativos:** A01, A03.  
**Superfícies:** AS01, AS03 · **fluxos:** F01, F05, F07, F09, F10 · **fronteiras:** TB1, TB2.  
**Misuse cases:** MC-05.

**Cenário:** Concatenação futura poderia transformar entrada em SQL; hoje acesso é parametrizado.  
**Evidência / fundamento:** Inspeção Session.get/select/ORM e testes de validação; sem finding SQLi ou captura específica de SQL emitido.  
**Controles existentes:** C02 (Validação explícita e extra='forbid'); C03 (SQLModel parametrizado)  
**Mitigações:** MT-08 · **verificação:** VT-08.  
**Prioridade:** Moderada (P=1, I=3, score=3). **Estado:** Controlada no vetor atual.  
**Risco residual / limite:** Preservar parâmetro; operação indevida sem autorização não é automaticamente SQLi.

### TH-09 — Esgotamento e contenção SQLite

**STRIDE:** D · **componentes:** P1, P2, P3, D1 · **ativos:** A04, A03.  
**Superfícies:** AS01, AS02, AS03 · **fluxos:** F01, F03, F05, F07, F09 · **fronteiras:** TB1, TB2.  
**Misuse cases:** MC-07.

**Cenário:** Limites de página não impedem volume, escrita contínua, corpo excessivo ou paginação cara.  
**Evidência / fundamento:** Rate limiting/quota/corpo total não configurados no app; sem benchmark de DoS.  
**Controles existentes:** C05 (Limites de campos/paginação/datas)  
**Mitigações:** MT-09 · **verificação:** VT-09.  
**Prioridade:** Alta (P=2, I=3, score=6). **Estado:** Parcialmente mitigada.  
**Risco residual / limite:** Capacidade/infraestrutura exigem medição; limite por resposta não prova resiliência.

### TH-10 — Leitura de arquivo SQLite/backup

**STRIDE:** I · **componentes:** D1 · **ativos:** A01, A02, A03.  
**Superfícies:** AS04 · **fluxos:** F09, F10 · **fronteiras:** TB2.  
**Misuse cases:** MC-08.

**Cenário:** Ator com acesso ao arquivo lê tudo sem passar pelos modelos da API.  
**Evidência / fundamento:** SQLite é local; ACL, criptografia de disco e backups não auditados. Não alegamos arquivo público.  
**Controles existentes:** Nenhum controle específico suficiente demonstrado para este vetor.  
**Mitigações:** MT-10 · **verificação:** VT-10.  
**Prioridade:** Alta (P=2, I=3, score=6). **Estado:** Condicional — infraestrutura.  
**Risco residual / limite:** Comprometimento do serviço pode contornar controle por rota; proteger chaves.

### TH-11 — Adulteração/perda do armazenamento

**STRIDE:** T, R, D · **componentes:** P3, D1 · **ativos:** A01, A02, A03, A04.  
**Superfícies:** AS04 · **fluxos:** F09, F10 · **fronteiras:** TB2.  
**Misuse cases:** MC-08.

**Cenário:** Ator com escrita altera/apaga banco/evidências e afeta serviço; falhas operacionais também podem causar perda.  
**Evidência / fundamento:** Projeto sem backup/restauração; não houve corrupção executada.  
**Controles existentes:** Nenhum controle específico suficiente demonstrado para este vetor.  
**Mitigações:** MT-10, MT-06 · **verificação:** VT-11.  
**Prioridade:** Alta (P=2, I=3, score=6). **Estado:** Condicional — infraestrutura.  
**Risco residual / limite:** Definir recuperação e proteger cópias contra o mesmo comprometimento.

### TH-12 — Interceptação/servidor falso sem TLS

**STRIDE:** S, T, I · **componentes:** P1, P2 · **ativos:** A01.  
**Superfícies:** AS06 · **fluxos:** F01, F02, F03, F04 · **fronteiras:** TB1.  
**Misuse cases:** MC-09.

**Cenário:** Se HTTP local for usado em rede, ator no caminho pode observar/modificar dados ou imitar servidor.  
**Evidência / fundamento:** Atual é HTTP loopback; não há evidência de exposição externa ou TLS de produção.  
**Controles existentes:** Nenhum controle específico suficiente demonstrado para este vetor.  
**Mitigações:** MT-11 · **verificação:** VT-12.  
**Prioridade:** Alta (P=2, I=3, score=6). **Estado:** Condicional — implantação em rede.  
**Risco residual / limite:** Score é do cenário condicional; autenticação não cifra o transporte.

### TH-13 — Funções acima do papel permitido

**STRIDE:** E · **componentes:** P1, P2 · **ativos:** A01, A04.  
**Superfícies:** AS01, AS02 · **fluxos:** F01, F03, F05 · **fronteiras:** TB1.  
**Misuse cases:** MC-01.

**Cenário:** Clientes executam ações reservadas a perfis legítimos; login futuro sem regra por função mantém acesso indevido.  
**Evidência / fundamento:** Papéis/matriz não existem; não alegamos escalada de token/papel já implementado.  
**Controles existentes:** C02 (Validação explícita e extra='forbid')  
**Mitigações:** MT-03, MT-01 · **verificação:** VT-13.  
**Prioridade:** Crítica (P=3, I=3, score=9). **Estado:** Aberta.  
**Risco residual / limite:** Raiz compartilhada com TH-01, mas testes de função são distintos de identidade/ownership.

### TH-14 — Confusão de acesso M2M/humano

**STRIDE:** S, E, I · **componentes:** P4 · **ativos:** A01, A04.  
**Superfícies:** AS07 · **fluxos:** F11, F12 · **fronteiras:** TB4.  
**Misuse cases:** MC-10.

**Cenário:** Credencial parceira aceita em rotas humanas ou disponibilidade retorna dados de pacientes.  
**Evidência / fundamento:** E3/P4 são previstos, sem endpoint/token atual.  
**Controles existentes:** Nenhum controle específico suficiente demonstrado para este vetor.  
**Mitigações:** MT-12 · **verificação:** VT-14.  
**Prioridade:** Alta (P=2, I=3, score=6). **Estado:** Planejada — integração futura.  
**Risco residual / limite:** Avaliação antecipatória, não finding atual; revisar antes de integrar.

## 8. Tratamento e responsabilidades propostas

Os responsáveis são funções sugeridas, não tarefas atribuídas a pessoas/equipes externas. “Planejada” não significa implementada.

| Mitigação | Ação | Responsável proposto | Estado |
|---|---|---|---|
| MT-01 — Identidade verificável | Autenticação centralizada; validar credenciais e, quando adotado JWT, assinatura, algoritmo permitido, emissor/audiência e expiração. Não confiar no ID ou papel declarado pelo cliente. | Backend / autenticação | Planejada |
| MT-02 — Autorização por recurso | Centralizar ownership e escopo organizacional em leitura, escrita, exclusão, listagens e agenda. Identidade vem da autenticação, não do corpo da consulta. | Backend / autorização | Planejada |
| MT-03 — Permissões por função | Aprovar matriz de recepcionista/profissional/administrador; negar por padrão e verificar cada ação no servidor. A matriz exata ainda não está definida. | Backend + negócio | Planejada; depende da matriz de negócio |
| MT-04 — Contratos explícitos | Preservar ConsultaWrite extra='forbid', ConsultaRead, auditoria gerada no servidor e projeção pública antes do template. | Backend / modelos | Implementada como C01/C02; manter regressões |
| MT-05 — Consistência do agendamento | Validar existência/vínculo de paciente e profissional; regra de conflito aplicada atomicamente. Proposta mínima a confirmar: uma consulta ativa por profissional no mesmo instante; intervalos por duração exigem modelagem adicional. | Backend + negócio | Planejada; regra de conflito proposta |
| MT-06 — Trilha de auditoria protegida | Registrar sujeito autenticado, ação, recurso, instante UTC, resultado e correlação; proteger integridade/acesso e definir retenção. Excluir tokens, credenciais e observacao dos logs de rotina. | Backend + plataforma | Planejada |
| MT-07 — Renderização contextual segura | Preservar autoescape e projeção pública; não aplicar safe/Markup a dados de usuário. Futuro consumidor JSON deve renderizar como texto; avaliar CSP como camada adicional. | Backend / templates | C04 implementado; CSP/cliente futuro não implementados |
| MT-08 — Parametrização SQL | Preservar SQLModel parametrizado; proibir concatenação de entrada; revisar buscas dinâmicas e regressões com conteúdo tratado como dado. | Backend / persistência | C03 implementado; teste específico a ampliar |
| MT-09 — Proteção de capacidade | Definir limites de corpo, requisições por cliente/operação, quotas de escrita, timeouts e monitoramento. Medir paginação cara e contenção SQLite em carga controlada. | Backend + plataforma | Parcial: C05 limita respostas/campos, não volume total |
| MT-10 — Armazenamento e recuperação | Conta de serviço e ACL restritas, proteção de dados/backups em repouso e gestão de chaves; testar restauração. Não servir banco ou diretório de dados como arquivos estáticos. | Plataforma | Planejada; host não auditado |
| MT-11 — Transporte protegido | TLS e validação de certificado para uso em rede; definir terminação proxy e cabeçalhos confiáveis. Loopback HTTP não comprova TLS de implantação. | Plataforma + backend | Planejada para exposição em rede |
| MT-12 — Separação M2M/humano | Definir identidade/credenciais, audiência e escopos do parceiro e contrato mínimo de disponibilidade. Negar acesso à agenda humana e CRUD; não enviar pacientes, observações ou auditoria. | Backend / integração | Planejada; E3/P4 não implementados |

**Ordem de tratamento:** identidade (MT-01); autorização (MT-02/03); consistência/auditoria (MT-05/06); capacidade e implantação (MT-09/10/11). Preservar modelos, SQL e HTML (MT-04/07/08) durante toda evolução. MT-12 é pré-condição de liberação da integração.

Não se recomenda uso com dados reais enquanto as lacunas de acesso e implantação estiverem abertas. Essa recomendação não é um gate automatizado nem uma decisão de severidade CVSS.

## 9. Verificações para os próximos exercícios

| ID | Critério de aceitação | Situação e evidência |
|---|---|---|
| VT-01 | Sem credencial válida, API retorna 401; agenda deve negar acesso sem conteúdo de pacientes, por 401 ou redirecionamento ao login conforme fluxo aprovado. Credencial inválida/expirada também é rejeitada. | Planejada. evidencias/exercicio_03/sondagem_cia.json demonstra a lacuna. |
| VT-02 | Com dois sujeitos/recursos, B não lê/altera/exclui consulta de A nem a encontra na listagem/agenda. Política proposta: 404 para recurso alheio, sem alteração no banco. Incluir casos positivos autorizados. | Planejada; base para Exercício 6. buscar_consulta hoje consulta somente por ID. |
| VT-03 | POST/PUT com criado_em, referencia_interna ou campo extra retorna 422 sem modificar registro; revalidar lista permitida ao evoluir schema. | Já existe parcialmente; manter. tests/test_exposicao_templates.py::test_cliente_nao_pode_definir_auditoria. |
| VT-04 | IDs inexistentes rejeitados sem persistência. Após aprovar regra de slot, duas gravações concorrentes produzem apenas uma consulta ativa; outra falha controladamente (proposta 409). | Planejada; depende da regra de negócio. Consulta armazena IDs sem FK e sem regra de conflito. |
| VT-05 | Ação autorizada e tentativa negada geram evento com resultado e identidade validada quando disponível; sem autenticação, registrar ator anônimo/identidade não validada, sem inventar autoria. Aplicativo não apaga silenciosamente evento no destino protegido. Testar ausência de tokens e observacao. | Planejada. criado_em/UUID não registram autoria/histórico. |
| VT-06 | POST, GET individual, lista, PUT, contexto HTML e OpenAPI só têm campos aprovados; marcador interno fictício não aparece. Toda alteração pública exige aprovação explícita. | Já existe; manter. tests/test_exposicao_templates.py::test_auditoria_persistida_mas_ausente_em_todas_respostas; test_openapi_publica_apenas_contratos_publicos. |
| VT-07 | Persistir script/img/svg/texto Jinja em observacao; saída contém texto escapado, sem elemento executável nem evento. Confirmar DOM e, futuramente, frontend. | Já existe no HTML; ampliar ao frontend. tests/test_exposicao_templates.py::test_xss_persistido_renderizado_como_texto; evidencias/exercicio_02/navegador_dom.json. |
| VT-08 | Texto parecido com SQL permanece literal; nenhum registro extra é lido/alterado/removido. ID malformado retorna 422. Capturar comandos emitidos e confirmar parâmetros separados do SQL. | Parcial; teste específico planejado. Inspeção ORM e testes CRUD/validação existentes. |
| VT-09 | Em ambiente isolado, limites configurados geram 429/413 conforme caso; serviço recupera capacidade. Medir latência/erros contra orçamento definido e quota de escrita. | Planejada; carga não executada. test_paginacao_invalida cobre só limite de resposta. |
| VT-10 | Conta não autorizada não lê banco/configuração/backup na implantação; arquivo não é servido via HTTP. Verificar criptografia e acesso às chaves sem copiar dados reais. | Planejada; infraestrutura. app/main.py só monta app/static; ACL do host desconhecida. |
| VT-11 | Em cópia descartável, falha/corrupção simulada dispara detecção e recuperação. Restaurar backup e conferir integridade/contagem e RPO/RTO definidos. Nunca destruir banco real. | Planejada. Projeto não possui backup/restauração. |
| VT-12 | Implantação de teste em rede usa HTTPS válido; cliente rejeita certificado inválido e não transmite dados sensíveis por HTTP. Verificar terminação TLS e salto interno do proxy. | Planejada. README demonstra apenas HTTP local. |
| VT-13 | Cada papel/ação da matriz aprovada tem caso permitido e negado; cabeçalho/campo de papel não amplia acesso. Ação proibida: 403 sem efeito. Recurso alheio segue VT-02. | Planejada; depende da matriz. app/auth é só preparação de pacote. |
| VT-14 | M2M com credencial/escopo válidos recebe só disponibilidade; ausência de credencial: 401. Escopo/audiência indevidos ou tentativa de CRUD/agenda humana: negar sem dados. | Planejada; integração inexistente. DFD E3/P4/F11/F12 são previstos. |

VT são requisitos verificáveis, não nomes de funções pytest já existentes. VT-10/11/12 exigem evidência da infraestrutura e não podem ser “comprovados” apenas por mocks.

**Cadeia para autorização:** MC-01 → TH-02 → A01/AS01/TB1/F01–F02 → MT-02 → VT-02. O Exercício 6 poderá começar pelos dois sujeitos/recursos; a relação concreta de ownership deve ser definida antes.

**Cadeia para XSS:** MC-04 → TH-07 → A01/AS02/TB3/F04 → MT-07/C04 → VT-07 → testes e DOM do Exercício 2. Preservar a cadeia ao introduzir novos campos e autenticação.

Não foram produzidos scans ZAP/SAST, resultados de carga ou execução de pipeline nesta etapa.

## 10. Referência oficial, manutenção e evidências

1. Preservar IDs do Exercício 3 e TH/MC/MT/VT. Nunca reutilizar um ID para outro problema.
2. Atualizar código vinculado, teste/evidência, data, responsável pela revisão e risco residual ao implementar controle. Plano sozinho não fecha ameaça.
3. Encerrar ameaça somente após demonstrar seus critérios. Aceitação de risco deve registrar justificativa e aprovação real; este documento não inventa uma aprovação do usuário.
4. Mudança de schema, identidade, papel, integração, rede ou armazenamento exige revisão de DFD e ameaça. Versionar e sincronizar Markdown/JSON.
5. No Exercício 12, aplicar o gate definido e justificado naquele exercício. No capstone (13), ligar cada teste/finding/correção a TH e VT e registrar risco residual/decisão de deploy.
6. Manter cenários controlados como regressões. Expandir A05/cadeia de fornecimento e P4 quando essas partes forem detalhadas.

| Exigência | Atendimento |
|---|---|
| Misuse cases | MC-01–MC-10: ator, pré-condição, sequência e resultado |
| STRIDE em pelo menos três componentes | P1, P2, P3 e D1; seis categorias consideradas |
| Ativos e superfícies | A01–A05 e AS01–AS07, ligados a cada ameaça |
| Mitigações | MT-01–MT-12, com estado e responsabilidade proposta |
| Referência para capstone | IDs estáveis, JSON, critérios VT e política de manutenção |
| Revisão Astra | docs/revisao_astra_exercicio_04.md |

A validação em evidencias/exercicio_04 verifica integridade das referências e hashes da baseline, não a segurança do sistema. A suíte anterior de 39 casos não foi apresentada como nova execução. Não houve alteração de código da aplicação. ZIP somente ao final.

## 11. Vídeo — aproximadamente 30 segundos

Mostrar matriz STRIDE e MC-01 → TH-02 → MT-02 → VT-02.

“Usei STRIDE para analisar o CRUD, a agenda e a persistência. Cada ameaça tem um cenário de abuso, os ativos afetados e uma mitigação verificável. Por exemplo, acessar uma consulta alheia exige autorização por recurso, que deverá ser testada com dois usuários distintos. Esse registro será a referência das correções e dos testes do capstone.”

Escolher este trecho ou o resumo CIA/DFD para evitar repetição, preservando o limite de cinco minutos e espaço para os exercícios 12 e 13.
