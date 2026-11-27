from datetime import timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, select, update
from sqlalchemy.orm import Session

from app.auth import service
from app.auth.ratelimit import LOGIN_PER_IP, LOGIN_PER_USERNAME, REGISTER_PER_IP
from app.models import Account, Budget, BudgetMember, User, UserSession, UserSettings
from app.security import token_hash
from tests.conftest import make_client, make_settings

PASSWORD = "correct horse battery"


def register(client: TestClient, username: str = "alice", password: str = PASSWORD):
    return client.post("/api/auth/register", json={"username": username, "password": password})


def login(client: TestClient, username: str = "alice", password: str = PASSWORD):
    return client.post("/api/auth/login", json={"username": username, "password": password})


def set_cookie_header(response) -> str:
    return response.headers["set-cookie"]


# --- register ---------------------------------------------------------------------------


def test_register_creates_user_budget_membership_account_and_settings(
    client: TestClient, engine: Engine
) -> None:
    response = register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["username"] == "alice"
    assert len(body["budgets"]) == 1
    assert body["budgets"][0]["role"] == "owner"

    with Session(engine) as db:
        user = db.scalars(select(User)).one()
        assert user.password_hash.startswith("$argon2")
        assert PASSWORD not in user.password_hash
        member = db.scalars(select(BudgetMember)).one()
        assert (member.user_id, member.role) == (user.id, "owner")
        assert str(member.budget_id) == body["budgets"][0]["id"]
        account = db.scalars(select(Account)).one()
        assert (account.budget_id, account.name) == (member.budget_id, "Main")
        settings = db.scalars(select(UserSettings)).one()
        assert (settings.user_id, settings.feature_flags) == (user.id, {})


def test_register_logs_the_user_in(client: TestClient) -> None:
    register(client)
    assert client.get("/api/auth/me").json()["username"] == "alice"


def test_register_duplicate_username_any_case_conflicts(client: TestClient) -> None:
    assert register(client, "Alice").status_code == 201
    response = register(client, "aLICE")
    assert response.status_code == 409
    assert response.json() == {"detail": "Username is already taken"}


@pytest.mark.parametrize("username", ["ab", "x" * 33, "has space", "emoji🙂", ""])
def test_register_rejects_bad_usernames(client: TestClient, username: str) -> None:
    assert register(client, username).status_code == 422


def test_register_rejects_short_password(client: TestClient) -> None:
    response = register(client, password="short")
    assert response.status_code == 422
    assert response.json() == {"detail": "Password must be at least 8 characters"}


def test_register_respects_configured_min_password_length() -> None:
    with make_client(make_settings(min_password_length=12)) as client:
        assert register(client, password="elevenchars").status_code == 422
        assert register(client, password="twelve chars").status_code == 201


def test_register_rejects_overlong_password(client: TestClient) -> None:
    assert register(client, password="x" * 1025).status_code == 422


def test_signup_disabled_still_allows_first_user() -> None:
    with make_client(make_settings(allow_signup=False)) as client:
        assert client.get("/api/config").json()["signup_open"] is True
        assert register(client, "first").status_code == 201
        assert client.get("/api/config").json()["signup_open"] is False
        response = register(client, "second")
        assert response.status_code == 403
        assert response.json() == {"detail": "Registration is disabled"}


def test_register_is_rate_limited_per_ip() -> None:
    limit = REGISTER_PER_IP[0]
    with make_client(client_ip="198.51.100.1") as client:
        for i in range(limit):
            assert register(client, f"user{i}").status_code == 201
        response = register(client, "onemore")
        assert response.status_code == 429
        assert int(response.headers["retry-after"]) > 0
    # Separate app instance = separate in-memory counters, and another IP is unaffected anyway.
    with make_client(client_ip="198.51.100.2") as other:
        assert register(other, "onemore").status_code == 201


def test_register_rate_limit_counts_failed_attempts_too(client: TestClient) -> None:
    limit = REGISTER_PER_IP[0]
    for _ in range(limit):
        register(client, password="short")
    assert register(client, "valid").status_code == 429


