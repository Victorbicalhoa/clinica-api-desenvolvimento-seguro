> Registro técnico da etapa indicada. Para resultados atuais e alterações posteriores, consulte o [índice de documentação](README.md).

# Exercício 8 — Identificação manual de vulnerabilidades OWASP Top 10

**Autor:** Hebert Almeida · **Data:** 24/09/2026 · **Versão:** REV-OWASP-1.0

## 1. Escopo, método e resultado

A análise foi feita por leitura do código da aplicação entregue na pasta Assessment, seguindo entrada HTTP → autenticação → autorização → persistência → resposta. Foram inspecionados também modelos, configuração, templates e testes existentes. Não foram utilizados scanners para identificar os padrões, nem executados ataques ou alterados controles da aplicação neste exercício. A coleta automática de linhas e hashes apenas registra os arquivos lidos; não é um scan de vulnerabilidades.

A baseline instalada corresponde ao Exercício 6. O Exercício 7 possui trabalho preparatório fora do projeto, ainda não concluído ou validado; esses arquivos não integram esta análise. Não há papel de paciente, endpoint de prontuário ou integração M2M na aplicação entregue. O contexto do enunciado é uma descrição de incidente a analisar, não evidência de execução contra esta versão.

**Resultado:** três lacunas presentes, em três categorias distintas, e uma instância didática de BOLA, contraposta ao controle já implementado. Não seria correto afirmar que a BOLA continua aberta no CRUD atual: GET/PUT/DELETE usam owned_consulta; listas e agenda profissional usam scope_consultas.

| ID | Padrão | OWASP Top 10:2025 | Correspondência 2021 | Situação |
|---|---|---|---|---|
| V08-01 | Buscar objeto pelo ID sem verificar vínculo | A01 — Broken Access Control; API1:2023 BOLA | A01 — Broken Access Control | Instância didática; padrão mitigado na aplicação atual |
| V08-02 | Login e novos desafios MFA sem limite global de tentativas | A07 — Authentication Failures | A07 — Identification and Authentication Failures | Presente na camada de aplicação |
| V08-03 | Operações e falhas de segurança sem trilha de auditoria apropriada | A09 — Security Logging and Alerting Failures | A09 — Security Logging and Monitoring Failures | Presente na aplicação; infraestrutura externa não auditada |
| V08-04 | Agendamentos sem política de conflito e transição de estado | A06 — Insecure Design | A04 — Insecure Design | Lacuna presente; regra de negócio proposta exige formalização |

