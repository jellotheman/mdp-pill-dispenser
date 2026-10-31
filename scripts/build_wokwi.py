"""Generate the free browser-Wokwi sketch. Only OUR files are combined.
Library source stays installed through Library Manager. Never reads settings.local.h.
Run: python scripts/build_wokwi.py
"""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parents[1]
source = root / "firmware" / "PillDispenser"
out = root / "output" / "wokwi"
out.mkdir(parents=True, exist_ok=True)
pieces = []
for name in ("settings.h", "DispenserCore.h", "HttpSync.h", "PillDispenser.ino"):
    text = (source / name).read_text(encoding="utf-8")
    text = "\n".join(line for line in text.splitlines()
                     if line.strip() not in ('#pragma once', '#include "settings.h"',
                                             '#include "DispenserCore.h"', '#include "HttpSync.h"'))
    pieces.append("// SOURCE: " + name + "\n" + text)
# Arduino.h must precede any ESP32 task/queue types in the combined sketch.
(out / "sketch.ino").write_text("#include <Arduino.h>\n\n" + "\n\n".join(pieces) + "\n", encoding="utf-8")
for name in ("diagram.json", "libraries.txt"):
    shutil.copyfile(source / name, out / name)
print("Wokwi files: output/wokwi/sketch.ino, diagram.json, libraries.txt")
