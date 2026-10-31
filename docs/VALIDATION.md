# Validation results

Checks performed through GitHub Actions on 31 October 2026.

## Results
- Python 3.12: **40 tests passed**.
- Automatic terminal demonstration: passed success, rejected fingerprint,
  repeated occurrence, missed authentication window and missing pill-drop cases.
- Real MicroPython 1.26.0 Unix interpreter: smoke test passed imports, bundled
  pysm transitions, JSON journal writes/reload, duplicate suppression and scheduling.

[Workflow run](https://github.com/jellotheman/mdp-pill-dispenser/actions/runs/41162210554)

Tested revision: 561ccba9ccf14045df32c37f4dc31065ff8b150d.
Both jobs completed successfully. Later documentation edits do not change the
tested firmware.

## What those tests cover
Authorization timing, repeated inputs, reminder/missed events, persistence and
interrupted attempts, corrupt/incomplete journals, motor/drop timeouts, schedule
validation and daily occurrence ids, button debouncing, servo command timing and
RTC decoding. The MicroPython smoke uses a fake motor with the actual interpreter.

The terminal demonstration produces an events artifact on the workflow run.
You can download it from the run page or generate it again with
python scripts/demo.py.

## Still to check
- Wokwi circuit rendering and an interactive browser run.
- ESP32-specific machine/PWM/I2C behaviour with the selected firmware.
- Real motor, sensor, fingerprint, lock and power operation.
- App/backend/device transport and real SMS delivery.

The simulator buttons stand in for sensors. A software smoke test on MicroPython
Unix is not an ESP32 hardware test, and detecting a drop does not prove ingestion.
