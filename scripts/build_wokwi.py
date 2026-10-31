"""Generate the free browser-Wokwi sketch. Only OUR files are combined.
Library source stays installed through Library Manager. Never reads settings.local.h.
Run: python scripts/build_wokwi.py
"""
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "firmware" / "PillDispenser"


def generate(destination, settings_text=None):
    """Combine application files; the default always uses public example settings."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    pieces = []
    for name in ("settings.example.h", "DispenserCore.h", "HttpSync.h", "MqttSync.h", "PillDispenser.ino"):
        text = settings_text if name == "settings.example.h" and settings_text is not None else (SOURCE / name).read_text(encoding="utf-8")
        text = "\n".join(line for line in text.splitlines()
                         if line.strip() not in ('#pragma once', '#include "settings.h"',
                                                 '#include "DispenserCore.h"', '#include "HttpSync.h"',
                                                 '#include "MqttSync.h"'))
        if name == "MqttSync.h":
            text = "#if defined(MDP_MQTT_ENABLED) && MDP_MQTT_ENABLED\n" + text + "\n#endif"
        pieces.append("// SOURCE: " + name + "\n" + text)
    # Arduino.h must precede any ESP32 task/queue types in the combined sketch.
    (destination / "sketch.ino").write_text("#include <Arduino.h>\n\n" + "\n\n".join(pieces) + "\n", encoding="utf-8")
    for name in ("diagram.json", "libraries.txt"):
        shutil.copyfile(SOURCE / name, destination / name)
    return destination


if __name__ == "__main__":
    generate(ROOT / "output" / "wokwi")
    print("Wokwi files: output/wokwi/sketch.ino, diagram.json, libraries.txt")