# --- login ------------------------------------------------------------------------------


def test_login_sets_secure_session_cookie_attributes() -> None:
    settings = make_settings(public_url="https://budget.example.test")
    with make_client(
        settings, base_url="https://budget.example.test", origin="https://budget.example.test"
    ) as client:
        register(client)
        response = login(client)
    assert response.status_code == 200
    cookie = set_cookie_header(response).lower()
    assert cookie.startswith("session=")
    assert "httponly" in cookie
    assert "secure" in cookie
    assert "samesite=lax" in cookie
    assert "path=/" in cookie
    assert f"max-age={30 * 24 * 3600}" in cookie


def test_login_cookie_not_secure_for_localhost_public_url(client: TestClient) -> None:
    register(client)
    cookie = set_cookie_header(login(client)).lower()
    assert "secure" not in cookie
    assert "httponly" in cookie


def test_only_token_hash_is_stored(client: TestClient, engine: Engine) -> None:
    register(client)
    response = login(client)
    token = response.cookies["session"]
    with Session(engine) as db:
        hashes = set(db.scalars(select(UserSession.token_hash)))
    assert token_hash(token) in hashes
    assert token.encode() not in hashes


def test_login_is_case_insensitive(client: TestClient) -> None:
    register(client, "Alice")
    response = login(client, "alice")
    assert response.status_code == 200
    assert response.json()["username"] == "Alice"
    assert login(client, "  ALICE ").status_code == 200


def test_wrong_password_and_unknown_user_look_the_same(client: TestClient) -> None:
    register(client)
    wrong = login(client, password="wrong password")
    unknown = login(client, "nobody")
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"detail": "Invalid username or password"}
    assert "set-cookie" not in wrong.headers


def test_login_rate_limited_per_username_across_case_variants(client: TestClient) -> None:
    register(client, "alice")
    limit = LOGIN_PER_USERNAME[0]
    for i in range(limit):
        name = "ALICE" if i % 2 else "alice"
        assert login(client, name, "wrong password").status_code == 401
    # Even the correct password is refused while limited.
    response = login(client, "Alice")
    assert response.status_code == 429
    assert int(response.headers["retry-after"]) > 0


def test_login_rate_limited_per_ip(client: TestClient) -> None:
    register(client, "alice")
    limit = LOGIN_PER_IP[0]
    for i in range(limit):
        login(client, f"nobody{i}", "wrong password")
    assert login(client).status_code == 429


def test_successful_login_resets_username_counter(client: TestClient) -> None:
    register(client)
    for _ in range(LOGIN_PER_USERNAME[0] - 1):
        login(client, password="wrong password")
    assert login(client).status_code == 200
    for _ in range(LOGIN_PER_USERNAME[0] - 1):
        assert login(client, password="wrong password").status_code == 401
    assert login(client).status_code == 200


# --- session, me, logout ----------------------------------------------------------------


def test_me_requires_a_session(client: TestClient) -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


def test_me_rejects_garbage_cookie(client: TestClient) -> None:
    client.cookies.set("session", "not-a-real-token")
    assert client.get("/api/auth/me").status_code == 401


def test_me_lists_only_own_budgets(engine: Engine) -> None:
    with make_client() as alice, make_client() as bob:
        a = register(alice, "alice").json()
        b = register(bob, "bob").json()
        me_a = alice.get("/api/auth/me").json()
        me_b = bob.get("/api/auth/me").json()
    assert me_a["id"] == a["id"] and me_b["id"] == b["id"]
    assert me_a["budgets"] == [{"id": a["budgets"][0]["id"], "name": "Personal", "role": "owner"}]
    assert me_a["budgets"][0]["id"] != me_b["budgets"][0]["id"]


