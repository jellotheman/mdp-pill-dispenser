# MDP Smart Pill Dispenser

Shared workspace for the five-person, first-year multidisciplinary project.

**Firmware now uses Arduino/C++**, following the decision to simplify Wokwi and hardware-library setup.
Start with [firmware instructions](firmware/README.md).
For continuation in the local Codex app, read [CODEX_HANDOFF.md](docs/CODEX_HANDOFF.md).

| Folder | Owner / work |
| --- | --- |
| firmware/ | Sreeram: ESP32 sketch, workflow, simulated/physical mechanism interface |
| mechanical/ | Compartments, mechanism, enclosure, editable CAD and assembly |
| electronics/ | Actual components, reviewed wiring, power and pin assignments |
| app/ | Existing companion app; source still to be supplied |
| integration/ | Reference API, schedule synchronization, history and notification delivery |
| docs/ | Team instructions, architecture, physical decisions and handoff |
| tests/ | Actual C++ workflow tests and Python reference-service tests |

[Detailed beginner collaboration guide](docs/TEAM_GUIDE.md) ·
[Architecture](docs/ARCHITECTURE.md) ·
[App/device contract](integration/INTERFACE.md) ·
[Hardware questions](docs/MECHANISM_BRIEF.md) ·
[Validation evidence and limits](docs/VALIDATION.md)

## What is implemented

- A community FSM library (AgileStateMachine) with state entry callbacks and an explicit workflow.
- Due-dose scheduling, matching-user authorization and rejection/missed-dose handling.
- Mechanism operations that receive the actual target compartment and dose.
- Homing, positioning, release and verification states with timeouts.
- Persistent occurrence records and compartment inventory, written before actuation.
- A persistent event outbox, unique event IDs, acknowledgement and retry.
- Versioned configuration: validated/persisted locally, applied acknowledgement, busy deferral.
- An HTTP client in a separate ESP32 task; sensor/motor logic stays in the main task.
- A FastAPI/SQLite reference service with history and deduplicated mock SMS records.
- A generated single-file Wokwi sketch using Library Manager dependencies.

## The simulation assumption

Only the simulation currently supplies a mechanism implementation: six virtual compartments,
each holding **one preloaded item**. Homing and indexing are simulated by timed feedback.
The pictured servo visualizes a release; it is not a real indexed carousel.
Buttons simulate user matching and passage detection.

A completed occurrence consumes its compartment. Tomorrow's schedule does not refill it.
The physical mechanism and refill/maintenance procedure are still undecided.
Setting SIMULATION_PROFILE=false deliberately blocks movement.

No fingerprint sensor, real pill sensing, physical lock, or real SMS provider is implemented.
A detected passage does not establish pill identity, a complete medically correct dose, or ingestion.

## Run checks

Install Python 3 and a C++17 compiler, then from the repository root:

~~~sh
python -m pip install -r requirements-dev.txt
python scripts/check_native.py --events
python -m pytest -q
python scripts/http_demo.py
python scripts/build_wokwi.py
~~~

The first native check downloads pinned development dependencies to .cache/.
It executes the same controller header included by the ESP32 sketch, with the actual FSM library.
The HTTP demo replays its events over real loopback HTTP; it does not execute ESP32 networking.

For an actual ESP32 compile, use Arduino CLI/IDE as described in firmware/README.md.
GitHub Actions performs both native/service checks and ESP32 compilation.
See the latest successful run for evidence, rather than inferring success from test files.

## Work in the browser or locally

- [Create a Codespace](https://codespaces.new/jellotheman/mdp-pill-dispenser?quickstart=1), or open your local clone in Codex.
- Open Wokwi separately using the free Arduino ESP32 template and generated files.
- Saving in Wokwi does not update this repository.
- Teammates can submit files through GitHub's Add file → Upload files.
- Preserve existing local changes before pulling updates; see the handoff.

The earlier MicroPython prototype remains available in Git history.
It is no longer the firmware entry point, and its old 40-test result does not validate this implementation.
