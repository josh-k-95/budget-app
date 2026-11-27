from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from app.api import api_router
from app.auth.csrf import OriginCheckMiddleware
from app.auth.ratelimit import RateLimits
from app.config import Settings, get_settings


def _mount_frontend(app: FastAPI, dist: Path) -> None:
    """Serve the built SPA: real files when they exist, otherwise index.html."""
    dist = dist.resolve()
    index = dist / "index.html"

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa(full_path: str) -> FileResponse:
        if full_path == "api" or full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = (dist / full_path).resolve()
        if full_path and candidate.is_relative_to(dist) and candidate.is_file():
            return FileResponse(candidate)
        if not index.is_file():
            raise HTTPException(status_code=404, detail="Frontend not built")
        return FileResponse(index)


def create_app(settings: Settings | None = None) -> FastAPI:
    explicit = settings is not None
    settings = settings or get_settings()
    app = FastAPI(
        title=settings.app_name,
        docs_url="/api/docs",
        redoc_url=None,
        openapi_url="/api/openapi.json",
    )
    if explicit:
        app.dependency_overrides[get_settings] = lambda: settings
    app.state.rate_limits = RateLimits()
    app.add_middleware(OriginCheckMiddleware, allowed_origin=settings.public_origin)
    app.include_router(api_router)
    _mount_frontend(app, settings.frontend_dist)
    return app


app = create_app()
