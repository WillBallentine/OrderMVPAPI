"""Integration tests for /api/v1/users/ endpoints."""

BASE = "/api/v1/users"


class TestGetMe:
    def test_get_me_returns_current_user(self, client, jwt_auth):
        resp = client.get(f"{BASE}/me", headers=jwt_auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["username"] == "testuser"
        assert data["role"] == "user"

    def test_get_me_requires_jwt_not_api_key(self, client, auth):
        resp = client.get(f"{BASE}/me", headers=auth)
        assert resp.status_code == 403

    def test_get_me_requires_auth(self, client):
        resp = client.get(f"{BASE}/me")
        assert resp.status_code == 401


class TestListUsers:
    def test_list_users_requires_admin(self, client, jwt_auth):
        resp = client.get(f"{BASE}/", headers=jwt_auth)
        assert resp.status_code == 403

    def test_list_users_admin_can_access(self, client, admin_jwt_auth):
        resp = client.get(f"{BASE}/", headers=admin_jwt_auth)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_list_users_requires_auth(self, client):
        resp = client.get(f"{BASE}/")
        assert resp.status_code == 401
