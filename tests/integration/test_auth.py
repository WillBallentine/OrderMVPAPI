"""Integration tests for /api/v1/auth/ endpoints."""

BASE = "/api/v1/auth"
REGISTER = f"{BASE}/register"
LOGIN = f"{BASE}/login"


class TestRegister:
    def test_register_creates_user(self, client):
        resp = client.post(REGISTER, json={"username": "newuser", "password": "password1"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["username"] == "newuser"
        assert data["role"] == "user"
        assert data["is_active"] is True
        assert "id" in data
        assert "hashed_password" not in data

    def test_register_duplicate_username_returns_409(self, client):
        client.post(REGISTER, json={"username": "dupuser", "password": "password1"})
        resp = client.post(REGISTER, json={"username": "dupuser", "password": "password2"})
        assert resp.status_code == 409

    def test_register_short_username_returns_422(self, client):
        resp = client.post(REGISTER, json={"username": "ab", "password": "password1"})
        assert resp.status_code == 422

    def test_register_invalid_username_chars_returns_422(self, client):
        resp = client.post(REGISTER, json={"username": "bad user!", "password": "password1"})
        assert resp.status_code == 422

    def test_register_short_password_returns_422(self, client):
        resp = client.post(REGISTER, json={"username": "validuser", "password": "short"})
        assert resp.status_code == 422


class TestLogin:
    def test_login_returns_token(self, client):
        client.post(REGISTER, json={"username": "loginuser", "password": "password1"})
        resp = client.post(LOGIN, data={"username": "loginuser", "password": "password1"})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password_returns_401(self, client):
        client.post(REGISTER, json={"username": "loginuser2", "password": "password1"})
        resp = client.post(LOGIN, data={"username": "loginuser2", "password": "wrongpass"})
        assert resp.status_code == 401

    def test_login_nonexistent_user_returns_401(self, client):
        resp = client.post(LOGIN, data={"username": "ghost", "password": "password1"})
        assert resp.status_code == 401

    def test_jwt_token_grants_access_to_orders(self, client, jwt_auth):
        resp = client.get("/api/v1/orders/", headers=jwt_auth)
        assert resp.status_code == 200
