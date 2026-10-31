# ESP32 firmware and simulation — Sreeram

## What to demonstrate

A dose becomes due, reminders start, an invalid fingerprint is rejected, a valid
fingerprint allows one motor movement, and a fresh pill-drop event confirms
dispensing. Ignoring the reminder marks the dose missed. A missing pill drop
locks the controller in ERROR instead of trying another release.

The code uses pysm, a community FSM library bundled as pysm.py with its licence.
It uses the ESP32's built-in MicroPython machine library for GPIO and PWM.

## Start with the browser terminal demo

1. Open the repository's **Code → Codespaces** tab.
2. Create a Codespace on main and wait for setup.
3. Open **Terminal → New Terminal**.
4. Run **python -m pytest -q**.
5. Run **python scripts/demo.py**.
6. Read the JSON event lines and the PASS line if all demonstration assertions pass.
7. Open output/demo-events.jsonl for the saved event example. It is a generated,
   ignored file; the CI run also uploads it as a downloadable artifact.

These run the same Controller and Journal classes that the ESP32 program uses.
They do not emulate an ESP32 processor or prove the wiring works.

For an interactive version run **python scripts/demo.py --interactive**.
Enter one command at a time:

```text
due
invalid
valid
advance 300
drop
advance 400
status
```

The result should be COMPLETED and motor_starts=1. Time advances only when you
enter advance. To return to IDLE, enter **advance 2000**.

To show a missed dose in a fresh interactive run:

```text
due
advance 20000
status
```

To show a failed dispensing attempt in a fresh run:

```text
due
valid
advance 700
advance 8000
status
```

ERROR intentionally stays locked. Quit and start a new terminal demonstration
for a clean session. This uses a temporary demo journal and does not erase a real
device's dose history.

## Visual ESP32 simulation in Wokwi

Use the online simulator in a second browser tab. This avoids installing or
licensing the VS Code Wokwi extension and managing MicroPython firmware images.

1. Open https://wokwi.com/projects/new/micropython-esp32 .
2. Check that it is a MicroPython project with main.py, not an Arduino sketch.
3. Replace its main.py contents with **firmware/main.py** from this repository.
4. Replace its diagram.json contents with **firmware/diagram.json**.
5. Use the file-tab menu to add **pysm.py**. Paste **firmware/pysm.py** into it.
   Keep this filename exactly; main.py imports the library by that name.
6. Leave DEMO_MODE = True near the top of main.py.
7. Start the simulation with the play button.
8. Read the serial monitor. It should print the instructions and, after five
   simulated seconds, a dose_due event and a reminder.
9. Press and release the **red button**. It represents a failed fingerprint.
   The servo should stay closed.
10. Press and release the **green button**. It represents successful fingerprint
    matching. The servo should move and then return.
11. Press and release the **blue button** during or just after that movement.
    It represents a pill passing the chute sensor. Do this within eight simulated
    seconds after the gate movement finishes.
12. Look for dispensed in the serial monitor and the completed green LED.
13. At 35 seconds the second dose becomes due. Do nothing to demonstrate a missed
    dose after its 20-second authentication window.
14. At 65 seconds the third dose becomes due. Approve with green but do not press
    blue; this demonstrates the drop-detection error and mock SMS request.

Buttons need a real click/release, not a held press. They are debounced and only
new presses count. The serial monitor says what each event means. The servo is
one demonstration gate, not a completed rotary tray.

Wokwi changes are a separate copy. Copy useful edits back to this repository and
commit them so the team receives them. Do not assume saving in Wokwi updated GitHub.
Do not publish a Wokwi copy if the team wants that copy private; check the Wokwi
account's project visibility options separately.

### Restarting demonstrations

The three demo dose ids are fixed. Within a persistent filesystem, completed or
missed ids stay recorded and are not offered again.

To reset a disposable Wokwi demonstration, interrupt it with Ctrl+C in the serial
monitor and use the MicroPython REPL to inspect the project files. After checking
it is only a simulation, remove dose-journal.json, and remove dose-journal.json.tmp
if an interrupted write left it behind. Then restart the simulation.

Never make automatic journal deletion part of normal startup. ERROR after a
restart means the mechanism/history must be inspected before allowing another
release. Power-cycle persistence in an online simulator is not a substitute for
testing the physical board's flash behaviour.

## Optional daily RTC schedule demonstration

The diagram includes a DS1307. The default timer demo does not need it.

1. Change DEMO_MODE to False in the Wokwi copy of main.py.
2. Leave the default morning schedule at 08:00.
3. The diagram's RTC starts at 07:59:55 on 31 October 2026, interpreted as local
   time by the simulator.
4. Start a fresh demonstration journal. Five seconds later the morning dose is due.
5. The daily mode gives a two-minute authentication window instead of the short
   20-second demo window.
6. Each occurrence id includes the date and schedule id so tomorrow's dose is
   distinct from today's.
7. A stopped, invalid or unreadable clock prevents normal operation. Check the
   traceback and circuit; do not invent a time or dispense anyway.

The RTC driver is a small demonstration reader. Real RTC choice, supply voltage,
I2C pull-ups/level conversion, battery and clock-setting procedure need electronics
review before connecting hardware.

## How the code fits together

| Part of main.py | Purpose |
| --- | --- |
| Settings | Demo timings and daily schedule examples |
| daily_candidates | Turn daily schedules and RTC time into dated dose occurrences |
| Journal | Record attempts/outcomes before allowing another release |
| Controller | FSM, reminders, approval, completion, timeout and event logic |
| DebouncedButton | Convert simulated buttons into one event per new press |
| ServoGate | Demonstrate one gate opening/closing; replace for the actual mechanism |
| read_ds1307 | Read optional simulation clock |
| run_board | Connect the controller to MicroPython GPIO and the simulation |

Permitted sequence: IDLE → WAITING_FOR_FINGERPRINT → DISPENSING → VERIFYING →
COMPLETED → IDLE. Waiting can also lead to MISSED → IDLE. A fault leads to ERROR.

The controller records started before commanding the motor. If the program
restarts with a started/error record or damaged journal, it locks for inspection.
This avoids blindly replaying an interrupted release. It is not a proof against
all flash failures or mechanical failures.

## What still needs the teammates

- Mechanical + electronics: choose the mechanism and motor, including how it
  homes, indexes a compartment and proves movement.
- Electronics: replace button inputs with a selected fingerprint module and
  sensor, agree power and pins, and add the physical locking arrangement.
- Integration: choose serial/HTTP/MQTT transport and real SMS delivery.
- App + integration: agree schedule editing and synchronization. The firmware's
  schedule list is currently configured in code, not downloaded from the app.

Fingerprint authentication here means the authorization workflow is simulated.
It does not enrol or match real fingerprints. SMS is represented by sms_requested
events only. Drop detection confirms a simulated release, not ingestion.

## Validation boundaries

pytest checks the shared Python logic, storage scenarios, button handling and
adapter behaviour using test doubles. The GitHub workflow can run it remotely.
Only a completed workflow is evidence those tests passed.

The actual Wokwi rendering/execution needs a browser run. Real electrical,
mechanical and biometric behaviour still needs physical testing. Keep these
claims separate in the project presentation.
