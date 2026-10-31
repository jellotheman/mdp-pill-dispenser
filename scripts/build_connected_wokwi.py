"""Build the synthetic public-MQTT Wokwi package for a presentation session."""
import argparse
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re

try:
    from .build_wokwi import ROOT, SOURCE, generate
except ImportError:
    from build_wokwi import ROOT, SOURCE, generate

INDIA = timezone(timedelta(hours=5, minutes=30))


def connected_settings(session):
    namespace = session.get("mqtt_namespace", "")
    device = session.get("device_id", "")
    for name, value in (("mqtt_namespace", namespace), ("device_id", device)):
        if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,32}", value):
            raise ValueError(f"Invalid {name}: use 1–32 letters, digits, underscores or hyphens.")
    settings = (SOURCE / "settings.example.h").read_text(encoding="utf-8")
    settings, count = re.subn(r"^#define MDP_MQTT_ENABLED\s+\d+.*$", "#define MDP_MQTT_ENABLED 1", settings, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError("Expected exactly one MDP_MQTT_ENABLED declaration.")
    values = {"SIMULATION_PROFILE": "true", "DEMO_TIMERS": "false", "ENABLE_NETWORK": "true",
              "DEVICE_ID": json.dumps(device), "MQTT_HOST": '"broker.hivemq.com"',
              "MQTT_PORT": "1883", "MQTT_NAMESPACE": json.dumps(namespace)}
    for name, value in values.items():
        pattern = rf"^(constexpr\s+(?:bool|unsigned|const char\*)\s+{name}\s*=\s*).+?;.*$"
        settings, count = re.subn(pattern, lambda match: match[1] + value + ";", settings, flags=re.MULTILINE)
        if count != 1:
            raise RuntimeError(f"Expected exactly one {name} declaration in example settings.")
    return settings


def build_connected(session_path):
    session_path = Path(session_path).resolve()
    if not session_path.is_relative_to((ROOT / "output").resolve()):
        raise ValueError("Keep presentation session files under the ignored output directory.")
    session = json.loads(session_path.read_text(encoding="utf-8"))
    destination = generate(session_path.parent / "wokwi", settings_text=connected_settings(session))
    diagram_path = destination / "diagram.json"
    diagram = json.loads(diagram_path.read_text(encoding="utf-8"))
    rtc = next(part for part in diagram["parts"] if part["id"] == "rtc")
    rtc["attrs"]["initTime"] = datetime.now(INDIA).date().isoformat() + "T07:59:30"
    diagram_path.write_text(json.dumps(diagram, indent=2) + "\n", encoding="utf-8")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", type=Path, required=True)
    args = parser.parse_args()
    destination = build_connected(args.session)
    print(f"Wokwi MQTT demo package: {destination}")
    print("Public broker: use synthetic data only; anyone can observe or alter this traffic.")
