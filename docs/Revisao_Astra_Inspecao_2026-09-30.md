# Parecer Astra — inspeção final e roteiro do AT

**Data:** 30/09/2026 · **Revisor:** agente `astra_ex13_review`, GPT-6 Astra, conforme solicitação do usuário.

Foram realizadas três revisões somente leitura: aderência do projeto instalado às rúbricas/enunciados; comparação com o repositório do professor no commit `2b0a2060d11092850a702cda2469f6f8c123381d`; e revisão dos novos materiais de inspeção e ensaio. O Astra não executou novos scanners por conta própria; inspecionou o código, documentos e resultados gerados pela validação principal.

## Conclusão sobre a aplicação

Os 13 exercícios não estão integralmente concluídos. O Astra confirmou as lacunas de M2M/Ex7, bloqueio efetivo de merge, demonstração antes/depois de BOLA/XSS, mock do sucesso inicial do Ex1 e evidências finais. Confirmou também a divergência Python 3.12 versus a exigência 3.10/3.11 do README do starter.

O modelo Patient ausente foi classificado como simplificação funcional a esclarecer, não reprovação certa deduzida apenas do exemplo. A política que permite profissionais criarem consultas segue o enunciado específico do Ex6, embora conflite com o starter. Não se recomenda copiar permissões ou segredos didáticos do exemplo para enfraquecer a aplicação.

MFA real, TLS operacional, SIEM, backups e IAST executado não foram considerados automaticamente requisitos acadêmicos ausentes: a disciplina pede MFA simulado e justificativa do posicionamento de IAST. Esses pontos pertencem à avaliação de riscos de produção.

## Conclusão sobre os novos materiais

**Aprovados para entrega dos materiais de inspeção e ensaio**, sem bloqueador técnico identificado. Relatório, matriz e roteiro distinguem controles demonstrados, pendências acadêmicas e riscos operacionais. A matriz com 19 atendidos, quatro parciais e um não atendido está coerente e não é apresentada como nota.

O script de ensaio imprime respostas selecionadas, sem expor senhas/tokens/cookies. A evidência HTTP real sustenta os códigos e o escape descritos. Provisionamento, vínculo dos IDs, cookie para demonstração local e uso da mesma origem estão coerentes com o código revisado.

O Astra solicitou conferir os destinos `evidencias/inspecao_final_2026-09-30/` e `docs/video/demonstrar_api_video.py`, além de incluir este parecer. A instalação dos materiais deve respeitar esses destinos; a verificação de cópia é registrada separadamente.

Este parecer **não** autoriza afirmar conclusão integral dos 13 exercícios, M2M funcional, Swagger visualmente verificado, bloqueio remoto de merge comprovado ou autorização de produção.
