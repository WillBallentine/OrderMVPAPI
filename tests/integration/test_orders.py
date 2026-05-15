"""Integration tests for the /api/v1/orders/ CRUD endpoints."""
import pytest

BASE = "/api/v1/orders"
VALID_PAYLOAD = {
    "patient_first_name": "Marie",
    "patient_last_name": "Curie",
    "patient_dob": "12/05/1900",
}


class TestCreateOrder:
    def test_creates_order_returns_201(self, client, auth):
        resp = client.post(f"{BASE}/", json=VALID_PAYLOAD, headers=auth)
        assert resp.status_code == 201
        data = resp.json()
        assert data["patient_first_name"] == "Marie"
        assert data["patient_last_name"] == "Curie"
        assert data["patient_dob"] == "12/05/1900"
        assert "id" in data
        assert "created_at" in data
        assert "updated_at" in data

    def test_create_returns_401_without_key(self, client):
        resp = client.post(f"{BASE}/", json=VALID_PAYLOAD)
        assert resp.status_code == 401

    def test_create_returns_401_wrong_key(self, client):
        resp = client.post(f"{BASE}/", json=VALID_PAYLOAD, headers={"X-API-Key": "wrong"})
        assert resp.status_code == 401

    def test_create_rejects_missing_fields(self, client, auth):
        resp = client.post(f"{BASE}/", json={"patient_first_name": "Marie"}, headers=auth)
        assert resp.status_code == 422

    def test_create_rejects_invalid_name_characters(self, client, auth):
        payload = {**VALID_PAYLOAD, "patient_first_name": "Marie123"}
        resp = client.post(f"{BASE}/", json=payload, headers=auth)
        assert resp.status_code == 422

    def test_create_rejects_empty_name(self, client, auth):
        payload = {**VALID_PAYLOAD, "patient_last_name": ""}
        resp = client.post(f"{BASE}/", json=payload, headers=auth)
        assert resp.status_code == 422

    def test_create_rejects_empty_dob(self, client, auth):
        payload = {**VALID_PAYLOAD, "patient_dob": ""}
        resp = client.post(f"{BASE}/", json=payload, headers=auth)
        assert resp.status_code == 422


class TestListOrders:
    def test_list_returns_empty_initially(self, client, auth):
        resp = client.get(f"{BASE}/", headers=auth)
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_returns_created_orders(self, client, auth, created_order):
        resp = client.get(f"{BASE}/", headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == created_order["id"]

    def test_list_requires_auth(self, client):
        assert client.get(f"{BASE}/").status_code == 401

    def test_list_pagination(self, client, auth):
        names = ["Alice", "Betty", "Carol", "Diana", "Edith"]
        for name in names:
            client.post(f"{BASE}/", json={**VALID_PAYLOAD, "patient_first_name": name}, headers=auth)
        resp = client.get(f"{BASE}/?skip=2&limit=2", headers=auth)
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_list_clamps_limit_at_500(self, client, auth):
        resp = client.get(f"{BASE}/?limit=9999", headers=auth)
        assert resp.status_code == 200  # clamped, not rejected


class TestGetOrder:
    def test_get_existing_order(self, client, auth, created_order):
        oid = created_order["id"]
        resp = client.get(f"{BASE}/{oid}", headers=auth)
        assert resp.status_code == 200
        assert resp.json()["id"] == oid

    def test_get_nonexistent_returns_404(self, client, auth):
        resp = client.get(f"{BASE}/99999", headers=auth)
        assert resp.status_code == 404

    def test_get_requires_auth(self, client, created_order):
        oid = created_order["id"]
        assert client.get(f"{BASE}/{oid}").status_code == 401


class TestUpdateOrder:
    def test_update_first_name(self, client, auth, created_order):
        oid = created_order["id"]
        resp = client.put(
            f"{BASE}/{oid}",
            json={"patient_first_name": "Maria"},
            headers=auth,
        )
        assert resp.status_code == 200
        assert resp.json()["patient_first_name"] == "Maria"
        assert resp.json()["patient_last_name"] == "Curie"  # unchanged

    def test_update_all_fields(self, client, auth, created_order):
        oid = created_order["id"]
        new = {"patient_first_name": "Ada", "patient_last_name": "Lovelace", "patient_dob": "12/10/1815"}
        resp = client.put(f"{BASE}/{oid}", json=new, headers=auth)
        assert resp.status_code == 200
        data = resp.json()
        assert data["patient_first_name"] == "Ada"
        assert data["patient_last_name"] == "Lovelace"

    def test_update_nonexistent_returns_404(self, client, auth):
        resp = client.put(f"{BASE}/99999", json={"patient_first_name": "X"}, headers=auth)
        assert resp.status_code == 404

    def test_update_rejects_invalid_name(self, client, auth, created_order):
        oid = created_order["id"]
        resp = client.put(f"{BASE}/{oid}", json={"patient_first_name": "Inv@lid!"}, headers=auth)
        assert resp.status_code == 422

    def test_update_requires_auth(self, client, created_order):
        oid = created_order["id"]
        resp = client.put(f"{BASE}/{oid}", json={"patient_first_name": "X"})
        assert resp.status_code == 401


class TestDeleteOrder:
    def test_delete_returns_204(self, client, auth, created_order):
        oid = created_order["id"]
        resp = client.delete(f"{BASE}/{oid}", headers=auth)
        assert resp.status_code == 204

    def test_deleted_order_is_gone(self, client, auth, created_order):
        oid = created_order["id"]
        client.delete(f"{BASE}/{oid}", headers=auth)
        resp = client.get(f"{BASE}/{oid}", headers=auth)
        assert resp.status_code == 404

    def test_delete_nonexistent_returns_404(self, client, auth):
        resp = client.delete(f"{BASE}/99999", headers=auth)
        assert resp.status_code == 404

    def test_delete_requires_auth(self, client, created_order):
        oid = created_order["id"]
        resp = client.delete(f"{BASE}/{oid}")
        assert resp.status_code == 401
