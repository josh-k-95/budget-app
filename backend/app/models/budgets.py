import uuid
from datetime import date

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, RecordMixin

NOT_DELETED = text("deleted_at IS NULL")


class Budget(RecordMixin, Base):
    """Owner of all domain data. Users reach it through budget_members."""

    __tablename__ = "budgets"

    name: Mapped[str]


class BudgetMember(RecordMixin, Base):
    __tablename__ = "budget_members"

    budget_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("budgets.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    role: Mapped[str]

    __table_args__ = (
        CheckConstraint("role IN ('owner', 'member')", name="role"),
        Index(
            "uq_budget_members_budget_user",
            "budget_id",
            "user_id",
            unique=True,
            postgresql_where=NOT_DELETED,
        ),
    )


class Account(RecordMixin, Base):
    __tablename__ = "accounts"

    budget_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("budgets.id"), index=True)
    name: Mapped[str]

    __table_args__ = (
        # Target for transactions' composite FK (keeps account and transaction in one budget).
        UniqueConstraint("budget_id", "id"),
    )


class Category(RecordMixin, Base):
    __tablename__ = "categories"

    budget_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("budgets.id"), index=True)
    name: Mapped[str]
    type: Mapped[str]

    __table_args__ = (
        CheckConstraint("type IN ('income', 'expense')", name="type"),
        UniqueConstraint("budget_id", "id"),
        Index(
            "uq_categories_budget_type_name_lower",
            "budget_id",
            "type",
            func.lower(text("name")),
            unique=True,
            postgresql_where=NOT_DELETED,
        ),
    )


class Transaction(RecordMixin, Base):
    __tablename__ = "transactions"

    budget_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("budgets.id"))
    account_id: Mapped[uuid.UUID]
    category_id: Mapped[uuid.UUID]
    amount: Mapped[int] = mapped_column(BigInteger)  # integer cents, always positive
    type: Mapped[str]
    descriptor: Mapped[str]
    date: Mapped[date]
    note: Mapped[str | None]

    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("type IN ('income', 'expense')", name="type"),
        ForeignKeyConstraint(
            ["budget_id", "account_id"],
            ["accounts.budget_id", "accounts.id"],
            name="fk_transactions_budget_account",
        ),
        ForeignKeyConstraint(
            ["budget_id", "category_id"],
            ["categories.budget_id", "categories.id"],
            name="fk_transactions_budget_category",
        ),
        Index("ix_transactions_budget_date", "budget_id", "date"),
    )
