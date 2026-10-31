# Codex handoff: MDP smart pill dispenser

Read this file when continuing in the local Codex app. It is self-contained.
Repository: https://github.com/jellotheman/mdp-pill-dispenser (private).
Owner: jellotheman. Firmware lead: Sreeram Biju.

## Current request and direction

The user wants understandable, maintainable firmware that uses community libraries,
can be demonstrated in free Wokwi, and can progress toward the physical product.
They can read Arduino code and explicitly prefer the simpler Arduino/library-manager route.
Do not switch back to Python firmware merely because earlier messages preferred Python.

The default branch is main. It contains Arduino/C++ firmware. Companion/presentation changes may
still be on an active feature branch; inspect git status/log before switching away from it.
The original MicroPython prototype, including pysm and its original tests, is preserved on legacy/micropython.
A temporary implementation branch, firmware/product-interfaces, may also exist.
The user requested the Arduino work back on the default branch.

The supplied companion app is now under app/: a Next.js/React PillPilot dashboard. Its original visual
design is retained and its in-memory store is replaced with the shared FastAPI/SQLite service.
Start with README.md and docs/PRESENTATION.md. Run present.cmd for a new disposable local presentation
in external APP/API/BRIDGE terminal windows; --no-setup reuses the prepared build. The launcher creates
a session-specific connected package under the session's wokwi/ folder. Firmware runs in the existing
Wokwi project after uploading that package. Do not add another device simulator; the user explicitly
prefers connected Wokwi. --local-only skips the MQTT bridge.

User operational requirements: close test terminal windows when starting/restarting or finishing
tests, and leave only the final APP/API/BRIDGE presentation windows open. Stop only the processes
owned by this project/session; do not stop unrelated laptop programs or rely on stale numeric PIDs.
Explain the three final terminal roles when handing the presentation back to the user.

The five roles remain:
1. Sreeram: ESP32 firmware and simulation.
2. Mechanical: compartments, mechanism, enclosure and CAD.
3. Electronics: components, wiring, power and actual sensor/motor interfaces.
4. Companion app: existing app and its UI/data layer.
5. Communication/integration: shared API, schedule/device synchronization, history and SMS.

## Start safely in the local clone

1. Read git status and inspect local changes before any checkout/pull.
2. Preserve uncommitted work or divergent commits on a personal branch; never reset --hard to simplify an update.
3. Determine the active branch and whether its work is already on main. Preserve unfinished feature
   work; only switch/update main when that matches the continuation task.
4. Read README.md, firmware/README.md, docs/ARCHITECTURE.md,
   integration/INTERFACE.md, docs/MECHANISM_BRIEF.md and docs/VALIDATION.md.
5. Check that the local files actually match the descriptions here.
6. Work in a branch for changes that affect shared interfaces.
7. The user has authorized implementation and testing; routine reversible implementation choices do not need repeated permission.

~~~sh
git status --short --branch
git log -5 --oneline
~~~

If Git later reports divergence while updating, inspect and reconcile it rather than force-pushing or dropping work.
The Python branch should remain available.

## Source map

- firmware/PillDispenser/PillDispenser.ino: board setup/loop, NVS adapter, buttons, RTC and indicators.
- firmware/PillDispenser/DispenserCore.h: board-independent contract, storage, occurrence logic,
  declarative FSM and mechanism interface.
- firmware/PillDispenser/HttpSync.h: ESP32 HTTP worker and main-task synchronization.
- firmware/PillDispenser/MqttSync.h: optional simulation-only MQTT worker and main-task synchronization.
- firmware/PillDispenser/settings.example.h: demonstration constants.
- firmware/PillDispenser/settings.h: loader for settings.local.h or defaults.
- firmware/PillDispenser/settings.local.h: optional local override, deliberately ignored by Git.
- firmware/PillDispenser/libraries.txt: pinned standard Library Manager entries.
- firmware/PillDispenser/diagram.json: demonstration circuit.
- integration/service.py: FastAPI/SQLite reference backend.
- integration/mqtt_bridge.py: optional MQTT-to-reference-API demonstration bridge.
- app/: supplied Next.js dashboard, server-only service proxy and shared UI contract.
- scripts/present.py / present.cmd: repeatable setup and external-console presentation launcher.
- scripts/build_connected_wokwi.py: session-specific connected Wokwi package.
- scripts/native_build.py: pinned native dependency/compiler setup for controller tests.
- tests/native/test_controller.cpp: scenarios executing the actual C++ controller.
- tests/native/Arduino.h: only the clock/type shim needed by the actual FSM library.
- tests/test_integration.py: service behavior.
- scripts/check_native.py: pinned dependency fetch, native build and scenario run.
- scripts/http_demo.py: real loopback HTTP replay of actual C++ events.
- scripts/build_wokwi.py: combines our source into output/wokwi/sketch.ino.
- docs/TEAM_GUIDE.md: verbose browser-upload/collaboration instructions for beginners.

## Dependencies and builds

