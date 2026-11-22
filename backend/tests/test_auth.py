"""Tests for /api/auth: registration, login and token checks."""

USER = {"email": "dm_test@example.com", "username": "DM_Master", "password": "SecurePassword123"}


def test_register_creates_user_and_returns_token(client):
    response = client.post("/api/auth/register", json=USER)
    assert response.status_code == 201
    body = response.json()
    assert body["token_type"] == "bearer" and body["access_token"]
    assert body["user"]["email"] == USER["email"]
    assert "password" not in body["user"] and "hashed_password" not in body["user"]


def test_duplicate_email_is_rejected(client):
    client.post("/api/auth/register", json=USER)
    response = client.post("/api/auth/register", json=USER)
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_short_password_and_bad_email_fail_validation(client):
    assert client.post("/api/auth/register", json={**USER, "password": "123"}).status_code == 422
    assert client.post("/api/auth/register", json={**USER, "email": "not-an-email"}).status_code == 422


def test_login_with_valid_and_invalid_credentials(client):
    client.post("/api/auth/register", json=USER)
    ok = client.post("/api/auth/login", json={"email": USER["email"], "password": USER["password"]})
    assert ok.status_code == 200 and ok.json()["access_token"]

    wrong = client.post("/api/auth/login", json={"email": USER["email"], "password": "wrong-password"})
    assert wrong.status_code == 401
    assert wrong.json()["detail"] == "Invalid email or password"

    unknown = client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "whatever1"})
    assert unknown.status_code == 401


def test_me_requires_valid_token(client):
    token = client.post("/api/auth/register", json=USER).json()["access_token"]
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer broken"}).status_code == 401
    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200 and me.json()["username"] == USER["username"]


def test_password_is_stored_as_bcrypt_hash(client):
    import sqlite3
    from app import database

    client.post("/api/auth/register", json=USER)
    row = sqlite3.connect(database.DB_PATH).execute("SELECT hashed_password FROM users").fetchone()
    assert row[0].startswith("$2b$12$") and USER["password"] not in row[0]


def test_logout_requires_token_and_succeeds_with_it(client):
    token = client.post("/api/auth/register", json=USER).json()["access_token"]
    assert client.post("/api/auth/logout").status_code == 401
    response = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out"


def test_server_log_messages_are_ascii_only():
    """Non-ASCII characters in print() crash the handler on consoles with a legacy code page."""
    import pathlib, re

    for path in pathlib.Path(__file__).resolve().parents[1].joinpath("app").rglob("*.py"):
        for call in re.findall(r"print\((.*)\)", path.read_text(encoding="utf-8")):
            assert call.isascii(), f"non-ASCII log message in {path.name}: {call}"
