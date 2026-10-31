# Validation evidence and limits

## Arduino/C++ implementation

Successful run:
https://github.com/jellotheman/mdp-pill-dispenser/actions/runs/41171457317

Implementation commit checked by that run:
84b827b317d7fc89dae586be190e90a0b77bbf38

Results:
- 42 native C++ firmware scenarios passed using the actual DispenserCore.h.
- The actual AgileStateMachine 1.0.7 and ArduinoJson 7.4.2 libraries were used.
- 17 reference API tests passed.
- A real loopback HTTP demonstration passed schedule save/fetch, an explicitly simulated applied
  acknowledgement, replay of C++-generated events, duplicate acknowledgement and one history outcome.
- The canonical ESP32 Arduino sketch compiled with core 3.2.0 and pinned dependencies.
- The generated single-file Wokwi sketch also compiled for ESP32.

The final documentation/default-configuration packaging update is checked again before promotion to main.
A later passing run on main supersedes the commit link above; inspect the current Actions result.

## What the native scenarios cover

Correct and incorrect user matching, exact authentication deadline, repeated matching,
busy/expired occurrences, duplicate suppression, persisted state across reboot,
interrupted attempts, storage failure, sensor obstruction, early/extra/missing passages,
stage timeout, unknown physical hardware, config revisions and busy deferral,
schema rejection, dated scheduling, outbox acknowledgement/session identity,
outbox exhaustion, compartment depletion and monotonic time checks.

The native Arduino.h shim supplies only the clock/types required by the real FSM library.
GPIO, NVS, HTTPClient, Wi-Fi and FreeRTOS are not executed by that runner.

## What the API checks cover

Saved versus applied state, edit conflicts, deferred/rejected/future acknowledgements,
token checking, identical replay, changed-content conflicts, device identity,
mock SMS deduplication, schedule rejection and SQLite persistence across service restart.

The HTTP replay uses a real loopback socket and temporary SQLite backend.
Its device applied acknowledgement is deliberately simulated.
It does not claim that the ESP32 network task fetched/acknowledged the configuration.

## Not yet observed or validated

- Browser Wokwi execution/animation.
- The compiled ESP32 Wi-Fi/HTTP/FreeRTOS path actually running against a reachable backend.
- Integration of the user's existing app, whose source is still pending.
- Real fingerprint matching/enrolment or physical passage sensing.
- Actual homing, indexing, release reliability, physical access lock or power system.
- Physical refill/fault recovery, long-term storage policy or arbitrary power-loss behavior.
- Real SMS delivery.

The simulation assumes six slots containing one item each and uses virtual homing/indexing.
The physical profile is deliberately blocked.
A compilation result and a simulated passage do not establish physical-product correctness.

## Original Python implementation

The earlier 40-test Python prototype and MicroPython smoke check remain on legacy/micropython.
Those historical results are not evidence for this Arduino implementation.
