"""Real HTTP replay of events produced by the compiled C++ controller.
Run python scripts/check_native.py --events first, then python scripts/http_demo.py.
Starts a temporary reference backend; does not connect to a physical ESP32.
"""
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
events = [json.loads(line) for line in (ROOT / "output/demo-events.jsonl").read_text().splitlines()]
with tempfile.TemporaryDirectory(prefix="mdp-http-") as folder:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
    environment = dict(os.environ, MDP_DEVICE_TOKEN="temporary-demo-token",
                       MDP_DB=str(Path(folder) / "demo.sqlite3"))
    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "integration.service:create_app", "--factory",
         "--host", "127.0.0.1", "--port", str(port), "--log-level", "error"],
        cwd=ROOT, env=environment)
    base = f"http://127.0.0.1:{port}"

    def request(method, path, value=None):
        data = None if value is None else json.dumps(value).encode()
        req = urllib.request.Request(base + path, data=data, method=method,
                                     headers={"Authorization": "Bearer temporary-demo-token",
                                              "Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=5) as response:
            return json.load(response)

    try:
        for _ in range(100):
            try:
                request("GET", "/health")
                break
            except (OSError, urllib.error.URLError):
                if process.poll() is not None:
                    raise RuntimeError("reference backend failed to start")
                time.sleep(0.1)
        else:
            raise RuntimeError("reference backend startup timed out")
        prefix = "/api/v1/devices/test-device"
        update = {"expected_revision": 0, "timezone": "Asia/Kolkata", "schedules": [
            {"id": "morning", "time": "08:00", "compartment": 1,
             "enabled": True, "auth_user_id": 7}]}
        config = request("PUT", prefix + "/config", update)
        assert request("GET", prefix + "/config") == config
        assert not request("GET", prefix + "/status")["synchronized"]
        # This is an explicit simulated-device acknowledgement, not Wi-Fi firmware execution.
        request("POST", prefix + "/config-acks", {"revision": config["revision"], "status": "applied"})
        assert request("GET", prefix + "/status")["synchronized"]
        for event in events:
            ack = request("POST", prefix + "/events", event)
            assert ack["accepted"] and ack["event_id"] == event["event_id"]
            assert request("POST", prefix + "/events", event)["duplicate"]
        history = request("GET", prefix + "/history")
        assert len(history) == 1 and history[0]["event"] == "dispensed"
        print("PASS: real HTTP schedule save/fetch, simulated applied acknowledgement, C++ event replay and deduplicated history.")
    finally:
        process.terminate()
        process.wait(timeout=10)
