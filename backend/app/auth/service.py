"""Users, registration and DB-backed sessions."""

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.models import Account, Budget, BudgetMember, User, UserSession, UserSettings
from app.security import hash_password, new_session_token, token_hash

SESSION_LIFETIME = timedelta(days=30)
# Sliding expiry is refreshed at most this often, to avoid a write on every request.
SESSION_TOUCH_INTERVAL = timedelta(hours=1)

DEFAULT_BUDGET_NAME = "Personal"
DEFAULT_ACCOUNT_NAME = "Main"


def utcnow() -> datetime:
    return datetime.now(UTC)


def find_user_by_username(db: Session, username: str) -> User | None:
    """Case-insensitive lookup among non-deleted users (uses uq_users_username_lower)."""
    return db.scalar(
        select(User).where(
            func.lower(User.username) == username.strip().lower(), User.deleted_at.is_(None)
        )
    )


def count_users(db: Session) -> int:
    return db.scalar(select(func.count()).select_from(User).where(User.deleted_at.is_(None))) or 0


def register_user(db: Session, username: str, password: str) -> User:
    """Create a user with a personal budget (owner), a "Main" account and settings.

    Flushes but does not commit; the caller owns the transaction.
    """
    user = User(username=username, password_hash=hash_password(password))
    budget = Budget(name=DEFAULT_BUDGET_NAME)
    db.add_all([user, budget])
    db.flush()
    db.add_all(
        [
            BudgetMember(budget_id=budget.id, user_id=user.id, role="owner"),
            Account(budget_id=budget.id, name=DEFAULT_ACCOUNT_NAME),
            UserSettings(user_id=user.id),
        ]
    )
    db.flush()
    return user


def create_session(db: Session, user: User) -> str:
    """Create a session row and return the raw token (for the cookie only)."""
    now = utcnow()
    db.execute(
        delete(UserSession).where(UserSession.user_id == user.id, UserSession.expires_at <= now)
    )
    token = new_session_token()
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=token_hash(token),
            expires_at=now + SESSION_LIFETIME,
            last_seen_at=now,
        )
    )
    db.flush()
    return token


def find_session(db: Session, token: str) -> tuple[UserSession, User] | None:
    row = db.execute(
        select(UserSession, User)
        .join(User, User.id == UserSession.user_id)
        .where(
            UserSession.token_hash == token_hash(token),
            UserSession.expires_at > utcnow(),
            UserSession.deleted_at.is_(None),
            User.deleted_at.is_(None),
        )
    ).first()
    return (row[0], row[1]) if row else None


def touch_session(session: UserSession) -> bool:
    """Extend a session's expiry if it was last refreshed a while ago. Returns True if changed."""
    now = utcnow()
    if now - session.last_seen_at < SESSION_TOUCH_INTERVAL:
        return False
    session.last_seen_at = now
    session.expires_at = now + SESSION_LIFETIME
    return True


def delete_session(db: Session, token: str) -> None:
    """Logout: hard-delete the session row."""
    db.execute(delete(UserSession).where(UserSession.token_hash == token_hash(token)))


def delete_user_sessions(db: Session, user_id: uuid.UUID) -> None:
    db.execute(delete(UserSession).where(UserSession.user_id == user_id))


@dataclass(frozen=True)
class Membership:
    budget_id: uuid.UUID
    name: str
    role: str


def user_memberships(db: Session, user_id: uuid.UUID) -> list[Membership]:
    rows = db.execute(
        select(Budget.id, Budget.name, BudgetMember.role)
        .join(BudgetMember, BudgetMember.budget_id == Budget.id)
        .where(
            BudgetMember.user_id == user_id,
            BudgetMember.deleted_at.is_(None),
            Budget.deleted_at.is_(None),
        )
        .order_by(Budget.created_at)
    ).all()
    return [Membership(budget_id=r[0], name=r[1], role=r[2]) for r in rows]


def user_budget_ids(db: Session, user_id: uuid.UUID) -> set[uuid.UUID]:
    """Budgets the user may access. Every domain query must be scoped to this set."""
    return {m.budget_id for m in user_memberships(db, user_id)}
