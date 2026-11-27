import io

import pytest
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app import cli
from app.auth import service
from app.models import User, UserSession
from app.security import verify_password

OLD = "old password 123"
NEW = "new password 456"


def _user_with_sessions(engine: Engine) -> None:
    with Session(engine) as db:
        user = service.register_user(db, "Alice", OLD)
        service.create_session(db, user)
        service.create_session(db, user)
        db.commit()


def _run(monkeypatch: pytest.MonkeyPatch, args: list[str], stdin: str = "") -> int:
    monkeypatch.setattr("sys.stdin", io.StringIO(stdin))
    return cli.main(args)


def test_reset_password_changes_hash_and_revokes_sessions(
    engine: Engine, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _user_with_sessions(engine)
    code = _run(monkeypatch, ["reset-password", "alice", "--password-stdin"], f"{NEW}\n")
    assert code == 0
    with Session(engine) as db:
        user = db.scalars(select(User)).one()
        assert verify_password(NEW, user.password_hash)
        assert not verify_password(OLD, user.password_hash)
        assert db.scalars(select(UserSession)).all() == []
    out = capsys.readouterr().out
    assert NEW not in out


def test_reset_password_interactive_requires_matching_entries(
    engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    _user_with_sessions(engine)
    answers = iter([NEW, "something else"])
    monkeypatch.setattr("getpass.getpass", lambda _prompt: next(answers))
    assert cli.main(["reset-password", "alice"]) == 1
    with Session(engine) as db:
        assert verify_password(OLD, db.scalars(select(User)).one().password_hash)


def test_reset_password_unknown_user_fails(
    engine: Engine, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    assert _run(monkeypatch, ["reset-password", "nobody", "--password-stdin"], f"{NEW}\n") == 1
    assert "No user named" in capsys.readouterr().err


def test_reset_password_enforces_min_length(
    engine: Engine, monkeypatch: pytest.MonkeyPatch
) -> None:
    _user_with_sessions(engine)
    assert _run(monkeypatch, ["reset-password", "alice", "--password-stdin"], "short\n") == 1
    with Session(engine) as db:
        assert verify_password(OLD, db.scalars(select(User)).one().password_hash)