def test_logout_deletes_session_and_invalidates_cookie(client: TestClient, engine: Engine) -> None:
    register(client)
    token = client.cookies["session"]
    response = client.post("/api/auth/logout")
    assert response.status_code == 204
    assert (
        'session=""' in set_cookie_header(response)
        or "max-age=0" in set_cookie_header(response).lower()
    )
    with Session(engine) as db:
        assert db.scalars(select(UserSession)).all() == []
    client.cookies.set("session", token)  # replaying the old cookie must not work
    assert client.get("/api/auth/me").status_code == 401


def test_logout_without_session_is_harmless(client: TestClient) -> None:
    assert client.post("/api/auth/logout").status_code == 204


def test_expired_session_is_rejected(client: TestClient, engine: Engine) -> None:
    register(client)
    with Session(engine) as db:
        db.execute(update(UserSession).values(expires_at=service.utcnow() - timedelta(seconds=1)))
        db.commit()
    assert client.get("/api/auth/me").status_code == 401


def test_session_expiry_slides_after_touch_interval(client: TestClient, engine: Engine) -> None:
    register(client)
    old = service.utcnow() - timedelta(days=2)
    with Session(engine) as db:
        db.execute(
            update(UserSession).values(last_seen_at=old, expires_at=old + timedelta(days=30))
        )
        db.commit()
    response = client.get("/api/auth/me")
    assert response.status_code == 200
    assert "session=" in set_cookie_header(response)
    with Session(engine) as db:
        session = db.scalars(select(UserSession)).one()
    assert session.expires_at > service.utcnow() + timedelta(days=29)


def test_recent_session_is_not_rewritten_on_every_request(client: TestClient) -> None:
    register(client)
    response = client.get("/api/auth/me")
    assert "set-cookie" not in response.headers


def test_deleted_user_session_is_rejected(client: TestClient, engine: Engine) -> None:
    register(client)
    with Session(engine) as db:
        db.execute(update(User).values(deleted_at=service.utcnow()))
        db.commit()
    assert client.get("/api/auth/me").status_code == 401


def test_login_cleans_up_expired_sessions(client: TestClient, engine: Engine) -> None:
    register(client)
    with Session(engine) as db:
        db.execute(update(UserSession).values(expires_at=service.utcnow() - timedelta(days=1)))
        db.commit()
    login(client)
    with Session(engine) as db:
        assert len(db.scalars(select(UserSession)).all()) == 1


# --- membership scoping -----------------------------------------------------------------


def test_user_budget_ids_never_include_other_users_budgets(engine: Engine) -> None:
    with Session(engine) as db:
        alice = service.register_user(db, "alice", PASSWORD)
        bob = service.register_user(db, "bob", PASSWORD)
        # Bob gets an extra budget he owns.
        extra = Budget(name="Bob's side project")
        db.add(extra)
        db.flush()
        db.add(BudgetMember(budget_id=extra.id, user_id=bob.id, role="owner"))
        db.commit()

        alice_ids = service.user_budget_ids(db, alice.id)
        bob_ids = service.user_budget_ids(db, bob.id)
        alice_personal = {m.budget_id for m in service.user_memberships(db, alice.id)}

    assert alice_ids == alice_personal
    assert len(alice_ids) == 1
    assert len(bob_ids) == 2
    assert alice_ids.isdisjoint(bob_ids)


def test_user_budget_ids_exclude_soft_deleted_memberships_and_budgets(engine: Engine) -> None:
    with Session(engine) as db:
        alice = service.register_user(db, "alice", PASSWORD)
        shared = Budget(name="Shared")
        gone = Budget(name="Gone", deleted_at=service.utcnow())
        db.add_all([shared, gone])
        db.flush()
        db.add_all(
            [
                BudgetMember(
                    budget_id=shared.id,
                    user_id=alice.id,
                    role="member",
                    deleted_at=service.utcnow(),
                ),
                BudgetMember(budget_id=gone.id, user_id=alice.id, role="owner"),
            ]
        )
        shared_id, gone_id, alice_id = shared.id, gone.id, alice.id
        db.commit()
        ids = service.user_budget_ids(db, alice_id)
    assert shared_id not in ids
    assert gone_id not in ids
    assert len(ids) == 1
