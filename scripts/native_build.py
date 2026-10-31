"""Build shared C++ controller checks with g++, clang++, or Windows MSVC."""
import argparse
import hashlib
import io
import os
from pathlib import Path
import shutil
import subprocess
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".cache" / "native"
DEPENDENCIES = {
    "AgileStateMachine": ("cotestatnt/AgileStateMachine", "86caf5514103b9f393c041da0cbc2ce94c066de2"),
    "ArduinoJson": ("bblanchon/ArduinoJson", "v7.4.2"),
}


def dependencies():
    CACHE.mkdir(parents=True, exist_ok=True)
    for name, (repository, revision) in DEPENDENCIES.items():
        folder = CACHE / name
        marker = folder / ".source-ref"
        if marker.exists() and marker.read_text() == revision:
            continue
        if folder.exists():
            if not folder.resolve().is_relative_to(CACHE.resolve()):
                raise RuntimeError("Dependency cache path escaped the native build folder.")
            shutil.rmtree(folder)
        url = f"https://github.com/{repository}/archive/{revision}.zip"
        with urllib.request.urlopen(url, timeout=60) as response:
            archive = zipfile.ZipFile(io.BytesIO(response.read()))
        extracted = CACHE / archive.namelist()[0].split("/")[0]
        archive.extractall(CACHE)
        extracted.rename(folder)
        marker.write_text(revision)


def compiler_environment():
    compiler = os.environ.get("CXX") or shutil.which("g++") or shutil.which("clang++") or shutil.which("cl")
    if compiler and (os.name != "nt" or Path(compiler).stem.lower() not in ("cl", "clang-cl") or os.environ.get("INCLUDE")):
        return compiler, dict(os.environ)
    if os.name == "nt":
        # Use Visual Studio's setup in a child process, without changing the user's PATH.
        installer = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Microsoft Visual Studio/Installer/vswhere.exe"
        if installer.exists():
            location = subprocess.check_output([
                str(installer), "-latest", "-products", "*", "-requires",
                "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "installationPath",
            ], text=True).strip()
            setup = Path(location) / "VC/Auxiliary/Build/vcvars64.bat"
            if location and setup.exists():
                result = subprocess.check_output(
                    f'cmd.exe /d /s /c ""{setup}" >nul && set"', text=True, stderr=subprocess.PIPE)
                environment = {key.upper(): value for key, value in os.environ.items()}
                environment.update((key.upper(), value) for key, value in
                                   (line.split("=", 1) for line in result.splitlines()
                                    if "=" in line and not line.startswith("=")))
                compiler = shutil.which("cl.exe", path=environment["PATH"])
                if compiler:
                    return compiler, environment
    raise RuntimeError("Install a C++17 compiler: Visual Studio Build Tools (Desktop development with C++), or g++/clang++ on PATH.")


def build():
    dependencies()
    compiler, environment = compiler_environment()
    binary = CACHE / ("controller-tests.exe" if os.name == "nt" else "controller-tests")
    agile = CACHE / "AgileStateMachine/src"
    includes = [ROOT / "tests/native", ROOT / "firmware/PillDispenser", agile, CACHE / "ArduinoJson/src"]
    source = ROOT / "tests/native/test_controller.cpp"
    sources = [source, agile / "AgileStateMachine.cpp", agile / "State.cpp"]
    inputs = [source, Path(__file__), ROOT / "firmware/PillDispenser/DispenserCore.h", ROOT / "tests/native/Arduino.h"]
    fingerprint = hashlib.sha256((compiler + repr(DEPENDENCIES)).encode())
    for path in inputs:
        fingerprint.update(path.read_bytes())
    stamp = binary.with_suffix(".build-hash")
    digest = fingerprint.hexdigest()
    if binary.exists() and stamp.exists() and stamp.read_text() == digest:
        return binary
    if Path(compiler).stem.lower() in ("cl", "clang-cl"):
        command = [compiler, "/nologo", "/std:c++17", "/EHsc", "/W4", "/O1",
                   "/D_CRT_SECURE_NO_WARNINGS", "/DARDUINOJSON_ENABLE_STD_STRING=1",
                   *["/I" + str(folder) for folder in includes], *map(str, sources),
                   "/Fe:" + str(binary), "/Fo:" + str(CACHE) + os.sep]
    else:
        command = [compiler, "-std=c++17", "-O1", "-g", "-Wall", "-Wextra",
                   *["-I" + str(folder) for folder in includes], *map(str, sources), "-o", str(binary)]
    subprocess.run(command, cwd=CACHE, env=environment, check=True)
    stamp.write_text(digest)
    return binary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(build())
