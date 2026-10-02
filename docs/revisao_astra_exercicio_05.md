# Revisão independente — Exercício 5

Data: 22/09/2026. Revisor: agente astra_exercicio2, modelo gpt-6-astra, reutilizado para a revisão desta etapa.

Escopo: relatório de arquitetura, código existente, DFD do Exercício 3, threat model oficial do Exercício 4 e validador documental.

Achados corrigidos:

- Referências normalizadas para os IDs oficiais TH-xx, MT-xx e VT-xx. O validador rejeita referências sem hífen.
- AR01 passou a distinguir a autorização pretendida das respostas atuais sem autorização.
- AR06 passou a identificar data/clinica.db como caminho padrão configurável por DATABASE_URL.

Na segunda leitura, o Astra confirmou as correções, a coerência das oito partições, dos fluxos e fronteiras e dos 12 vetores nos três eixos. Parecer final: **Exercício 5 aprovado, sem pendências desta revisão.**

O revisor não editou arquivos nem executou testes ou o validador. A execução do validador é registrada separadamente em evidencias/exercicio_05/validacao_arquitetura.json. A aprovação refere-se ao artefato de arquitetura; não comprova implementação de autenticação ou proteção de infraestrutura futura.
