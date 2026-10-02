# Revisão Astra — conformidade de 02/10/2026

Revisor: agente Astra solicitado pelo aluno. Revisão de código/documentação; os comandos de teste e scanners foram executados pelo agente principal, com arquivos de evidência inspecionados pelo revisor.

Na primeira revisão, o Astra solicitou mover as operações SQLite/bcrypt/quota do grant M2M para threadpool e aplicar a quota de client_id antes do lookup, inclusive para clientes inexistentes. Ambos corrigidos. Foram adicionados testes da sequência idêntica de limites e da recusa a cliente desativado.

Na revisão documental, solicitou distinguir revogação humana por sessão/JTI da versão M2M, preservar TB4 para a fronteira parceiro/clínica e atualizar R23 para as evidências de 02/10. Os três pontos foram corrigidos.

Parecer final recebido:

> Aprovado no escopo local, sem bloqueadores técnicos identificados na versão revisada. Evidências coerentes: 226 testes, 74 verificações OpenAPI, SCA sem vulnerabilidades reportadas e gate aprovado. Permanecem registrados dois Bandit LOW triados e dois ZAP informativos em 12 respostas.

> 23 de 24 rubricas possuem evidência local suficiente; R21 permanece parcial, aguardando execução GitHub e bloqueio efetivo de merge. Isso não representa nota nem garantia de aprovação acadêmica.

O parecer antecedeu a incorporação ao projeto. A instalação é comprovada separadamente pelo manifesto de hashes e pela verificação do ambiente instalado. Capturas, vídeo e ZIP permanecem etapas da entrega. A decisão operacional continua NO-GO para produção.