Firmware dependencies are unmodified Library Manager packages:
AgileStateMachine 1.0.7, ArduinoJson 7.4.2, ESP32Servo 3.0.9, RTClib 2.1.4, Adafruit BusIO 1.17.2,
PubSubClient 2.8.
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
- Optional MQTT simulation transport and bridge use the same strict configuration and event contracts.
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

## Presentation continuation on this laptop

1. Read PRESENTATION.md, VALIDATION.md and QUALITY_REVIEW.md. Do not infer runtime success from the
   setup instructions or earlier compiled/native checks.
2. The user's existing Wokwi project is https://wokwi.com/projects/479372515382840321 . It originally
   has the canonical headers plus a renamed sketch.ino. Prefer the supported generated three-file
   package for repeatable setup. No separate settings file is currently emitted by the connected
   builder: do not invent a nonexistent output path.
3. Run `present.cmd` after preparing dependencies, or `present.cmd --no-setup` for the current build.
   The printed ignored session directory holds session.json, SQLite and generated wokwi/ files.
   A fresh session has a fresh MQTT namespace; load its three files into Wokwi. API tokens stay local.
4. The shared public broker is untrusted: anyone can read or forge messages. Namespace randomness
   prevents accidental collisions, not malicious access. Only synthetic simulation data is allowed.
   Do not use this transport for physical devices or real patient/medication information.
5. Check VALIDATION.md for actual runtime evidence; compiling a sketch or passing API tests does
   not prove a completed Wokwi-to-service-to-dashboard cycle.
6. Browser access: the supported in-app browser reached Wokwi signed in as jellotheman. Native Firefox
   computer control hit a URL-policy block. Use the supported browser surface rather than trying to
   bypass that restriction. Reinspect live browser state; prior control handles are not reusable.
7. A file chooser stalled during setup; Escape recovered it. Browser editor paste worked. Keep
   canonical headers aligned and prefer the generated complete package for repeat presentation.
8. Stop/close temporary test servers before the final startup. Leave only final APP, API and BRIDGE
   windows. APP serves the dashboard; API owns SQLite/config/history; BRIDGE exchanges simulated
   messages with the broker. Wokwi remains the ESP32 execution environment.

## Ownership for continued changes

- app/: preserve the supplied design. Components own panels; use-dashboard owns polling/edits;
  contract schemas validate the UI boundary and the server route supplies the backend token.
- integration/: integration teammate's working reference and extension point. Keep one store,
  atomically save labels/config, retain revision conflicts and exact idempotent event acknowledgements.
- firmware/: local scheduling, authorization, persistent occurrences/outbox and mechanism safety.
  Firmware remains Arduino/C++; Python is only the backend/development/presentation tooling.
- scripts/present.py: setup and external presentation processes; build_connected_wokwi.py: session
  package. Ordinary build_wokwi.py stays the standalone safe default.
- mechanical/electronics/: supply the actual release design, component/pin/power details, feedback,
  refill and inspection procedure before real adapters are implemented.

## Companion app and next integration work

The app now saves labels and firmware schedules atomically through the reference service. The
companion endpoint preserves labels outside the exact device config schema. Its expected_revision
guards concurrent edits. The dashboard displays real service history and applied acknowledgements;
it no longer fabricates dose events or uses a preview-only pause toggle.

The launcher starts the app, reference service and MQTT bridge. Firmware remains the Arduino/C++
ESP32/Wokwi implementation; its network messages use the same configuration and event contracts.
Browser Wokwi cannot reach laptop localhost directly through the public gateway. The generated
package configures the shared broker and current-date 07:59:30 demonstration RTC.
Do not manufacture device acknowledgements or dose history to make the dashboard appear connected.
The integration teammate still owns provisioning, deployment, access control and real SMS delivery.
Connect and observe the distinct ESP32/Wokwi networking path after configuring a reachable endpoint.

Do not wait for completed CAD to agree software interfaces.
Do wait for construction details before claiming a correct physical release sequence.

## Networking caveats that matter to setup

The default has ENABLE_NETWORK=false and empty service credentials.
For a real connection, copy settings.example.h to ignored settings.local.h and edit it.
The optional MQTT transport is simulation-only; HTTP remains available. Only the main task touches the controller, JSON state,
Preferences, sensors and actuators.

Wokwi's public gateway can reach internet services, not a local computer's localhost.
Private Codespaces URLs require GitHub authentication; an ESP32 does not inherit the browser session.
HTTPS needs the issuing root CA and valid time. Certificate verification is not disabled.
For Wokwi, use the deliberate synthetic simulation settings in the generated session sketch.
Use demo data and keep tokens out of committed source. See integration/README.md for broker limits.

## Style and scope

Prefer plain, understandable code and comments describing the physical meaning.
Use community component/protocol libraries where they reduce maintained code.
Do not build a custom FSM engine, HTTP parser, fingerprint matcher or JSON parser.
Keep the five-member collaboration instructions detailed.
Update documentation when code or assumptions change.
Be explicit about what was tested, compiled, simulated or physically observed.
