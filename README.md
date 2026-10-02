# API de agendamento clínico — desenvolvimento seguro

API REST educacional com **FastAPI, SQLModel e Pydantic**, construída para demonstrar decisões de segurança em um sistema que representa agendamentos de clínicas. Use exclusivamente dados fictícios. O projeto não é um prontuário eletrônico nem está autorizado para produção.

## Funcionalidades e controles

- CRUD de consultas modularizado com APIRouter; consultas SQL parametrizadas e sessões injetadas.
- Autenticação com bcrypt, JWT com expiração/revogação, MFA administrativo simulado e autorização por papel e ownership.
- Client Credentials para laboratório, scope de disponibilidade e identidade/audience separadas dos usuários humanos.
- Contratos explícitos com `extra='forbid'`, response models e agenda Jinja2 com herança/autoescape.
- CORS com allowlist, cabeçalhos de segurança, limites de corpo e quotas por endpoint/identidade.
- Auditoria, threat model STRIDE, rastreabilidade e pipeline com pytest, Bandit, pip-audit e OWASP ZAP passivo.

## Executar localmente

Requer Python 3.12. No PowerShell, na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-security.txt
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m app.auth.provision demo_prof --papel profissional --profissional-id 1 --paciente-id 1
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

O provisionamento solicita uma senha exclusiva sem eco. Abra `http://127.0.0.1:8000/docs`, clique em **Authorize** e autentique `demo_prof` no esquema OAuth2PasswordBearer. O contrato de criação exige paciente/profissional vinculados. Configuração opcional em `.env`, a partir de `.env.example`; nunca publique segredos ou bancos. Sem chave configurada, reiniciar o servidor invalida tokens emitidos com a chave efêmera anterior.

## Verificar segurança

```powershell
.\.venv\Scripts\python.exe -m scripts.run_checks
.\.venv\Scripts\python.exe -m scripts.audit_openapi
.\.venv\Scripts\python.exe -m scripts.fetch_zap
.\.venv\Scripts\python.exe -m scripts.run_dast --zap-home .cache/security-tools/ZAP_2.17.0
.\.venv\Scripts\python.exe -m scripts.security_gate --reports reports
```

Java 21 e rede são necessários para o scan. O ZAP observa respostas de uma aplicação descartável em loopback, com dados fictícios. Não é scan ativo e não comprova TLS/infraestrutura. Os resultados atuais são apresentados nas evidências; a rodada local de 02/10/2026 aprovou 226 testes e 74 verificações OpenAPI.

O gate reprova falhas obrigatórias, evidências ausentes, severidades bloqueantes e vulnerabilidades de dependências. A demonstração remota de branch protection será documentada após sua execução; um YAML sozinho não comprova impedimento de merge.

## Documentação

- [Decisões e estado de conformidade](docs/Correcoes_Conformidade_2026-10-02.md)
- [Threat model STRIDE](docs/exercicio_04.md)
- [Integração M2M](docs/exercicio_07.md)
- [Pipeline, CVSS e impacto de negócio](docs/exercicio_12.md)
- [Capstone e riscos residuais](docs/exercicio_13.md)
- [Rastreabilidade atualizada](docs/Exercicio_13_Rastreabilidade_2026-10-02.json)

Os documentos de cada exercício preservam o estado histórico daquela etapa; a atualização de conformidade informa as correções posteriores. Produção permanece **NO-GO** até validar MFA real, TLS/proxy, proteção do banco, backups/restauração e operação. Os assets Swagger vendorizados mantêm seus arquivos LICENSE/NOTICE.
