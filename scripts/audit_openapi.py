"""Auditoria estrutural do contrato; nao substitui testes runtime/autorizacao."""

import argparse
import json
from pathlib import Path

from app.core.config import Settings
from app.main import create_app


def audit(schema: dict) -> dict:
    checks = []

    def require(name, condition):
        checks.append({"check": name, "passed": bool(condition)})

    paths = schema["paths"]
    schemes = schema["components"]["securitySchemes"]
    require(
        "OAuth2 password aponta para auth/token",
        schemes["OAuth2PasswordBearer"]["flows"]["password"]["tokenUrl"] == "auth/token",
    )
    require("Bearer JWT explicito", schemes["JWTBearer"]["scheme"] == "bearer")
    require("Cookie de agenda documentado", schemes["AgendaCookie"]["name"] == "agenda_session")
    require(
        "M2M client credentials",
        schemes["LaboratorioOAuth2"]["flows"]["clientCredentials"]["tokenUrl"]
        == "integracoes/token",
    )
    operations = []
    identifiers = []
    for path, methods in paths.items():
        for method, operation in methods.items():
            if method not in {"get", "post", "put", "delete", "patch", "head", "options"}:
                continue
            identity = method.upper() + " " + path
            identifiers.append(operation["operationId"])
            public = (method, path) in {
                ("get", "/health"),
                ("post", "/auth/token"),
                ("post", "/auth/mfa"),
            }
            security = operation.get("security", [])
            if path == "/integracoes/token":
                expected_security = security == [{"ClientBasic": []}]
            elif path == "/integracoes/disponibilidade":
                expected_security = security == [{"LaboratorioOAuth2": ["disponibilidade:read"]}]
            else:
                expected_security = (
                    not security
                    if public
                    else {"OAuth2PasswordBearer": []} in security and {"JWTBearer": []} in security
                )
            require(
                identity + " autenticacao declarada",
                expected_security,
            )
            require(
                identity + " cookie so em agenda",
                ({"AgendaCookie": []} in security) == (path == "/agenda" and method == "get"),
            )
            require(identity + " 413 declarado", "413" in operation["responses"])
            if not public:
                require(
                    identity + " 401/403 declarados",
                    {"401", "403"} <= operation["responses"].keys(),
                )
            operations.append(
                {
                    "operation": identity,
                    "security": security,
                    "responses": sorted(operation["responses"]),
                }
            )
    require("operationIds unicos", len(identifiers) == len(set(identifiers)))
    token = paths["/auth/token"]["post"]
    form = token["requestBody"]["content"]["application/x-www-form-urlencoded"]["schema"]
    require(
        "Login requer grant_type username password",
        set(form["required"]) == {"grant_type", "username", "password"},
    )
    require("Login extra forbid", form["additionalProperties"] is False)
    require("Senha writeOnly", form["properties"]["password"]["writeOnly"] is True)
    for code, name in [("200", "TokenRead"), ("202", "DesafioRead")]:
        require(
            "Login resposta " + code,
            token["responses"][code]["content"]["application/json"]["schema"]
            == {"$ref": "#/components/schemas/" + name},
        )
    models = schema["components"]["schemas"]
    require(
        "Entrada consulta extra forbid", models["ConsultaWrite"]["additionalProperties"] is False
    )
    require(
        "Saida consulta allowlist",
        set(models["ConsultaRead"]["properties"])
        == {"id", "paciente_id", "profissional_id", "data_hora", "status", "observacao"},
    )
    require(
        "Persistencia interna nao exposta",
        not {"Consulta", "Usuario", "Sessao", "DesafioMFA", "OrcamentoAuth", "EventoAuditoria"}
        & models.keys(),
    )
    require(
        "Sem endpoints debug/fixture",
        not any(term in path for path in paths for term in ("debug", "seed", "fixture", "test")),
    )
    for path in ("/auth/browser-session", "/auth/logout"):
        body = paths[path]["post"]["requestBody"]["content"]["application/json"]["schema"]
        require(
            path + " corpo vazio/extra forbid",
            body["additionalProperties"] is False and not body["properties"],
        )
    require(
        "Logout sem quota geral documentada",
        "429" not in paths["/auth/logout"]["post"]["responses"],
    )
    return {
        "passed": all(check["passed"] for check in checks),
        "checks": checks,
        "operations": operations,
        "limits": (
            "Auditoria estrutural e de contrato; ownership e MFA requerem testes runtime; "
            "Fluxos humano e M2M separados; controles reais dependem de testes."
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("reports"))
    args = parser.parse_args()
    args.out.mkdir(exist_ok=True)
    schema = create_app(settings=Settings(_env_file=None)).openapi()
    result = audit(schema)
    (args.out / "openapi.json").write_text(json.dumps(schema, indent=2), encoding="utf-8")
    (args.out / "openapi-audit.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(f"OpenAPI: {len(result['checks'])} checks; passed={result['passed']}")
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
