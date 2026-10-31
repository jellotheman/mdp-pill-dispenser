# Codex handoff: MDP smart pill dispenser

Read this file when continuing in the local Codex app. It is self-contained.
Repository: https://github.com/jellotheman/mdp-pill-dispenser (private).
Owner: jellotheman. Firmware lead: Sreeram Biju.

## Current request and direction

The user wants understandable, maintainable firmware that uses community libraries,
can be demonstrated in free Wokwi, and can progress toward the physical product.
They can read Arduino code and explicitly prefer the simpler Arduino/library-manager route.
Do not switch back to Python firmware merely because earlier messages preferred Python.

The default/current branch is main. It contains Arduino/C++ firmware.
The original MicroPython prototype, including pysm and its original tests, is preserved on legacy/micropython.
A temporary implementation branch, firmware/product-interfaces, may also exist.
The user requested the Arduino work back on the default branch.

The user has an existing app that has not yet been uploaded. They will supply it later.
Do not invent its framework, call its source reviewed, or build a replacement UI before inspection.

The five roles remain:
1. Sreeram: ESP32 firmware and simulation.
2. Mechanical: compartments, mechanism, enclosure and CAD.
3. Electronics: components, wiring, power and actual sensor/motor interfaces.
4. Companion app: existing app and its UI/data layer.
5. Communication/integration: shared API, schedule/device synchronization, history and SMS.

## Start safely in the local clone

1. Read git status and inspect local changes before any checkout/pull.
2. Preserve uncommitted work or divergent commits on a personal branch; never reset --hard to simplify an update.
3. When the working tree is safe, fetch origin, switch to main, and pull --ff-only.
4. Read README.md, firmware/README.md, docs/ARCHITECTURE.md,
   integration/INTERFACE.md, docs/MECHANISM_BRIEF.md and docs/VALIDATION.md.
5. Check that the local files actually match the descriptions here.
6. Work in a branch for changes that affect shared interfaces.
7. The user has authorized implementation and testing; routine reversible implementation choices do not need repeated permission.

~~~sh
git status
git fetch origin
git switch main
git pull --ff-only origin main
~~~

If the last command reports divergence, inspect and reconcile it rather than force-pushing or dropping work.
The Python branch should remain available.

## Source map

- firmware/PillDispenser/PillDispenser.ino: board setup/loop, NVS adapter, buttons, RTC and indicators.
- firmware/PillDispenser/DispenserCore.h: board-independent contract, storage, occurrence logic,
  declarative FSM and mechanism interface.
- firmware/PillDispenser/HttpSync.h: ESP32 HTTP worker and main-task synchronization.
- firmware/PillDispenser/settings.example.h: demonstration constants.
- firmware/PillDispenser/settings.h: loader for settings.local.h or defaults.
- firmware/PillDispenser/settings.local.h: optional local override, deliberately ignored by Git.
- firmware/PillDispenser/libraries.txt: pinned standard Library Manager entries.
- firmware/PillDispenser/diagram.json: demonstration circuit.
- integration/service.py: FastAPI/SQLite reference backend.
- tests/native/test_controller.cpp: scenarios executing the actual C++ controller.
- tests/native/Arduino.h: only the clock/type shim needed by the actual FSM library.
- tests/test_integration.py: service behavior.
- scripts/check_native.py: pinned dependency fetch, native build and scenario run.
- scripts/http_demo.py: real loopback HTTP replay of actual C++ events.
- scripts/build_wokwi.py: combines our source into output/wokwi/sketch.ino.
- docs/TEAM_GUIDE.md: verbose browser-upload/collaboration instructions for beginners.

## Dependencies and builds

Firmware dependencies are unmodified Library Manager packages:
AgileStateMachine 1.0.7, ArduinoJson 7.4.2, ESP32Servo 3.0.9, RTClib 2.1.4, Adafruit BusIO 1.17.2.
ESP32 Arduino core is pinned to 3.2.0 for CI.

Important compatibility detail: the published AgileStateMachine 1.0.8 header failed strict ESP32 compilation
because of extra member qualifications. Do not upgrade to it casually.
Native checks use the exact 1.0.7 release commit, matching the board build.
Do not replace it with development-main source just to make native tests pass.

From the repository root:

~~~sh
python -m pip install -r requirements-dev.txt
python scripts/check_native.py --events
python -m pytest -q
python scripts/http_demo.py
python scripts/build_wokwi.py
~~~

The native command needs a C++17 compiler (g++ or clang++, or CXX).
On Windows, determine which compiler/runtime is available instead of assuming Bash commands work.
Arduino IDE or CLI can compile the actual board sketch. The exact CLI commands are in firmware/README.md.
GitHub Actions checks native logic/API/HTTP replay and compiles both the canonical and generated sketches.

Current validation evidence and limitations are authoritative in docs/VALIDATION.md.
Do not reuse the old Python prototype's 40-test claim for the new code.

## Wokwi: no paid custom-library upload

The library-manager screenshot the user supplied contains Arduino/C++ libraries.
Those packages work with the Arduino implementation now used.
A generated Wokwi project needs sketch.ino, diagram.json and libraries.txt.
Use https://wokwi.com/projects/new/esp32 and paste the generated files.
The generator combines our source only; it does not copy dependency internals.
It deliberately reads settings.example.h and never embeds settings.local.h.

Saving a Wokwi project does not synchronize this repository.
A successful compile is not evidence of an observed Wokwi browser run.
Do not claim the current assistant executed the browser simulation unless a real browser run has been performed.

## What is implemented

