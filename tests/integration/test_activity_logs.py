"""Integration tests for activity logging."""
import pytest

LOGS_BASE = "/api/v1/activity-logs"
ORDERS_BASE = "/api/v1/orders"

VALID_ORDER = {
    "patient_first_name": "Marie",
    "patient_last_name": "Curie",
    "patient_dob": "12/05/1900",
}


class TestActivityLogging:
    def test_logs_require_auth(self, client):
        assert client.get(LOGS_BASE + "/").status_code == 401

    def test_create_order_generates_log(self, client, auth):
        client.post(f"{ORDERS_BASE}/", json=VALID_ORDER, headers=auth)
        logs = client.get(f"{LOGS_BASE}/", headers=auth).json()
        actions = [l["action"] for l in logs]
        assert "CREATE" in actions

    def test_get_order_generates_read_log(self, client, auth, created_order):
        oid = created_order["id"]
        client.get(f"{ORDERS_BASE}/{oid}", headers=auth)
        logs = client.get(f"{LOGS_BASE}/", headers=auth).json()
        assert any(l["action"] == "READ" and l["resource_id"] == str(oid) for l in logs)

    def test_update_order_generates_update_log(self, client, auth, created_order):
        oid = created_order["id"]
        client.put(f"{ORDERS_BASE}/{oid}", json={"patient_first_name": "Ada"}, headers=auth)
        logs = client.get(f"{LOGS_BASE}/", headers=auth).json()
        assert any(l["action"] == "UPDATE" for l in logs)

    def test_delete_order_generates_delete_log(self, client, auth, created_order):
        oid = created_order["id"]
        client.delete(f"{ORDERS_BASE}/{oid}", headers=auth)
        logs = client.get(f"{LOGS_BASE}/", headers=auth).json()
        assert any(l["action"] == "DELETE" for l in logs)

    def test_log_contains_response_status(self, client, auth):
        client.post(f"{ORDERS_BASE}/", json=VALID_ORDER, headers=auth)
        logs = client.get(f"{LOGS_BASE}/", headers=auth).json()
        create_log = next(l for l in logs if l["action"] == "CREATE")
        assert create_log["response_status"] == 201

    def test_failed_request_is_also_logged(self, client, auth):
        client.get(f"{ORDERS_BASE}/99999", headers=auth)  # 404
        logs = client.get(f"{LOGS_BASE}/", headers=auth).json()
        assert any(l["response_status"] == 404 for l in logs)

    def test_logs_are_returned_newest_first(self, client, auth):
        client.post(f"{ORDERS_BASE}/", json=VALID_ORDER, headers=auth)
        client.post(f"{ORDERS_BASE}/", json={**VALID_ORDER, "patient_first_name": "Ada"}, headers=auth)
        logs = client.get(f"{LOGS_BASE}/", headers=auth).json()
        assert len(logs) >= 2
        ids = [l["id"] for l in logs]
        assert ids == sorted(ids, reverse=True), "Logs must be returned newest (highest id) first"

    def test_log_pagination(self, client, auth):
        for i in range(5):
            client.post(f"{ORDERS_BASE}/", json={**VALID_ORDER, "patient_first_name": f"P{i}"}, headers=auth)
        resp = client.get(f"{LOGS_BASE}/?limit=2", headers=auth)
        assert resp.status_code == 200
        assert len(resp.json()) == 2
