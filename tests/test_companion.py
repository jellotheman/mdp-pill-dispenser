"""Companion metadata and firmware configuration must be one atomic, persistent edit."""
import copy
import sqlite3

import pytest
from fastapi.testclient import TestClient
from integration.service import create_app

PREFIX = "/api/v1/devices/mdp-demo"
TOKEN = "companion-test-token"
UPDATE = {"expected_revision": 0, "timezone": "Asia/Kolkata", "schedules": [
    {"id": "morning", "medication": "Morning medication", "time": "08:00",
     "compartment": 1, "enabled": True, "auth_user_id": 1}
]}


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(tmp_path / "companion.sqlite3", TOKEN),
                    headers={"Authorization": "Bearer " + TOKEN}) as session:
        yield session


def test_labels_persist_but_do_not_leak_into_device_config(client):
    assert client.put(PREFIX + "/companion", json=UPDATE).status_code == 200
    config = client.get(PREFIX + "/config").json()
    assert config["schedules"][0] == {k: v for k, v in UPDATE["schedules"][0].items() if k != "medication"}
    companion = client.get(PREFIX + "/companion").json()
    assert companion["schedules"] == UPDATE["schedules"]
    assert companion["revision"] == companion["status"]["desired_revision"] == 1
    assert not companion["status"]["synchronized"]
    client.post(PREFIX + "/config-acks", json={"revision": 1, "status": "applied"})
    assert client.get(PREFIX + "/companion").json()["status"]["synchronized"]


def test_stale_edit_changes_neither_labels_nor_config(client):
    client.put(PREFIX + "/companion", json=UPDATE)
    stale = copy.deepcopy(UPDATE)
    stale["schedules"][0].update(medication="Stale label", enabled=False)
    assert client.put(PREFIX + "/companion", json=stale).status_code == 409
    assert client.get(PREFIX + "/companion").json()["schedules"] == UPDATE["schedules"]


def test_label_storage_failure_rolls_back_the_new_device_revision(client, tmp_path):
    client.put(PREFIX + "/companion", json=UPDATE)
    # Fail after config has been written, at the metadata boundary in the same transaction.
    with sqlite3.connect(tmp_path / "companion.sqlite3") as db:
        db.execute("""CREATE TRIGGER reject_label BEFORE INSERT ON medication_labels
                      WHEN NEW.medication = 'fail-label'
                      BEGIN SELECT RAISE(ABORT, 'injected label storage failure'); END""")
    update = copy.deepcopy(UPDATE)
    update["expected_revision"] = 1
    update["schedules"][0].update(medication="fail-label", time="09:00")
    with pytest.raises(sqlite3.IntegrityError, match="injected label storage failure"):
        client.put(PREFIX + "/companion", json=update)
    snapshot = client.get(PREFIX + "/companion").json()
    assert snapshot["revision"] == 1
    assert snapshot["schedules"] == UPDATE["schedules"]


def test_pause_survives_restart_and_keeps_identity(tmp_path):
    database = tmp_path / "persistent.sqlite3"
    for step in range(2):
        with TestClient(create_app(database, TOKEN), headers={"Authorization": "Bearer " + TOKEN}) as session:
            if step == 0:
                session.put(PREFIX + "/companion", json=UPDATE)
                paused = copy.deepcopy(UPDATE)
                paused["expected_revision"] = 1
                paused["schedules"][0]["enabled"] = False
                assert session.put(PREFIX + "/companion", json=paused).status_code == 200
            schedule = session.get(PREFIX + "/companion").json()["schedules"][0]
            assert schedule["id"] == "morning"
            assert schedule["medication"] == "Morning medication"
            assert not schedule["enabled"]


@pytest.mark.parametrize("change", [
    {"medication": "   "}, {"medication": 42}, {"compartment": 7},
    {"time": "24:00"}, {"auth_user_id": 0}, {"enabled": "false"},
])
def test_invalid_app_metadata_never_creates_a_revision(client, change):
    update = copy.deepcopy(UPDATE)
    update["schedules"][0].update(change)
    assert client.put(PREFIX + "/companion", json=update).status_code == 422
    assert client.get(PREFIX + "/config").json()["revision"] == 0


def test_duplicate_ids_and_unauthorized_edits_rejected(client):
    update = copy.deepcopy(UPDATE)
    update["schedules"] *= 2
    assert client.put(PREFIX + "/companion", json=update).status_code == 422
    assert client.put(PREFIX + "/companion", json=UPDATE, headers={"Authorization": ""}).status_code == 401


def test_device_only_edit_preserves_existing_label_and_maps_unknown_ids(client):
    client.put(PREFIX + "/companion", json=UPDATE)
    config = client.get(PREFIX + "/config").json()
    config["schedules"][0]["enabled"] = False
    config["schedules"].append({"id": "evening", "time": "20:00", "compartment": 2,
                                "enabled": True, "auth_user_id": 1})
    client.put(PREFIX + "/config", json={"expected_revision": 1, "timezone": "Asia/Kolkata", "schedules": config["schedules"]})
    schedules = client.get(PREFIX + "/companion").json()["schedules"]
    assert schedules[0]["medication"] == "Morning medication" and not schedules[0]["enabled"]
    assert schedules[1]["medication"] == "evening"
