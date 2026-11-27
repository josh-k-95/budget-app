from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import service
from app.auth.deps import (
    SESSION_COOKIE,
    CurrentUser,
    DbDep,
    SettingsDep,
    clear_session_cookie,
    client_ip,
    get_rate_limits,
    require_secure_transport,
    set_session_cookie,
)
from app.auth.ratelimit import RateLimits
from app.models import User
from app.schemas.auth import (
    BudgetMembershipResponse,
    LoginRequest,
    RegisterRequest,
    UserResponse,
)
from app.security import password_problem, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

RateLimitsDep = Annotated[RateLimits, Depends(get_rate_limits)]
INVALID_CREDENTIALS = "Invalid username or password"


def signup_open(db: Session, allow_signup: bool) -> bool:
    """ALLOW_SIGNUP=false still lets the very first user register."""
    return allow_signup or service.count_users(db) == 0


def user_response(db: Session, user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        username=user.username,
        budgets=[
            BudgetMembershipResponse(id=m.budget_id, name=m.name, role=m.role)
            for m in service.user_memberships(db, user.id)
        ],
    )


def too_many_attempts(retry_after: int) -> HTTPException:
    return HTTPException(
        status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many attempts. Try again later.",
        headers={"Retry-After": str(retry_after)},
    )


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_secure_transport)],
)
def register(
    body: RegisterRequest,
    request: Request,
    response: Response,
    db: DbDep,
    settings: SettingsDep,
    limits: RateLimitsDep,
) -> UserResponse:
    ip = client_ip(request)
    if (wait := limits.register_ip.retry_after(ip)) is not None:
        raise too_many_attempts(wait)
    limits.register_ip.hit(ip)

    if not signup_open(db, settings.allow_signup):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="Registration is disabled")
    if problem := password_problem(body.password, settings.min_password_length):
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=problem)
    if service.find_user_by_username(db, body.username) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Username is already taken")

    try:
        user = service.register_user(db, body.username, body.password)
        token = service.create_session(db, user)
        db.commit()
    except IntegrityError:  # lost a race on the unique username index
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, detail="Username is already taken") from None

    set_session_cookie(response, token, settings)
    return user_response(db, user)


@router.post("/login", dependencies=[Depends(require_secure_transport)])
def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: DbDep,
    settings: SettingsDep,
    limits: RateLimitsDep,
) -> UserResponse:
    ip = client_ip(request)
    username_key = body.username.lower()
    wait = max(
        limits.login_username.retry_after(username_key) or 0,
        limits.login_ip.retry_after(ip) or 0,
    )
    if wait:
        raise too_many_attempts(wait)

    user = service.find_user_by_username(db, body.username)
    # Always run a hash verification (a dummy one for unknown users) to keep timing similar.
    if not verify_password(body.password, user.password_hash if user else None) or user is None:
        limits.login_username.hit(username_key)
        limits.login_ip.hit(ip)
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=INVALID_CREDENTIALS)

    limits.login_username.reset(username_key)
    token = service.create_session(db, user)
    db.commit()
    set_session_cookie(response, token, settings)
    return user_response(db, user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(request: Request, db: DbDep, settings: SettingsDep) -> Response:
    """Idempotent: deletes the session row if there is one and always clears the cookie."""
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        service.delete_session(db, token)
        db.commit()
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    clear_session_cookie(response, settings)
    return response


@router.get("/me")
def me(user: CurrentUser, db: DbDep) -> UserResponse:
    return user_response(db, user)
