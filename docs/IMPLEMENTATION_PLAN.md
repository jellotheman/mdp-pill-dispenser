# Firmware improvement plan and status

1. Inspect the current Python prototype and identify domain/hardware/integration assumptions — complete.
2. Reassess the language after user steering; use Arduino/C++ and standard Wokwi dependencies — complete.
3. Preserve the original Python implementation on legacy/micropython — complete.
4. Introduce dose-aware mechanism operations and explicit stage/verification behavior — complete.
5. Add persistent inventory, occurrence status and acknowledged event delivery — complete.
6. Provide a reference configuration/history API while awaiting the existing app — complete.
7. Execute native/API/HTTP checks and compile canonical/generated ESP32 sketches — passed including final packaging; see VALIDATION.md.
8. Update beginner guides, contract, mechanism questions and local Codex handoff — complete.
9. Put the checked Arduino version on the default main branch — complete.
10. Integrate the supplied companion app with the shared API and prepare its local presentation — implemented; see PRESENTATION.md and current validation results.
11. Add an optional synthetic-data MQTT bridge and simulation transport — implemented; see VALIDATION.md
    for observed connected-run results, which are distinct from unit tests and compilation.
12. Design and implement physical hardware adapters, provisioning and secure deployment — pending
    agreed construction details and hardware testing.

The previous implementation remains recoverable; no user work is discarded.
The simulation mechanism is explicitly provisional and physical operation remains blocked.
