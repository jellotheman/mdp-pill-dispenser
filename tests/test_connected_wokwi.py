"""A connected demo package is isolated from the offline firmware defaults."""
from datetime import datetime
import json
import pytest
from scripts import build_connected_wokwi as connected
from scripts.build_wokwi import SOURCE, generate

@pytest.fixture
def session(tmp_path, monkeypatch):
    monkeypatch.setattr(connected, "ROOT", tmp_path)
    path = tmp_path / "output/presentation/demo/session.json"
    path.parent.mkdir(parents=True)
    data = {"mqtt_namespace": "demo_123", "device_id": "mdp-demo", "token": "private-api-token"}
    path.write_text(json.dumps(data), encoding="utf-8")
    return path, data

def test_connected_package_is_simulated_and_excludes_api_token(session):
    path, data = session
    original_settings = (SOURCE / "settings.example.h").read_bytes()
    destination = connected.build_connected(path)
    sketch = (destination / "sketch.ino").read_text(encoding="utf-8")
    assert "#define MDP_MQTT_ENABLED 1" in sketch
    assert "constexpr bool ENABLE_NETWORK = true;" in sketch
    assert "constexpr bool DEMO_TIMERS = false;" in sketch
    assert "constexpr bool SIMULATION_PROFILE = true;" in sketch
    assert 'MQTT_NAMESPACE = "demo_123";' in sketch
    assert data["token"] not in sketch
    diagram = json.loads((destination / "diagram.json").read_text())
    rtc = next(part for part in diagram["parts"] if part["id"] == "rtc")
    assert rtc["attrs"]["initTime"] == datetime.now(connected.INDIA).date().isoformat() + "T07:59:30"
    assert diagram["connections"] == json.loads((SOURCE / "diagram.json").read_text())["connections"]
    assert (SOURCE / "settings.example.h").read_bytes() == original_settings
    offline = generate(path.parent / "offline")
    assert "constexpr bool ENABLE_NETWORK = false;" in (offline / "sketch.ino").read_text(encoding="utf-8")

@pytest.mark.parametrize("namespace", ["", "bad/topic", "a" * 33, "bad+name"])
def test_invalid_namespace_is_rejected(session, namespace):
    _, data = session
    data["mqtt_namespace"] = namespace
    with pytest.raises(ValueError, match="mqtt_namespace"):
        connected.connected_settings(data)

def test_session_must_be_under_output(tmp_path, monkeypatch):
    monkeypatch.setattr(connected, "ROOT", tmp_path)
    with pytest.raises(ValueError, match="ignored output"):
        connected.build_connected(tmp_path / "app/session.json")
