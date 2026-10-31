"""Exercise the transport against the real API and SQLite without a public broker."""
import json
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from integration.mqtt_bridge import Bridge
from integration.service import create_app


class FakeBroker:
    def __init__(self):
        self.publications = []

    def is_connected(self):
        return True

    def publish(self, topic, payload, qos, retain):
        self.publications.append((topic, json.loads(payload), qos, retain))
        return SimpleNamespace(rc=0)


class TestApi:
    __test__ = False

    def __init__(self, client):
        self.client = client

    def request(self, path, data=None):
        route = "/api/v1/devices/mdp-demo" + path
        response = self.client.get(route) if data is None else self.client.post(route, json=data)
        if response.status_code != 200:
            raise ValueError(str(response.status_code))
        return response.json()


@pytest.fixture
def setup(tmp_path):
    with TestClient(create_app(tmp_path / "bridge.sqlite3", "token"),
                    headers={"Authorization": "Bearer token"}) as session:
        broker = FakeBroker()
        yield session, broker, Bridge(TestApi(session), broker, "private-test", "mdp-demo")


def test_config_is_retained_and_republished_on_reconnect(setup):
    session, broker, bridge = setup
    update = {"expected_revision": 0, "timezone": "Asia/Kolkata", "schedules": [
        {"id": "a", "time": "08:00", "compartment": 1, "enabled": True,
         "auth_user_id": 1, "medication": "Private label"}]}
    assert session.put("/api/v1/devices/mdp-demo/companion", json=update).status_code == 200
    bridge.sync_config()
    topic, config, qos, retain = broker.publications[0]
    assert topic == "mdp-demo/private-test/mdp-demo/config" and qos == 1 and retain
    assert config["revision"] == 1 and "medication" not in config["schedules"][0]
    bridge.sync_config()
    assert len(broker.publications) == 1
    bridge.needs_config.set()
    bridge.sync_config()
    assert len(broker.publications) == 2


def test_event_acknowledged_only_after_valid_commit_and_duplicate_is_idempotent(setup):
    session, broker, bridge = setup
    event = {"schema_version": 2, "event_id": "mdp-demo:session:1", "device_id": "mdp-demo",
             "session_id": "session", "event": "dispensed", "state": "COMPLETED",
             "elapsed_ms": 123, "occurred_at": None, "dose_id": "today:a", "schedule_id": "a",
             "compartment": 1, "revision": 1, "reason": "one_passage_observed",
             "observed_count": 1, "simulated": True}
    def deliver(data, retain=False):
        bridge.on_message(broker, None, SimpleNamespace(topic=bridge.prefix + "/events",
                           payload=json.dumps(data).encode(), retain=retain))
    deliver(dict(event, simulated=False))
    deliver(event, retain=True)
    assert broker.publications == []
    deliver(event)
    assert broker.publications[-1][1] == {"accepted": True, "duplicate": False, "event_id": event["event_id"]}
    deliver(event)
    assert broker.publications[-1][1]["duplicate"] is True
    assert len(session.get("/api/v1/devices/mdp-demo/history").json()) == 1
    deliver(dict(event, reason="different"))
    assert len(broker.publications) == 2


def test_config_ack_updates_status(setup):
    session, broker, bridge = setup
    session.put("/api/v1/devices/mdp-demo/config", json={"expected_revision": 0,
        "timezone": "Asia/Kolkata", "schedules": []})
    bridge.on_message(broker, None, SimpleNamespace(topic=bridge.prefix + "/config-ack",
        payload=b'{"revision":1,"status":"applied","reason":"applied"}', retain=False))
    assert session.get("/api/v1/devices/mdp-demo/status").json()["synchronized"] is True
