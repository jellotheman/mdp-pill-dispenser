"""Download pinned development dependencies and test the actual C++ controller.
Run: python scripts/check_native.py [--events]
Requires Python 3 and g++/clang++ (or set CXX). No Arduino board is required.
"""
import os
import pathlib
import shutil
import subprocess
import sys
import urllib.request
import zipfile
import io

ROOT = pathlib.Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "native"
CACHE.mkdir(parents=True, exist_ok=True)
DEPS = {
    "AgileStateMachine": ("cotestatnt/AgileStateMachine", "86caf5514103b9f393c041da0cbc2ce94c066de2"),
    "ArduinoJson": ("bblanchon/ArduinoJson", "v7.4.2"),
}
for name, (repo, ref) in DEPS.items():
    folder = CACHE / name
    marker = folder / ".source-ref"
    if not marker.exists() or marker.read_text() != ref:
        if folder.exists():
            shutil.rmtree(folder)
        url = f"https://github.com/{repo}/archive/{ref}.zip"
        with urllib.request.urlopen(url, timeout=60) as response:
            archive = zipfile.ZipFile(io.BytesIO(response.read()))
        extracted = CACHE / archive.namelist()[0].split("/")[0]
        archive.extractall(CACHE)
        extracted.rename(folder)
        marker.write_text(ref)
compiler = os.environ.get("CXX") or shutil.which("g++") or shutil.which("clang++")
if not compiler:
    raise SystemExit("Install a C++17 compiler, or run Firmware checks in GitHub Actions.")
binary = CACHE / ("controller-tests.exe" if os.name == "nt" else "controller-tests")
agile = CACHE / "AgileStateMachine" / "src"
command = [
    compiler, "-std=c++17", "-O1", "-g", "-Wall", "-Wextra",
    "-I" + str(ROOT / "tests" / "native"),
    "-I" + str(ROOT / "firmware" / "PillDispenser"),
    "-I" + str(agile), "-I" + str(CACHE / "ArduinoJson" / "src"),
    str(ROOT / "tests" / "native" / "test_controller.cpp"),
    str(agile / "AgileStateMachine.cpp"), str(agile / "State.cpp"),
    "-o", str(binary),
]
subprocess.run(command, check=True)
arguments = [str(binary)] + (["--events"] if "--events" in sys.argv else [])
result = subprocess.run(arguments, check=True, text=True, capture_output=True)
print(result.stdout, end="")
output = ROOT / "output"
output.mkdir(exist_ok=True)
events = [line[6:] for line in result.stdout.splitlines() if line.startswith("EVENT ")]
if events:
    (output / "demo-events.jsonl").write_text("\n".join(events) + "\n", encoding="utf-8")
