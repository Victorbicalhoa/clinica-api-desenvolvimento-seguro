# Comprovar R21 — bloqueio de merge

Estado: preparação local concluída; repositório próprio e execução remota pendentes. O repositório do professor serve apenas para comparação e não deve receber esta entrega.

1. Criar/indicar repositório próprio e definir visibilidade. Conferir que o plano suporta proteção/rulesets para essa visibilidade; não transformar um repositório em público apenas para contornar limitação de plano sem autorização.
2. Publicar somente código, testes, configuração, documentos e evidências sanitizadas. Excluir `.env`, `.venv`, `.cache`, bancos, logs brutos de proxy, tokens e credenciais. `.gitignore` não protege arquivos já rastreados.
3. Executar o workflow `DevSecOps` e confirmar o nome real do check **security-gate**. Baixar os artifacts com pytest, Bandit, SCA, OpenAPI, ZAP e gate; registrar URL da execução e SHA do commit.
4. Proteger `main` exigindo PR e o check `security-gate`, atualização em relação à base e política de bypass que não permita ao autor da prova ignorar o check. Registrar/exportar a configuração. [Documentação oficial](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches).
5. Criar branch de prova e acrescentar somente um teste sentinela `def test_gate_demonstracao(): assert False, "Prova controlada do gate"` em arquivo de teste. Nenhuma vulnerabilidade precisa ser adicionada à aplicação. Abrir PR e aguardar falha do check. Registrar tela/estado de merge impedido, URL do PR, run e commit.
6. Remover apenas o sentinela, executar novamente e registrar check aprovado e condição de merge liberada. Não fazer merge do commit que contém a falha intencional. A prova pode terminar fechando o PR sem merge.
7. Anexar configuração, dois runs e estados do PR à pasta de evidências; atualizar R21 para atendida somente depois de verificar o bloqueio real. Os testes de política em `tests/test_security_gate.py` complementam a prova com cenários de severidade bloqueante.

Se o workflow ou a proteção não funcionar, corrigir antes de alegar conformidade. Capturas e URLs não devem conter segredos. O aluno deve explicar que pipeline reprovado e merge bloqueado são mecanismos relacionados, mas a regra da branch é necessária para tornar o resultado obrigatório.
