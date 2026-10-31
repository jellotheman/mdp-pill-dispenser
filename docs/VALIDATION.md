# Validation evidence and limits

## Earlier Arduino/C++ validation

Successful run:
https://github.com/jellotheman/mdp-pill-dispenser/actions/runs/41171980287

Implementation commit checked by that run:
b7c87a32f49f91478fa43eae5049e1f5f3637de8

Results:
- 42 native C++ firmware scenarios passed using the actual DispenserCore.h.
- The actual AgileStateMachine 1.0.7 and ArduinoJson 7.4.2 libraries were used.
- 17 reference API tests passed.
- A real loopback HTTP demonstration passed schedule save/fetch, an explicitly simulated applied
  acknowledgement, replay of C++-generated events, duplicate acknowledgement and one history outcome.
- The canonical ESP32 Arduino sketch compiled with core 3.2.0 and pinned dependencies.
- The generated single-file Wokwi sketch also compiled for ESP32.

The final default-configuration packaging was included in that successful run, and that implementation
is now on main. Later documentation-only changes do not change the checked firmware source.
Inspect the current Actions result when changing source.

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

- The compiled ESP32 Wi-Fi/HTTP/FreeRTOS path actually running against a reachable backend.
- Real fingerprint matching/enrolment or physical passage sensing.
- Actual homing, indexing, release reliability, physical access lock or power system.
- Physical refill/fault recovery, long-term storage policy or arbitrary power-loss behavior.
- Real SMS delivery.

The simulation assumes six slots containing one item each and uses virtual homing/indexing.
The physical profile is deliberately blocked.
A compilation result and a simulated passage do not establish physical-product correctness.

## Companion integration and presentation

The supplied app is now integrated with the shared reference service. Firmware remains the existing
ESP32/Wokwi implementation; no additional device simulator is used. See PRESENTATION.md for the
presentation setup and networking requirements. The earlier Actions run above predates this app
integration; do not treat it as validation of the newly added app or launcher. Record current command
results separately after running them.

### Connected MQTT presentation, 31 October 2026

The generated MQTT sketch compiled in the browser Wokwi project. The simulated ESP32 connected to
HiveMQ, received the service's revision 1 schedule and acknowledged it; the dashboard showed Applied
r1. A simulated matching fingerprint and one simulated passage produced a dispensed event, which
arrived in the SQLite-backed API and appeared in the dashboard history. The dashboard's read-only API
check also succeeded. This validates one demonstration path, not a physical device or an adversarial
public network. The earlier attempted HTTP tunnel did not complete device synchronization and is not
the presentation path.

Local checks: 42 native controller scenarios; 38 Python tests including bridge and package tests;
six dashboard origin tests; app lint, TypeScript checking and production build. The public broker also
passed a synthetic-client configuration/event/receipt test. Public broker availability can vary.

Test/presentation terminals must be stopped and closed before restarting or finishing tests. Only
the final APP, API and BRIDGE windows should remain for the user; generated packages and session
credentials remain in ignored output/ rather than committed source.

## Original Python implementation

The earlier 40-test Python prototype and MicroPython smoke check remain on legacy/micropython.
Those historical results are not evidence for this Arduino implementation.
