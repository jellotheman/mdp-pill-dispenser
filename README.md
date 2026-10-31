# MDP Smart Pill Dispenser

PillPilot is the companion dashboard for a student ESP32 pill-dispenser project. The firmware is
Arduino/C++; Python runs a small reference integration service and developer tools, not the device.

## Presentation on Windows

From the project root, run `present.cmd`. The first run installs dependencies and builds the app.
The launcher opens separate local terminal windows and the dashboard at http://127.0.0.1:3000:

- **APP** serves the dashboard.
- **API** stores schedules, history and simulated notifications in a local SQLite database.
- **BRIDGE** exchanges simulated device configuration and events with an MQTT broker.

The ESP32 firmware runs separately in [the existing Wokwi project](https://wokwi.com/projects/479372515382840321).
The launcher prints a session-specific `wokwi/` folder with `sketch.ino`, `diagram.json` and
`libraries.txt`; use all three from the same session in Wokwi. See the
[presentation guide](docs/PRESENTATION.md) for setup, buttons, restarting and troubleshooting.
Python 3.10+, Node.js/npm and internet access are needed. `present.cmd --no-setup` reuses an
existing build; `--local-only` starts just APP and API. Run the full command after source changes.

The default MQTT demonstration uses a shared public broker and synthetic data only. Other clients
can read or forge its messages; a random topic is not access control. Do not use real medication,
patient or fingerprint information. A private authenticated broker and additional product work are
required for a real deployment.

Stop the project's previous terminals before starting or restarting. After tests, close their
terminals and keep only the final APP, API and BRIDGE presentation windows open. Stop each with
Ctrl+C. Session files and SQLite databases are kept under ignored `output/presentation/`.

## How it works

The app saves a desired schedule to the service. In the connected demo, the MQTT bridge sends that
configuration to Wokwi; the firmware validates and persists it and reports its applied revision.
The firmware uses its RTC to decide when a dose is due and retains its local schedule when offline.
It reports durable events through the bridge to the service, and the app reads the resulting history.
The service does not issue timed motor commands. The firmware requires local authorization and
never permits a remote command to impersonate a fingerprint or directly dispense.

The standalone simulation uses fixed 5/35/65-second demonstration offers, without a network.
The connected presentation instead uses the simulated RTC and schedules saved through the app.
The initial connected demonstration has doses at 08:00 and 08:02, with a third at 08:05 paused.
The device acknowledgement distinguishes a saved schedule from one the controller actually applied.

The same sketch and headers can be compiled and flashed to an ESP32, but this project does **not**
yet contain working physical motor, fingerprint, pill-passage or lock drivers. Its physical profile
deliberately refuses operation. The simulation models six compartments, one preloaded item per slot;
its servo, buttons and timing do not validate a physical mechanism. SMS records are simulated.

## Project folders and further reading

| Folder | Purpose |
| --- | --- |
| `firmware/` | ESP32 controller, simulation and future physical mechanism interface |
| `app/` | Next.js companion dashboard and server-side service adapter |
| `integration/` | Reference API, MQTT bridge and shared contract |
| `mechanical/`, `electronics/` | Physical design, components and wiring |
| `docs/`, `tests/` | Team notes, handoff and verification |

[Presentation](docs/PRESENTATION.md) · [Firmware](firmware/README.md) ·
[Integration](integration/README.md) · [Contract](integration/INTERFACE.md) ·
[Architecture](docs/ARCHITECTURE.md) · [Validation](docs/VALIDATION.md) ·
[Later-session handoff](docs/CODEX_HANDOFF.md)

## Development checks

After installing dependencies, from the project root:

```powershell
.\.venv\Scripts\python.exe scripts/check_native.py --events
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe scripts/http_demo.py
npm.cmd --prefix app test
npm.cmd --prefix app run lint
npm.cmd --prefix app run build
```

Native controller checks need a C++17 compiler; running the app and service does not.
See [VALIDATION.md](docs/VALIDATION.md) for observed results and limits. The earlier MicroPython
prototype remains on `legacy/micropython`; it is no longer the entry point.
