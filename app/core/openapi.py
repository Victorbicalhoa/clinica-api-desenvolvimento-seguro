"""Contrato publico coerente com validacao manual e controles do middleware."""

from fastapi import FastAPI

from app.models.entrada import CorpoVazio, LoginForm
from app.models.integracao import SCOPE_AVAILABILITY, ClientCredentialsForm


def configure_openapi(app: FastAPI) -> None:
    original = app.openapi

    def documented_openapi():
        schema = original()
        schemes = schema["components"]["securitySchemes"]
        schemes["LaboratorioOAuth2"] = {
            "type": "oauth2",
            "flows": {
                "clientCredentials": {
                    "tokenUrl": "integracoes/token",
                    "scopes": {
                        SCOPE_AVAILABILITY: "Ler somente horarios explicitamente ofertados."
                    },
                }
            },
        }
        schemes["JWTBearer"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT obtido no login ou apos confirmar MFA.",
        }
        schemes["AgendaCookie"] = {
            "type": "apiKey",
            "in": "cookie",
            "name": "agenda_session",
            "description": "Cookie aceito somente no GET /agenda.",
        }
        paths = schema["paths"]
        token = paths["/auth/token"]["post"]
        token["requestBody"] = {
            "required": True,
            "content": {
                "application/x-www-form-urlencoded": {"schema": LoginForm.model_json_schema()}
            },
        }
        token["responses"]["200"]["content"]["application/json"]["schema"] = {
            "$ref": "#/components/schemas/TokenRead"
        }
        token["responses"]["202"] = {
            "description": "MFA administrativo pendente; sem access_token.",
            "content": {
                "application/json": {"schema": {"$ref": "#/components/schemas/DesafioRead"}}
            },
        }
        token["description"] = (
            "OAuth2 password para humanos. Administrador recebe 202 e deve confirmar /auth/mfa; "
            "depois pode usar JWTBearer no Swagger. M2M usa /integracoes/token, separado. "
            "Senha limitada a 72 bytes UTF-8; campos duplicados, extras e query sao rejeitados."
        )
        for path, methods in paths.items():
            for method, operation in methods.items():
                if method not in {"get", "post", "put", "delete", "patch", "head", "options"}:
                    continue
                responses = operation["responses"]
                if path == "/integracoes/disponibilidade":
                    operation["security"] = [{"LaboratorioOAuth2": [SCOPE_AVAILABILITY]}]
                responses.setdefault(
                    "413", {"description": "Corpo maior que o limite configurado."}
                )
                if operation.get("security"):
                    if not path.startswith("/integracoes/"):
                        operation["security"] = [{"OAuth2PasswordBearer": []}, {"JWTBearer": []}]
                    if path == "/agenda" and method == "get":
                        operation["security"].append({"AgendaCookie": []})
                    responses.setdefault(
                        "401", {"description": "Credencial ausente, invalida ou revogada."}
                    )
                    responses.setdefault("403", {"description": "Papel ou vinculo nao autorizado."})
                    responses.setdefault(
                        "503", {"description": "Persistencia ou auditoria indisponivel."}
                    )
                if path not in {"/health", "/auth/logout"}:
                    responses.setdefault(
                        "429",
                        {
                            "description": "Orcamento esgotado; consultar Retry-After.",
                            "headers": {
                                "Retry-After": {"schema": {"type": "integer", "minimum": 1}}
                            },
                        },
                    )
                if path.startswith("/consultas") and method in {"post", "put", "delete"}:
                    responses.setdefault(
                        "409", {"description": "Conflito de persistencia ou estado."}
                    )
                if "{consulta_id}" in path:
                    responses.setdefault(
                        "404", {"description": "Consulta nao encontrada ou fora do ownership."}
                    )
        for path in ("/auth/token", "/auth/mfa"):
            for code, text in {
                "401": "Autenticacao negada.",
                "422": "Entrada invalida.",
                "503": "MFA, persistencia ou auditoria indisponivel.",
            }.items():
                paths[path]["post"]["responses"].setdefault(code, {"description": text})
        token["responses"]["415"] = {"description": "Tipo de formulario nao suportado."}
        machine = paths["/integracoes/token"]["post"]
        machine["requestBody"] = {
            "required": True,
            "content": {
                "application/x-www-form-urlencoded": {
                    "schema": ClientCredentialsForm.model_json_schema()
                }
            },
        }
        machine["description"] = (
            "Client credentials com HTTP Basic. Nunca usar credenciais humanas. "
            "Scope omitido concede disponibilidade:read; scope vazio/desconhecido e rejeitado. "
            "Token expira em 300 segundos, sem refresh token; requer TLS fora de loopback."
        )
        machine["responses"]["400"] = {"description": "invalid_request ou invalid_scope."}
        for path in ("/auth/logout", "/auth/browser-session"):
            paths[path]["post"]["responses"]["422"] = {"description": "Corpo ou query invalido."}
            paths[path]["post"]["requestBody"] = {
                "required": False,
                "content": {"application/json": {"schema": CorpoVazio.model_json_schema()}},
            }
        return schema

    app.openapi = documented_openapi
