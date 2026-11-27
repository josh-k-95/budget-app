"""CSRF defence: state-changing /api requests must come from PUBLIC_URL's origin.

Applies to cookie-authenticated browser requests. Future bearer-token clients (Android) must be
exempted explicitly rather than weakening this check.
"""

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from app.config import normalize_origin

UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


class OriginCheckMiddleware:
    def __init__(self, app: ASGIApp, allowed_origin: str) -> None:
        self.app = app
        self.allowed_origin = allowed_origin

    def _allowed(self, origin: str | None) -> bool:
        if origin is None or origin == "null":
            return False
        return normalize_origin(origin) == self.allowed_origin

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if (
            scope["type"] == "http"
            and scope["method"] in UNSAFE_METHODS
            and (scope["path"] == "/api" or scope["path"].startswith("/api/"))
        ):
            origin = None
            for name, value in scope["headers"]:
                if name == b"origin":
                    origin = value.decode("latin-1")
                    break
            if not self._allowed(origin):
                response = JSONResponse({"detail": "Origin not allowed"}, status_code=403)
                await response(scope, receive, send)
                return
        await self.app(scope, receive, send)
