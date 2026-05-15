"""Integration tests for POST /api/v1/orders/batch."""

BASE = "/api/v1/orders/batch"
VALID_ORDER = {"patient_first_name": "Marie", "patient_last_name": "Curie", "patient_dob": "12/05/1900"}


class TestBatchCreateOrders:
    def test_batch_creates_multiple_orders(self, client, auth):
        payload = [
            {"patient_first_name": "Alice", "patient_last_name": "Smith", "patient_dob": "01/01/1990"},
            {"patient_first_name": "Betty", "patient_last_name": "Jones", "patient_dob": "02/02/1985"},
            {"patient_first_name": "Carol", "patient_last_name": "Brown", "patient_dob": "03/03/1975"},
        ]
        resp = client.post(BASE, json=payload, headers=auth)
        assert resp.status_code == 201
        data = resp.json()
        assert len(data) == 3
        assert data[0]["patient_first_name"] == "Alice"
        assert data[2]["patient_first_name"] == "Carol"

    def test_batch_ids_are_unique(self, client, auth):
        payload = [VALID_ORDER, VALID_ORDER, VALID_ORDER]
        resp = client.post(BASE, json=payload, headers=auth)
        assert resp.status_code == 201
        ids = [o["id"] for o in resp.json()]
        assert len(set(ids)) == 3

    def test_batch_persists_to_list(self, client, auth):
        payload = [VALID_ORDER, VALID_ORDER]
        client.post(BASE, json=payload, headers=auth)
        list_resp = client.get("/api/v1/orders/", headers=auth)
        assert len(list_resp.json()) == 2

    def test_batch_empty_list_returns_400(self, client, auth):
        resp = client.post(BASE, json=[], headers=auth)
        assert resp.status_code == 400

    def test_batch_exceeds_100_returns_400(self, client, auth):
        payload = [VALID_ORDER] * 101
        resp = client.post(BASE, json=payload, headers=auth)
        assert resp.status_code == 400

    def test_batch_requires_auth(self, client):
        resp = client.post(BASE, json=[VALID_ORDER])
        assert resp.status_code == 401

    def test_batch_validates_each_order(self, client, auth):
        payload = [
            VALID_ORDER,
            {"patient_first_name": "Bad123", "patient_last_name": "Name", "patient_dob": "01/01/2000"},
        ]
        resp = client.post(BASE, json=payload, headers=auth)
        assert resp.status_code == 422

    def test_batch_works_with_jwt(self, client, jwt_auth):
        payload = [VALID_ORDER, VALID_ORDER]
        resp = client.post(BASE, json=payload, headers=jwt_auth)
        assert resp.status_code == 201
        assert len(resp.json()) == 2
