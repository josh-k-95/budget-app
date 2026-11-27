import uuid
from datetime import date

import pytest
from alembic import command
from alembic.util.exc import CommandError
from sqlalchemy import Engine, create_engine, inspect
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Account, Budget, Category, Transaction, User, UserSettings
from tests.conftest import TEST_DATABASE_URL, alembic_config, reset_schema

EXPECTED_TABLES = {
    "users",
    "sessions",
    "budgets",
    "budget_members",
    "accounts",
    "categories",
    "transactions",
    "user_settings",
}


def test_migrations_create_all_tables(engine: Engine) -> None:
    tables = set(inspect(engine).get_table_names())
    assert tables >= EXPECTED_TABLES
    for table in EXPECTED_TABLES:
        columns = {c["name"] for c in inspect(engine).get_columns(table)}
        assert {"id", "created_at", "updated_at", "deleted_at"} <= columns, table


def test_models_match_migrations(engine: Engine) -> None:
    """Fails if a model changed without a matching Alembic migration."""
    try:
        command.check(alembic_config())
    except CommandError as exc:  # pragma: no cover - message is the useful part
        pytest.fail(str(exc))


def test_downgrade_then_upgrade() -> None:
    scratch = create_engine(TEST_DATABASE_URL)
    try:
        command.downgrade(alembic_config(), "base")
        assert set(inspect(scratch).get_table_names()) <= {"alembic_version"}
        command.upgrade(alembic_config(), "head")
        assert set(inspect(scratch).get_table_names()) >= EXPECTED_TABLES
    finally:
        scratch.dispose()


def _budget_with_refs(db: Session) -> tuple[Budget, Account, Category]:
    budget = Budget(name="Personal")
    db.add(budget)
    db.flush()
    account = Account(budget_id=budget.id, name="Main")
    category = Category(budget_id=budget.id, name="Food", type="expense")
    db.add_all([account, category])
    db.flush()
    return budget, account, category


def _transaction(budget: Budget, account: Account, category: Category, **kw: object) -> Transaction:
    fields: dict[str, object] = {
        "budget_id": budget.id,
        "account_id": account.id,
        "category_id": category.id,
        "amount": 1250,
        "type": "expense",
        "descriptor": "Groceries",
        "date": date(2026, 11, 27),
    }
    fields.update(kw)
    return Transaction(**fields)


def test_valid_transaction_inserts(db: Session) -> None:
    budget, account, category = _budget_with_refs(db)
    tx = _transaction(budget, account, category)
    db.add(tx)
    db.flush()
    db.refresh(tx)
    assert isinstance(tx.id, uuid.UUID)
    assert tx.created_at is not None
    assert tx.deleted_at is None


@pytest.mark.parametrize("amount", [0, -100])
def test_amount_must_be_positive(db: Session, amount: int) -> None:
    budget, account, category = _budget_with_refs(db)
    db.add(_transaction(budget, account, category, amount=amount))
    with pytest.raises(IntegrityError, match="ck_transactions_amount_positive"):
        db.flush()


def test_transaction_type_is_checked(db: Session) -> None:
    budget, account, category = _budget_with_refs(db)
    db.add(_transaction(budget, account, category, type="transfer"))
    with pytest.raises(IntegrityError, match="ck_transactions_type"):
        db.flush()


def test_transaction_cannot_use_another_budgets_category(db: Session) -> None:
    budget_a, account_a, _ = _budget_with_refs(db)
    _, _, category_b = _budget_with_refs(db)
    db.add(_transaction(budget_a, account_a, category_b))
    with pytest.raises(IntegrityError, match="fk_transactions_budget_category"):
        db.flush()


def test_transaction_cannot_use_another_budgets_account(db: Session) -> None:
    budget_a, _, category_a = _budget_with_refs(db)
    _, account_b, _ = _budget_with_refs(db)
    db.add(_transaction(budget_a, account_b, category_a))
    with pytest.raises(IntegrityError, match="fk_transactions_budget_account"):
        db.flush()


def test_category_names_unique_per_budget_and_type_case_insensitive(db: Session) -> None:
    budget, _, _ = _budget_with_refs(db)
    db.add(Category(budget_id=budget.id, name="Salary", type="income"))
    db.add(Category(budget_id=budget.id, name="food", type="income"))  # same name, other type: ok
    db.flush()
    db.add(Category(budget_id=budget.id, name="FOOD", type="expense"))
    with pytest.raises(IntegrityError, match="uq_categories_budget_type_name_lower"):
        db.flush()


def test_usernames_unique_case_insensitive(db: Session) -> None:
    db.add(User(username="Alice", password_hash="x"))
    db.flush()
    db.add(User(username="alice", password_hash="x"))
    with pytest.raises(IntegrityError, match="uq_users_username_lower"):
        db.flush()


def test_user_settings_feature_flags_default_to_empty(db: Session) -> None:
    user = User(username="bob", password_hash="x")
    db.add(user)
    db.flush()
    settings = UserSettings(user_id=user.id)
    db.add(settings)
    db.flush()
    db.refresh(settings)
    assert settings.feature_flags == {}


def test_fresh_schema_reset_is_repeatable(engine: Engine) -> None:
    # Guard for the session fixture: resetting + upgrading twice must work.
    reset_schema(engine)
    command.upgrade(alembic_config(), "head")
    assert set(inspect(engine).get_table_names()) >= EXPECTED_TABLES
