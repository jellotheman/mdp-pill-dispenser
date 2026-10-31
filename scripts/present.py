"""Prepare and launch the local PillPilot presentation in separate console windows.

Windows: present.cmd (or python scripts/present.py)
Linux: python scripts/present.py --prepare-only, then use the printed worker commands.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import secrets
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).resolve()
VENV_PYTHON = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
ROLES = ("api", "app", "bridge")
WOKWI_PROJECT = "https://wokwi.com/projects/479372515382840321"


def run(command, *, cwd=ROOT):
    print("Running:", subprocess.list2cmdline([str(value) for value in command]), flush=True)
    subprocess.run([str(value) for value in command], cwd=cwd, check=True)


def prepare():
    if not VENV_PYTHON.exists():
        run([sys.executable, "-m", "venv", ROOT / ".venv"])
    run([VENV_PYTHON, "-m", "pip", "install", "-r", "requirements-dev.txt"])
    npm = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if not npm or not shutil.which("node"):
        raise RuntimeError("Install Node.js 20.9+ with npm, then rerun the launcher.")
    run([npm, "ci"], cwd=ROOT / "app")
    run([npm, "run", "build"], cwd=ROOT / "app")
    run([VENV_PYTHON, ROOT / "scripts/build_wokwi.py"])


def check_prepared():
    if not VENV_PYTHON.exists() or not (ROOT / "app/.next/BUILD_ID").exists():
        raise RuntimeError("Presentation dependencies or production build are missing. Rerun without --no-setup.")


def check_port(port):
    with socket.socket() as sock:
        try:
            sock.bind(("127.0.0.1", port))
        except OSError as error:
            raise RuntimeError(
                f"Port {port} is already occupied. Close the earlier presentation terminal or use "
                "--api-port and --app-port to choose other ports. No existing process was stopped."
            ) from error


def request(session, method, path, value=None):
    body = None if value is None else json.dumps(value).encode("utf-8")
    req = urllib.request.Request(
        session["backend_url"] + path, method=method, data=body,
        headers={"Authorization": "Bearer " + session["token"], "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=3) as response:
        return json.load(response)


def seed_schedules(session):
    prefix = f"/api/v1/devices/{session['device_id']}"
    current = request(session, "GET", prefix + "/config")
    if current["revision"]:
        return  # A resumed session retains its edits and recorded device history.
    rows = [
        {"id": "morning", "medication": "Morning medication", "time": "08:00", "compartment": 1,
         "enabled": True, "auth_user_id": 1},
        {"id": "afternoon", "medication": "Afternoon medication", "time": "08:02", "compartment": 2,
         "enabled": True, "auth_user_id": 1},
        {"id": "evening", "medication": "Evening medication", "time": "08:05", "compartment": 3,
         "enabled": False, "auth_user_id": 1},
    ]
    request(session, "PUT", prefix + "/companion", {
        "expected_revision": 0, "timezone": "Asia/Kolkata", "schedules": rows,
    })


def wait_ready(url, process, label, *, timeout=60, show_progress=False):
    deadline = time.monotonic() + timeout
    next_report = time.monotonic() + 10
    reason = "waiting for a response"
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"{label} exited during startup. Read its console window for the error.")
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except urllib.error.HTTPError as error:
            reason = f"HTTP {error.code}; waiting for the service to become ready"
        except urllib.error.URLError as error:
            reason = "waiting for DNS resolution" if isinstance(error.reason, socket.gaierror) else "waiting for service connectivity"
        except OSError:
            reason = "waiting for service connectivity"
        if show_progress and time.monotonic() >= next_report:
            remaining = max(0, round(deadline - time.monotonic()))
            print(f"{label}: {reason} ({remaining}s remaining).", flush=True)
            next_report = time.monotonic() + 10
        time.sleep(0.25)
    raise RuntimeError(f"{label} did not become ready within {round(timeout)} seconds: {reason}. Read its console window.")


def session_environment(session):
    return dict(
        os.environ,
        MDP_DEVICE_TOKEN=session["token"],
        MDP_DEVICE_ID=session["device_id"],
        MDP_DB=session["database"],
        MDP_BACKEND_URL=session["backend_url"],
        NEXT_TELEMETRY_DISABLED="1",
        PYTHONUNBUFFERED="1",
    )


def worker(role, session_file):
    session = json.loads(session_file.read_text(encoding="utf-8"))
    environment = session_environment(session)
    if os.name == "nt":
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleW(f"PillPilot | {role.upper()} | {session_file.parent.name}")
    print(f"PillPilot presentation: {role.upper()}\nSession: {session_file.parent}", flush=True)
    if role == "api":
        command = [str(VENV_PYTHON), "-m", "uvicorn", "integration.service:create_app", "--factory",
                   "--host", "127.0.0.1", "--port", str(session["api_port"])]
        cwd = ROOT
        print("Shared SQLite reference service. SMS records are simulated. Ctrl+C stops this service.", flush=True)
    elif role == "bridge":
        command = [str(VENV_PYTHON), "-m", "integration.mqtt_bridge", "--api", session["backend_url"],
                   "--device", session["device_id"], "--namespace", session["mqtt_namespace"],
                   "--broker", "broker.hivemq.com", "--port", "1883"]
        cwd = ROOT
        print("Public MQTT broker: synthetic demonstration data only. Ctrl+C stops the bridge.", flush=True)
    else:
        seed_schedules(session)
        node = shutil.which("node")
        if not node:
            raise RuntimeError("Node.js is unavailable on PATH.")
        command = [node, str(ROOT / "app/node_modules/next/dist/bin/next"), "start",
                   "--hostname", "127.0.0.1", "--port", str(session["app_port"])]
        cwd = ROOT / "app"
        print(f"Dashboard: {session['app_url']}\nCtrl+C stops the dashboard server.", flush=True)
    try:
        return subprocess.call(command, cwd=cwd, env=environment)
    except KeyboardInterrupt:
        print("\nPresentation component stopped.", flush=True)
        return 130


def open_worker(role, session_file):
    command = [str(VENV_PYTHON), str(SCRIPT), "--worker", role, "--session", str(session_file)]
    if os.name == "nt":
        return subprocess.Popen(command, cwd=ROOT, creationflags=subprocess.CREATE_NEW_CONSOLE)
    # Keep Linux support explicit and predictable; xterm provides the same separate-console behavior.
    terminal = shutil.which("xterm")
    if not terminal:
        raise RuntimeError(
            "Separate windows on Linux require xterm. Use --prepare-only, then run "
            "the printed --worker commands in your own terminals."
        )
    return subprocess.Popen([terminal, "-T", f"PillPilot {role}", "-e", *command], cwd=ROOT)


def stop_started(processes):
    # Only live handles created by THIS invocation are eligible; never trust saved numeric PIDs.
    for process in reversed(processes):
        if process.poll() is not None:
            continue
        if os.name == "nt":
            subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"], capture_output=True)
        else:
            process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


def create_session(args):
    if args.session:
        session_file = args.session.resolve()
        if not session_file.is_file():
            raise RuntimeError(f"Session file does not exist: {session_file}")
        return session_file, json.loads(session_file.read_text(encoding="utf-8"))
    folder = ROOT / "output/presentation" / (datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ") + "-" + uuid.uuid4().hex[:8])
    folder.mkdir(parents=True)
    session = {
        "device_id": "mdp-demo", "token": secrets.token_urlsafe(32),
        "api_port": args.api_port, "app_port": args.app_port,
        "backend_url": f"http://127.0.0.1:{args.api_port}",
        "app_url": f"http://127.0.0.1:{args.app_port}",
        "database": str(folder / "service.sqlite3"),
        "mqtt_namespace": uuid.uuid4().hex,
    }
    session_file = folder / "session.json"
    session_file.write_text(json.dumps(session, indent=2) + "\n", encoding="utf-8")
    return session_file, session


def print_workers(session_file, *, local_only=False):
    for role in (ROLES[:2] if local_only else ROLES):
        print(subprocess.list2cmdline([str(VENV_PYTHON), str(SCRIPT), "--worker", role,
                                       "--session", str(session_file)]))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--prepare-only", action="store_true", help="Install/build and print manual worker commands without opening windows.")
    parser.add_argument("--no-setup", action="store_true", help="Reuse installed dependencies and the latest production build.")
    parser.add_argument("--no-browser", action="store_true", help="Open terminal windows without opening a browser.")
    connection = parser.add_mutually_exclusive_group()
    connection.add_argument("--local-only", action="store_true", help="Start app/API without the MQTT bridge.")
    parser.set_defaults(local_only=False)
    parser.add_argument("--api-port", type=int, default=8000)
    parser.add_argument("--app-port", type=int, default=3000)
    parser.add_argument("--session", type=Path, help="Resume an existing ignored output/presentation/.../session.json.")
    parser.add_argument("--worker", choices=ROLES, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.worker:
        if not args.session:
            parser.error("--worker requires --session")
        return worker(args.worker, args.session.resolve())
    if not (1 <= args.api_port <= 65535 and 1 <= args.app_port <= 65535) or args.api_port == args.app_port:
        parser.error("Choose two different ports between 1 and 65535.")
    if not args.no_setup:
        prepare()
    check_prepared()
    session_file, session = create_session(args)
    print(f"\nSession files: {session_file.parent}")
    if args.prepare_only:
        print("Open these commands in separate terminals (API first, then app" + ("" if args.local_only else ", then bridge") + "):")
        print_workers(session_file, local_only=args.local_only)
        print("For automatic startup and a connected Wokwi package, rerun with --no-setup.")
        return 0
    check_port(session["api_port"])
    check_port(session["app_port"])
    processes = []
    try:
        api = open_worker("api", session_file)
        processes.append(api)
        wait_ready(session["backend_url"] + "/health", api, "Integration service")
        seed_schedules(session)
        app = open_worker("app", session_file)
        processes.append(app)
        wait_ready(session["app_url"] + "/api/dashboard", app, "Dashboard")
        if not args.local_only:
            bridge = open_worker("bridge", session_file)
            processes.append(bridge)
            run([VENV_PYTHON, ROOT / "scripts/build_connected_wokwi.py", "--session", session_file])
        if not args.no_browser:
            webbrowser.open(session["app_url"])
        print(f"\nReady: {session['app_url']}\nAPI documentation: {session['backend_url']}/docs")
        if not args.local_only:
            print(f"Wokwi demo files: {session_file.parent / 'wokwi'}")
            print("Use that session's sketch.ino, diagram.json and libraries.txt in Wokwi; public MQTT is for synthetic data only.")
            print(f"Existing Wokwi project: {WOKWI_PROJECT}")
        running = "APP and API" if args.local_only else "APP, API and BRIDGE"
        print(f"The external terminals own the running components. Stop {running} with Ctrl+C.")
        print("Device configuration remains pending until the ESP32/Wokwi client connects and acknowledges it.")
        print("Presentation guide: docs/PRESENTATION.md")
        print(f"Resume this session after stopping its terminals: python scripts/present.py --no-setup --session \"{session_file}\"")
        return 0
    except BaseException:
        stop_started(processes)
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, RuntimeError, subprocess.CalledProcessError, urllib.error.URLError) as error:
        print(f"\nPresentation could not start: {error}", file=sys.stderr)
        raise SystemExit(1)
