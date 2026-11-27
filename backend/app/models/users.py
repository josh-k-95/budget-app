import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, LargeBinary, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, RecordMixin


class User(RecordMixin, Base):
    __tablename__ = "users"

    username: Mapped[str]
    password_hash: Mapped[str]

    __table_args__ = (
        Index(
            "uq_users_username_lower",
            func.lower(text("username")),
            unique=True,
            postgresql_where=text("deleted_at IS NULL"),
        ),
    )


class UserSession(RecordMixin, Base):
    """Login session. Only the SHA-256 hash of the token is stored. Logout hard-deletes the row."""

    __tablename__ = "sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    token_hash: Mapped[bytes] = mapped_column(LargeBinary(32), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class UserSettings(RecordMixin, Base):
    __tablename__ = "user_settings"

    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    feature_flags: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