- Explicit permitted FSM transitions and state entry actions.
- Due occurrence eligibility and matching-user authorization before movement.
- HOMING, POSITIONING, RELEASING and VERIFYING, each with a deadline.
- Motor/feedback operations receive the intended compartment/dose.
- An obstructed pre-release sensor blocks release.
- One observed passage during release/verification, plus a settling interval.
- Extra observed passage or absent feedback locks ERROR without automatic retry.
- Persistent attempts recorded before movement, including quarantined slot inventory.
- Completed slots become spent; tomorrow does not silently refill them.
- Reboot after an interrupted attempt or fault requires inspection.
- Versioned config persistence, stale/reused revision checks and busy deferral.
- Critical-event outbox with unique boot-session/sequence IDs and acknowledged removal.
- HTTP requests executed in a separate FreeRTOS task via copied queue messages.
- Reference API with expected-revision edits, applied acknowledgements, history and deduplicated mock SMS.

Transient serial diagnostic events are not all durable API events.
Do not post every console line to the endpoint; follow INTERFACE.md.

## Crucial physical assumptions

The simulation assumes SIX compartments, each holding ONE preloaded item.
This is a provisional software model, not an agreed mechanical decision.
The servo visualizes release only. Homing/indexing are simulated by timing.
Buttons simulate matching-user and passage feedback; no real biometric algorithm is implemented.

SIMULATION_PROFILE=false selects UnconfiguredMechanism and blocks operation.
It is not a production-readiness switch.

Before implementing a real driver, obtain:
- Whether storage is preloaded doses, one item per slot, or bulk pills.
- Actual compartment count, position numbering, motor/driver, gear ratio and homing reference.
- Release sequence, position feedback, sensor placement/polarity/pulse characteristics.
- Definition of success and safe-stop behavior.
- Refill, inventory confirmation, interrupted-power and fault-inspection procedure.
- Exact fingerprint module, matching IDs and enrolment method.
- Physical access lock, RTC, supply and reviewed wiring.

Use docs/MECHANISM_BRIEF.md with mechanical/electronics members.
A bulk counting design could require changing the workflow and contract.
Do not merely replace a pin number and claim it is supported.

The Wokwi button's 40 ms debounce is not a physical pill-sensor driver.
Real pulses may need interrupts or input capture and measured filtering.
The simulation's timings/settling interval are not physical calibration.
A passage proves neither pill identity, a medically correct full dose, nor ingestion.

## Persistence boundaries

The ESP32 stores one version-2 JSON snapshot in one Preferences/NVS key.
Only the main task accesses it.
Storage is bounded: 12,000 bytes and 24 pending critical events.
No silent dropping or automatic reset/pruning exists.
Long-term retention, flash wear, write latency and physical maintenance remain design work.
Tests do not establish behavior under every real flash/power failure.

The explicit erase-demo serial command is available only in the simulation profile.
It is for disposable demonstration state. Never turn it into physical fault recovery.
No physical refill or enrolment workflow has been implemented.

## Communication contract

Read integration/INTERFACE.md for full JSON examples.
Route prefix: /api/v1/devices/{device_id}.
Event schema_version is 2; route /v1 and event schema are separate version concepts.

Config: revision, timezone=Asia/Kolkata, schedules[].
Each schedule: id, time=HH:MM, compartment, enabled, auth_user_id.
Daily occurrence identity: date:schedule_id, independent of config revision.
Extra fields are rejected; preserve app-only medication details in the app/backend through mapping.

The app saves with expected_revision. The backend increments desired revision.
The ESP32 persists a supported configuration while idle, then acknowledges applied.
A busy device sends deferred. The app must distinguish saved from applied.
Changing config cannot clear a device fault or refill a slot.

Critical events: dose_due, authorized, dispensed, missed, error.
event_id = device_id:session_id:sequence.
Only an exact matching acknowledgement removes an event.
Backend identical replay is idempotent; changed content under the same ID is rejected.
elapsed_ms is since boot. occurred_at is currently null.
received_at is backend UTC receipt time, not the original event time.
History must not label dispensed as taken.

The service currently records mock SMS only; no real provider is contacted.
A production account/provisioning system is not implemented.

## Existing app: next substantial task

When source arrives:
1. Inspect its framework, manifests, existing backend, data model, routes and mocks.
2. Run it using its actual instructions; preserve useful UI and existing work.
3. Reuse its backend or the reference service as appropriate; do not create two disconnected databases.
4. Map medication names/instructions to stable device schedule IDs and supported physical slots.
5. Implement expected-revision edits and saved/applied status.
6. Replace mock history with actual service results.
7. Keep device-side authorization and due-dose checks authoritative.
8. Add a connected app → service → ESP32/Wokwi → history demonstration.
9. Verify offline reconnect/retry and SMS idempotency before adding real delivery.

Do not wait for completed CAD to agree software interfaces.
Do wait for construction details before claiming a correct physical release sequence.

## Networking caveats that matter to setup

The default has ENABLE_NETWORK=false and empty service credentials.
For a real connection, copy settings.example.h to ignored settings.local.h and edit it.
The worker handles Wi-Fi/HTTP only. Only the main task touches the controller, JSON state,
Preferences, sensors and actuators.

Wokwi's public gateway can reach internet services, not a local computer's localhost.
Private Codespaces URLs require GitHub authentication; an ESP32 does not inherit the browser session.
HTTPS needs the issuing root CA and valid time. Certificate verification is not disabled.
For Wokwi, put deliberate simulation settings into a private copy of the generated sketch.
Use demo data and keep tokens out of committed source.

## Style and scope

Prefer plain, understandable code and comments describing the physical meaning.
Use community component/protocol libraries where they reduce maintained code.
Do not build a custom FSM engine, HTTP parser, fingerprint matcher or JSON parser.
Keep the five-member collaboration instructions detailed.
Update documentation when code or assumptions change.
Be explicit about what was tested, compiled, simulated or physically observed.
