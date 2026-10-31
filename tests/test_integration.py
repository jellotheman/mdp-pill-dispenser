import json

import pytest
from fastapi.testclient import TestClient
from integration.service import create_app

TOKEN = "test-only-token"


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / "service.sqlite3", TOKEN),
                    headers={"Authorization": "Bearer " + TOKEN}) as c:
        yield c


PREFIX = "/api/v1/devices/test-device"
UPDATE = {"expected_revision": 0, "timezone": "Asia/Kolkata", "schedules": [
    {"id": "morning", "time": "08:00", "compartment": 1, "enabled": True, "auth_user_id": 7}
]}


def event(name="dispensed"):
    return {"schema_version": 2, "event_id": "test-device:session:1", "device_id": "test-device",
            "session_id": "session", "event": name, "state": "COMPLETED" if name == "dispensed" else "MISSED",
            "elapsed_ms": 100, "occurred_at": None, "dose_id": "2026-10-31:morning",
            "schedule_id": "morning", "compartment": 1, "revision": 1,
            "reason": None, "observed_count": 1, "simulated": True}


def test_saved_and_applied_are_distinct(client):
    response = client.put(PREFIX + "/config", json=UPDATE)
    assert response.status_code == 200
    assert response.json()["revision"] == 1
    assert not client.get(PREFIX + "/status").json()["synchronized"]
    client.post(PREFIX + "/config-acks", json={"revision": 1, "status": "applied"})
    assert client.get(PREFIX + "/status").json()["synchronized"]


def test_concurrent_app_edit_uses_expected_revision(client):
    assert client.put(PREFIX + "/config", json=UPDATE).status_code == 200
    assert client.put(PREFIX + "/config", json=UPDATE).status_code == 409


@pytest.mark.parametrize("status", ["deferred", "rejected"])
def test_deferred_or_rejected_does_not_claim_applied(client, status):
    client.put(PREFIX + "/config", json=UPDATE)
    client.post(PREFIX + "/config-acks", json={"revision": 1, "status": status})
    assert not client.get(PREFIX + "/status").json()["synchronized"]


def test_ack_for_unknown_revision_is_rejected(client):
    assert client.post(PREFIX + "/config-acks", json={"revision": 99, "status": "applied"}).status_code == 409


def test_missing_token_rejected(client):
    assert client.get(PREFIX + "/config", headers={"Authorization": ""}).status_code == 401


def test_replayed_event_returns_same_ack_and_one_history_entry(client):
    first = client.post(PREFIX + "/events", json=event())
    second = client.post(PREFIX + "/events", json=event())
    assert first.json()["duplicate"] is False
    assert second.json()["duplicate"] is True
    assert len(client.get(PREFIX + "/history").json()) == 1


def test_event_id_cannot_be_reused_with_changed_content(client):
    data = event()
    client.post(PREFIX + "/events", json=data)
    data["observed_count"] = 2
    assert client.post(PREFIX + "/events", json=data).status_code == 409


def test_device_identity_checked(client):
    data = event()
    data["device_id"] = "other"
    assert client.post(PREFIX + "/events", json=data).status_code == 422


def test_mock_sms_deduplicated_with_event(client):
    for _ in range(3):
        assert client.post(PREFIX + "/events", json=event("missed")).status_code == 200
    notifications = client.get(PREFIX + "/notifications").json()
    assert len(notifications) == 1
    assert notifications[0]["status"] == "simulated"


@pytest.mark.parametrize("change", [
    {"time": "24:00"}, {"compartment": 7}, {"compartment": True}, {"enabled": "yes"},
    {"auth_user_id": 0}, {"id": "bad:id"}
])
def test_service_rejects_invalid_schedule(client, change):
    update = json.loads(json.dumps(UPDATE))
    update["schedules"][0].update(change)
    assert client.put(PREFIX + "/config", json=update).status_code == 422


def test_database_survives_service_restart(tmp_path):
    path = tmp_path / "persistent.sqlite3"
    for iteration in range(2):
        with TestClient(create_app(path, TOKEN), headers={"Authorization": "Bearer " + TOKEN}) as c:
            response = c.post(PREFIX + "/events", json=event())
            assert response.json()["duplicate"] is bool(iteration)
            assert len(c.get(PREFIX + "/history").json()) == 1
