> **Estado atual (02/10/2026):** correções locais de M2M (Ex7), laboratório BOLA/XSS e mock de sucesso concluídas. Consulte [Correções de conformidade](Correcoes_Conformidade_2026-10-02.md) e a matriz atualizada. R21 permanece parcial até comprovar o check obrigatório em repositório GitHub próprio; vídeo pessoal e pacote final pendentes. As contagens e pendências abaixo são registros das etapas anteriores. Python 3.12 é mantido; o repositório do professor é apenas comparativo.

# Acompanhamento do Assessment

## Regras de trabalho

Implementar um exercício por vez e aguardar a revisão do usuário antes do próximo. Cada exercício terá revisão pelo modelo Astra, verificação contra a rubrica, decisões técnicas e evidências reais. Não inventar resultados de testes ou scans.

## Contexto

Recursos: pacientes, profissionais de saúde e consultas.
Clientes: frontend JSON, página HTML interna da recepção e laboratório parceiro M2M para horários disponíveis.
Papéis: recepcionista, profissional de saúde e administrador. As permissões concretas serão definidas conforme os exercícios.

## Entrega final

Código, relatório técnico, rastreabilidade do capstone, prints, payloads, pipeline GitHub Actions, saída real do ZAP e link do vídeo no YouTube não listado. ZIP somente no final, com nome Hebert_almeida_DR2_AT.ZIP. Excluir .venv, caches, bancos locais e segredos; revisar explicitamente os arquivos antes de compactar, pois .gitignore não filtra ZIP automaticamente.

## Vídeo

Até 5 minutos, gravado pelo aluno. Seleção provisória: autorização por recurso, security gate do Exercício 12 e capstone do Exercício 13. Ao terminar cada exercício selecionado, fornecer fala sugerida e demonstração. Consolidar roteiro ao final.

## Situação

Ambiente preparado. Exercício 1 implementado e revisado pelo Astra. Exercício 2 implementado e revisado pelo Astra, com 39 testes acumulados aprovados. As capturas de print dos exercícios 1 e 2 estão pendentes por falha da ferramenta; as demais evidências foram salvas. Exercício 3 concluído: análise CIA, frameworks e DFD em PNG/Mermaid, revisados pelo Astra sem pendências. Código da aplicação preservado. Exercício 4 concluído e aprovado pelo Astra: threat model com 14 ameaças, 10 misuse cases, STRIDE em quatro componentes e rastreabilidade para o capstone. Exercício 5 concluído e aprovado pelo Astra: arquitetura com oito partições, fluxos e fronteiras, 12 vetores nos três eixos e orientações para autenticação futura. Exercício 6 concluído e aprovado pelo Astra: OAuth2PasswordBearer, bcrypt, JWT com expiração e revogação, MFA simulado, RBAC e ownership centralizado. Validação: 70 testes + 1 concorrente e 20 cenários HTTP. Roteiro de 55 segundos incluído. Capturas da demonstração ainda pendentes, sem credenciais visíveis. Exercício 7 recebido e iniciado em staging externo, ainda não concluído, validado ou instalado. Exercício 8 concluído: análise manual OWASP aprovada pelo Astra, com três lacunas atuais e BOLA didática explicitamente distinta da proteção já implementada. Baseline da aplicação preservada. Exercício 9 concluído e aprovado pelo Astra em 25/09/2026: correções centralizadas, auditoria, limite de autenticação e conflitos de agenda conforme regra aprovada pelo usuário. 90 testes aprovados e comparação antes/depois real. Endpoint adicional /auth/browser-session corrigido; roteiro de 45 segundos incluído. Capturas da demonstração continuam pendentes. Exercício 10 concluído e aprovado pelo Astra: CORS, cabeçalhos e rate limiting diferenciado; 114 testes aprovados, 12 sondagens HTTP e roteiro opcional de 25 segundos. TLS real e capturas não comprovados. Exercício 11 concluído e aprovado pelo Astra: persistência em disco, parametrização, DI e configuração .env comprovadas; 127 testes aprovados. Exercício 12 concluído e aprovado pelo Astra: pipeline YAML, gate fail-closed, CVSS/negocio, 175 testes, scans reais e comparacao do gate. python-multipart atualizado0.0.32. ZAP passivo com9respostas/7alertas triados; IAST e execucao GitHub nao realizados. Exercício 13 concluído no escopo local em 25/09/2026 e aprovado pelo Astra: 190 testes, 65 verificações OpenAPI, ZAP passivo com nove respostas e dois alertas informativos. CSP/SRI corrigidos, rastreabilidade de 14 ameaças entregue, gate aprovado sem exceções Medium. Produção NO-GO; Exercício 7, controles operacionais, verificação visual/prints e vídeo pessoal continuam pendentes. Roteiro final de 4min50s disponível. ZIP somente ao final.
