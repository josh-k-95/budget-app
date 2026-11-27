"""FastAPI dependencies for authentication."""

from typing import Annotated

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.auth import service
from app.auth.ratelimit import RateLimits
from app.config import Settings, get_settings
from app.db import get_db
from app.models import User

SESSION_COOKIE = "session"
LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})

DbDep = Annotated[Session, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def set_session_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        SESSION_COOKIE,
        token,
        max_age=int(service.SESSION_LIFETIME.total_seconds()),
        path="/",
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
    )


def clear_session_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        SESSION_COOKIE, path="/", httponly=True, secure=settings.secure_cookies, samesite="lax"
    )


def get_current_user(
    request: Request, response: Response, db: DbDep, settings: SettingsDep
) -> User:
    token = request.cookies.get(SESSION_COOKIE)
    found = service.find_session(db, token) if token else None
    if found is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    session, user = found
    if service.touch_session(session):
        db.commit()
        set_session_cookie(response, token, settings)  # type: ignore[arg-type]  # token is set
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_secure_transport(request: Request, settings: SettingsDep) -> None:
    """Refuse to create sessions over plain HTTP, except on localhost or when explicitly allowed.

    The scheme reflects X-Forwarded-Proto from trusted proxies (Uvicorn --proxy-headers).
    """
    if request.url.scheme == "https" or settings.allow_insecure_http:
        return
    if request.url.hostname in LOCAL_HOSTS:
        return
    raise HTTPException(status.HTTP_403_FORBIDDEN, detail="HTTPS is required to sign in")


def get_rate_limits(request: Request) -> RateLimits:
    return request.app.state.rate_limits


def client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"
