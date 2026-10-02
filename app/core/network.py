from fastapi import FastAPI
from starlette.datastructures import MutableHeaders
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import Settings

CSP = (
    "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
    "font-src 'self'; connect-src 'self'; base-uri 'none'; form-action 'self'; "
    "frame-ancestors 'none'; object-src 'none'"
)


class RequestBodyLimit:
    def __init__(self, app: ASGIApp, limit: int):
        self.app, self.limit = app, limit

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        chunks, size = [], 0
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            body = message.get("body", b"")
            size += len(body)
            if size > self.limit:
                response = JSONResponse(
                    {"detail": "Corpo da requisicao excede o limite."},
                    status_code=413,
                    headers={"Cache-Control": "no-store"},
                )
                await response(scope, receive, send)
                return
            chunks.append(body)
            if not message.get("more_body", False):
                break
        delivered = False

        async def bounded_receive():
            nonlocal delivered
            if not delivered:
                delivered = True
                return {"type": "http.request", "body": b"".join(chunks), "more_body": False}
            return await receive()

        await self.app(scope, bounded_receive, send)


class SecurityHeaders:
    def __init__(self, app: ASGIApp, hsts_max_age: int):
        self.app = app
        self.hsts_max_age = hsts_max_age

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def secure_send(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(scope=message)
                headers["X-Frame-Options"] = "DENY"
                headers["X-Content-Type-Options"] = "nosniff"
                headers["Content-Security-Policy"] = CSP
                if scope.get("scheme") == "https":
                    headers["Strict-Transport-Security"] = f"max-age={self.hsts_max_age}"
                elif "Strict-Transport-Security" in headers:
                    del headers["Strict-Transport-Security"]
            await send(message)

        await self.app(scope, receive, secure_send)


class HardenedAPI(FastAPI):
    """Envolve inclusive ServerErrorMiddleware: cabecalhos tambem em erros e preflight."""

    def __init__(self, *, network_settings: Settings, **kwargs):
        self.network_settings = network_settings
        super().__init__(**kwargs)

    def build_middleware_stack(self) -> ASGIApp:
        inner = super().build_middleware_stack()
        bounded = RequestBodyLimit(inner, self.network_settings.max_request_body_bytes)
        cors = CORSMiddleware(
            bounded,
            allow_origins=self.network_settings.cors_allow_origins,
            allow_credentials=False,
            allow_methods=["GET", "POST", "PUT", "DELETE"],
            allow_headers=["Authorization", "Content-Type"],
            expose_headers=["Location", "Retry-After", "X-Request-ID"],
            max_age=600,
        )
        return SecurityHeaders(cors, hsts_max_age=self.network_settings.hsts_max_age)
