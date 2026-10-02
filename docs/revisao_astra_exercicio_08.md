# Revisão Astra — Exercício 8

Data: 24/09/2026. Revisor: agente astra_exercicio2, modelo gpt-6-astra, reutilizado para esta etapa.

Revisão somente leitura do código entregue, relatório e evidências. O staging não concluído do Exercício 7 foi excluído do escopo. Nenhum scanner, ataque ou teste foi executado pelo revisor.

O Astra confirmou:

- BOLA em A01/API1 apenas como instância didática; ownership já protege a versão atual. Não existe papel paciente ou rota de prontuário nessa baseline.
- A07: ausência de limite global de autenticação/emissão de desafios; cinco tentativas por desafio não são limite global.
- A09: ausência de trilha estruturada de eventos e alertas na aplicação; sessões e metadados não substituem auditoria.
- A06: ausência de desenho de conflito de agenda, condicionando a proibição de duplicidade à regra de negócio ainda por aprovar.
- Categorias, referências ao threat model e limites do relatório estão precisos; manifesto identifica 33 arquivos e extratos documentam dez arquivos completos com linhas numeradas.

**Parecer:** relatório aprovado tecnicamente, sem achados pendentes de conteúdo. A única pendência de empacotamento apontada foi incluir coletar_evidencias.py na pasta prometida; o script é incluído na entrega e sua execução documental final é registrada em validacao_documental.json.

A aprovação não declara descoberta de BOLA aberta, execução de testes exploratórios ou correção das lacunas identificadas.