Foi adotada a edição [OWASP Top 10:2025](https://top10.owasp.org/2025/), com correspondência à edição 2021 para facilitar comparação com o material da disciplina. BOLA é a categoria específica **API1:2023** do OWASP API Security Top 10; não é o nome de uma categoria independente no Top 10 geral.

## 2. V08-01 — BOLA: autenticar não autoriza o objeto

**Categoria:** A01:2025/A01:2021 Broken Access Control e API1:2023 Broken Object Level Authorization. O padrão é aceitar um identificador controlado pelo cliente e devolver o objeto sem conferir a relação entre identidade e recurso. [Referência OWASP API1:2023](https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/).

**Instância vulnerável para leitura:** o trecho abaixo é uma reconstrução didática, adaptada às funções e tipos da aplicação. Não é transcrição do código atual, snapshot histórico ou rota registrada. Mantém autenticação para isolar a falha de autorização por objeto:

```python
# SOMENTE EXEMPLO DIDATICO VULNERAVEL — nao registrar na aplicacao.
@router.get("/consultas/{consulta_id}", response_model=ConsultaRead)
def obter_consulta_sem_ownership(
    consulta_id: ConsultaId, session: SessionDep, user: ProfessionalDep
):
    consulta = session.get(Consulta, consulta_id)
    if consulta is None:
        raise HTTPException(404, "Consulta nao encontrada.")
    return consulta  # user foi autenticado, mas nao foi relacionado ao objeto.
```

**Análise linha a linha:** ProfessionalDep exige um profissional, mas o parâmetro user não participa da busca. Session.get filtra apenas pela chave primária; a verificação seguinte comprova existência, não permissão. ConsultaRead limita campos, mas ainda contém paciente_id e observacao. Portanto, trocar um ID válido por outro pode expor dados de terceiros nesse exemplo, mesmo com token válido, query parametrizada e response model.

**Cenário e pré-condição:** profissional A possui consulta 10; profissional B possui consulta 20. A está autenticado e troca `/consultas/10` por `/consultas/20`. No padrão vulnerável, se 20 existir, seu conteúdo é retornado. Os números são ilustrativos e os resultados são previsões da leitura, não respostas HTTP obtidas nesta etapa. Para o paciente autenticado descrito no enunciado, a mesma falha ocorre se uma rota de prontuário usar o ID sem relacionar paciente autenticado e consulta. Essa rota/papel não existe na baseline e não foi inventada como evidência local.

**Impacto:** acesso horizontal indevido a informações de saúde; se a mesma omissão existir em PUT/DELETE, também alteração ou exclusão de dados de terceiros. Prioridade alta caso o padrão seja introduzido em uma implantação real. Não se atribui um vazamento real ao projeto.

**Situação atual:** app/routes/consultas.py, obter_consulta, chama `owned_consulta(consulta_id, session, user)`. Em app/auth/policies.py, owned_consulta combina o ID com scope_consultas, que exige simultaneamente profissional_id da conta e paciente_id pertencente a VinculoPaciente do usuário. Um recurso fora desses vínculos é tratado como não encontrado. Listas e agenda profissional aplicam o mesmo filtro. A recepção possui política explícita de leitura operacional sem observacao; ela não representa bypass do contrato de acesso adotado no Exercício 6.

**Critério de verificação:** usuário A lê seu recurso; GET/PUT/DELETE de B com token A retornam 404, sem alteração; listas/HTML de A não contêm recursos de B. O teste existente `test_ownership_crud_listas_agenda_e_vinculos`, em tests/test_auth.py, cobre esse cenário entre profissionais. Seu resultado pertence à execução do Exercício 6, não a uma nova execução nesta análise.

**Decisão para as próximas etapas:** preservar a política central; se houver novo papel paciente, acrescentar associação paciente↔conta validada pelo servidor e testes próprios antes da exposição. UUIDs não substituem ownership. Não reintroduzir a rota vulnerável para produzir uma demonstração.

**Rastreabilidade:** TH-02, MC-01, MT-02, VT-02; TB1; A01.

## 3. V08-02 — Tentativas ilimitadas no fluxo de autenticação

**Categoria:** A07:2025 Authentication Failures. Limitar tentativas e tratar ataques repetidos faz parte da proteção do fluxo de autenticação. Hashing de senha não restringe o número de tentativas online. [Referência OWASP A07](https://top10.owasp.org/2025/A07_2025-Authentication_Failures/).

**Evidência manual:** em app/routes/auth.py, login executa consulta por username, verify_password e retorna falha ou sucesso. Não há contador persistido de falhas por conta/origem, janela de tentativas ou aplicação de atraso/bloqueio adaptativo. app/main.py registra routers e middleware de cache, sem mecanismo de limitação. Settings não configura esse controle. DesafioMFA registra tentativas por desafio; confirm_mfa limita esse contador a cinco, mas login pode criar novo desafio a cada apresentação válida da senha administrativa.

**Fluxo de abuso:** um atacante que alcança `/auth/token` pode repetir combinações de credenciais. Com senha administrativa já comprometida e MFA simulado habilitado, pode solicitar novos desafios e renovar o orçamento de tentativas; cinco erros em um desafio não bloqueiam a conta nem a emissão de outro. Não foi realizado ataque de força bruta. Não há evidência de quebra de bcrypt ou de bypass da validade/consumo único do desafio.

**Impacto e pré-condições:** aumento da viabilidade de adivinhação online e custo de processamento bcrypt; tomada de conta depende de descobrir credencial válida, não decorre automaticamente de uma requisição. Na demonstração local em loopback, a superfície é menor; a falha de controle torna-se especialmente relevante antes da exposição de rede. Controles de proxy/IdP externos não foram auditados e não podem ser presumidos.

**Controles existentes e insuficiência:** bcrypt custo 12, mensagem genérica, hash fictício para usuário ausente, JWT com expiração, MFA administrativo simulado, expiração e consumo único do desafio. Esses controles protegem outros aspectos, mas não implementam orçamento global de tentativas.

**Correção recomendada, ainda não implementada aqui:** limite por conta e origem, orçamento compartilhado de emissão/validação MFA, atraso progressivo e tratamento de abuso sem bloqueio permanente facilmente induzido por terceiros. Contadores precisam funcionar entre workers; um dicionário local não basta em implantação distribuída.

**Critério futuro:** definir limiares e janela; ultrapassá-los deve provocar resposta controlada, como 429, inclusive ao trocar challenge_id; após recuperação permitida, uma autenticação legítima deve funcionar. Não fixar limiares fictícios como se já fossem configuração do sistema.

**Prioridade:** alta antes da exposição externa. **Rastreabilidade:** TH-01 e TH-09 como riscos relacionados; MT-09 e VT-09 precisam ser detalhados para autenticação e renovação de desafios. O limite do VT-09 original não é evidência de controle já implantado.

## 4. V08-03 — Auditoria de segurança insuficiente

**Categoria:** A09:2025 Security Logging and Alerting Failures. A leitura mostra ausência de eventos estruturados que permitam detectar e investigar falhas de autenticação, negações de acesso e alterações de consultas. [Referência OWASP A09](https://top10.owasp.org/2025/A09_2025-Security_Logging_and_Alerting_Failures/).

**Evidência manual:** em app/routes/consultas.py, POST/PUT/DELETE persistem a operação sem emitir evento de auditoria com ator, ação, resultado e recurso. app/auth/policies.py lança 403/404, e app/auth/security.py lança 401, sem registro próprio da decisão. Em app/models/consulta.py, criado_em e referencia_interna apenas caracterizam o registro, sem indicar quem leu/alterou/excluiu. Sessao e DesafioMFA controlam autenticação, mas não representam um histórico de ações sobre consultas.

**Fluxo de abuso:** um usuário com permissão altera ou exclui uma consulta e posteriormente nega a ação; outro cliente tenta recursos de terceiros repetidamente. As respostas impedem o acesso indevido quando a política se aplica, mas não há na aplicação uma trilha adequada para correlacionar as decisões com a identidade validada. Logs HTTP do Uvicorn podem existir; método, URL e status isolados não equivalem à auditoria clínica nem a um sistema de alertas.

**Impacto:** dificuldade de investigação, atribuição e detecção tempestiva. Essa lacuna não concede acesso por si só; agrava a resposta a incidentes e a capacidade de responsabilização. Prioridade alta antes de uso operacional com dados sensíveis.

**Correção recomendada:** serviço central de eventos estruturados contendo instante UTC, ID de correlação, identidade validada quando houver, ação, identificador mínimo do recurso e resultado. Falha de login não deve atribuir identidade autenticada ao username informado. Não registrar senhas, hashes, JWT, OTP ou observacao; restringir consulta/alteração dos eventos e definir retenção, alertas e resposta.

**Critério futuro:** uma sequência permitida de criação/alteração/exclusão e uma negação de acesso devem gerar eventos correlacionáveis, sem conteúdo clínico ou segredos. Testar também que um usuário comum não altera/apaga a trilha e que alertas configurados chegam ao destino previsto. Nada disso foi declarado executado nesta etapa.

**Rastreabilidade:** TH-05, MC-06, MT-06, VT-05; A01/A02. Observação complementar: o OTP exibido no terminal é parte da simulação opt-in do Exercício 6, não um mecanismo de logging de segurança apropriado para produção.

## 5. V08-04 — Ausência de invariantes de agendamento

**Categoria:** A06:2025 Insecure Design (A04:2021). O desenho permite persistir entradas sintaticamente válidas sem definir/garantir invariantes de negócio sobre concorrência e transição de status. É um problema diferente de BOLA: o agente pode estar autorizado a todos os recursos envolvidos. [Referência OWASP A06](https://top10.owasp.org/2025/A06_2025-Insecure_Design/).

**Evidência manual:** ConsultaWrite valida IDs, fuso, enum de status e tamanho do texto. authorize_write verifica vínculos. Em criar_consulta, depois dessa verificação, há construção do objeto, add e commit, sem verificação de conflito. atualizar_consulta aplica sqlmodel_update diretamente após ownership/vínculos. O modelo Consulta não declara restrição de unicidade para profissional e instante, nem uma máquina de estados para a consulta. SQL parametrizado protege a interpretação da query, não a coerência da agenda.

**Cenário de análise:** um profissional autenticado repete POST com profissional_id próprio, paciente vinculado, mesmo data_hora e status agendada. Pelo caminho lido, cada execução pode produzir novo registro, pois a chave primária é gerada e nenhum controle de conflito foi definido. Também não há política que impeça substituir realizada por agendada em PUT. São inferências da inspeção, não payloads executados neste exercício.

**Premissa de negócio explícita:** considerar indevida mais de uma consulta ativa do mesmo profissional no mesmo instante é uma regra proposta para esta clínica, não fornecida literalmente pelo enunciado. A ausência do controle e do desenho de transições é comprovável no código; classificar cada duplicidade como operação proibida exige confirmar a política. Não se inventam duração de atendimento, intervalos de sobreposição ou exceções clínicas ainda não modelados.

**Impacto potencial:** agenda contraditória, capacidade indevidamente ocupada e perda de confiabilidade operacional, inclusive por repetição intencional de operações autorizadas. Não é vazamento de prontuário nem injeção SQL. Prioridade moderada para definição imediata da regra; sobe conforme exposição e impacto confirmado pelo negócio.

**Correção recomendada:** formalizar regras de estado, cancelamento, duração e conflitos; aplicar o controle no caminho de POST e PUT e garantir atomicidade com mecanismo apropriado no banco/transação. Consultar a existência e depois inserir sem proteção transacional permanece sujeito a corrida.

**Critério futuro, condicionado à regra aprovada:** para duas criações simultâneas do mesmo horário/profissional, exatamente uma deve ter sucesso e a outra receber conflito, como 409, sem duplicidade. Definir também testes de transições permitidas e negadas e casos legítimos que devem continuar funcionando.

**Rastreabilidade:** TH-04, MC-02, MT-05, VT-04; A01/A04. O threat model já registrava essa regra como proposta; esta revisão não a promove a requisito aprovado silenciosamente.

## 6. Padrões que não foram classificados como falhas abertas

- **SQL injection:** consultas atuais usam SQLModel/SQLAlchemy com valores parametrizados. Não foi encontrado SQL concatenado com entrada de usuário nos caminhos lidos.
- **XSS persistido na agenda:** observacao pode armazenar marcação, mas o Jinja usa autoescape no contexto textual e os templates não usam safe nesse conteúdo. Armazenar o texto não comprova execução no navegador.
- **Mass assignment e exposição da auditoria:** extra=forbid e ConsultaRead limitam entrada e saída; o ORM não vai diretamente para o template.
- **JWT sem expiração ou algoritmo livre:** security.py exige exp, fixa HS256, valida emissor/audiência e confere sessão persistida. Essas falhas não foram encontradas.
- **“Paciente autenticado lendo prontuário” na versão atual:** esse papel e endpoint não existem. A falha do contexto foi explicada por uma instância didática, sem fabricar evidência de acesso.

Essas conclusões são limitadas ao código revisado. Não demonstram ausência de todas as vulnerabilidades nem certificam infraestrutura, dependências ou implantação.

## 7. Evidências e atendimento à tarefa

`evidencias/exercicio_08/trechos_revisados.md` reúne trechos reais com números de linha, caminhos e SHA-256. `baseline_sha256.json` registra app, tests e configuração sem segredos. `coletar_evidencias.py` permite refazer a coleta e verificar que o código não mudou durante esta etapa. Os hashes não validam segurança; apenas identificam a versão lida.

| Item solicitado | Evidência |
|---|---|
| Leitura de código, sem depender de scanner | Caminhos, funções e encadeamento explicados em V08-01 a V08-04; extratos da baseline |
| Pelo menos três categorias distintas | Três lacunas atuais em A07/A09/A06; BOLA em A01/API1 analisada separadamente |
| Incluir uma instância de BOLA | Trecho didático vulnerável com identidade autenticada sem vínculo; comparação com owned_consulta atual |
| Impactos, causas e orientação para correção | Pré-condições, efeitos, controles existentes e critérios futuros em cada ficha |
| Rastreabilidade | IDs do threat model do Exercício 4 preservados |

**Limite de aderência do cenário:** se a avaliação exigir uma BOLA aberta na versão entregue, essa condição não é atendida, pois a proteção já foi implementada no Exercício 6. A entrega demonstra a capacidade de identificar o padrão e distinguir o caso vulnerável da versão protegida, preservando o código seguro. Não se deve afirmar um achado inexistente nem regredir a aplicação para simular descoberta.

Resultados anteriores de pytest permanecem históricos. Não houve nova execução da suíte, scan ZAP, exploração de BOLA, brute force ou correção funcional nesta etapa. O ZIP continua reservado para o final.

## 8. Roteiro opcional de vídeo — 25 segundos

Mostrar o trecho didático e em seguida app/auth/policies.py: “Nesta análise, diferenciei autenticação de autorização. Buscar apenas pelo ID permitiria BOLA mesmo com usuário autenticado. Na versão atual, o filtro relaciona profissional e paciente antes de devolver a consulta. A leitura também revelou falta de limites globais no login, auditoria de segurança insuficiente e regras de conflito de agenda ainda por definir.”

Este trecho pode substituir parte da explicação do Exercício 6, sem aumentar o vídeo além de cinco minutos. Manter prioridade para a demonstração e para as decisões dos Exercícios 12 e 13.
