# Presenting PillPilot with Wokwi

The three project parts are the Arduino/C++ ESP32 firmware, the PillPilot companion dashboard,
and the Python reference integration service. The service stores schedules and receives events;
the ESP32 itself uses its clock and checks authorization. MQTT carries messages between the
service's bridge and Wokwi. No separate device simulator is needed.

## Start on Windows

Install Python 3.10+ with pip/venv and Node.js 20.9+ with npm. Internet and free ports 8000 and
3000 are needed. In PowerShell or Command Prompt at the repository root:

```powershell
.\present.cmd
```

The first run installs dependencies and builds the app. Wait for **Ready**; the launcher opens
the dashboard and three local terminal windows:

- **APP:** serves the dashboard at http://127.0.0.1:3000.
- **API:** hosts the reference service and local SQLite database; its interactive API documentation
  is at http://127.0.0.1:8000/docs.
- **BRIDGE:** synchronizes the API with MQTT. Keep it running to exchange device data.

Stop Wokwi and close previous test or presentation terminals before restarting. Leave only the
final presentation's APP, API and BRIDGE terminals running. Stop each with Ctrl+C when finished;
do not stop unrelated laptop programs.

The default demo connects through the free Wokwi public gateway and shared HiveMQ public broker.
**Use synthetic data only.** Other clients can read or forge messages on this broker. The generated
random topic reduces accidental collisions but does not authenticate a client. The demonstration
is unsuitable for real medication, patient or biometric data and is not a production system.
No fingerprint images or templates are part of the contract.

## Connect the existing Wokwi project

The launcher prints the session folder under ignored `output/presentation/`. Its `wokwi/` folder
contains `sketch.ino`, `diagram.json` and `libraries.txt`. Use all three from the same session:

1. Stop the simulation in [the existing Wokwi project](https://wokwi.com/projects/479372515382840321).
2. Replace each corresponding editor file with the generated file and press Play. The generated
   sketch contains the demo broker and session namespace; it does not contain the API token.
3. Leave APP, API and BRIDGE running. The dashboard shows a saved revision before the ESP32
   acknowledges applying it. An applied revision is an acknowledgement, not a live heartbeat.

The connected sketch uses daily schedules and a simulated RTC set to 07:59:30 on the current
Asia/Kolkata date. A fresh service has demonstration doses at 08:00 and 08:02, and a paused
08:05 dose. Wokwi simulation time can progress slower than wall-clock time. The standalone
`output/wokwi/` package has networking off and uses the 5/35/65-second offers instead.

## Walkthrough

1. Show the dashboard and use **Test integration API** to check the app-to-service request. This
   does not itself prove Wokwi is connected. Save or pause a schedule and show the saved and applied
   revisions once the firmware acknowledges it.
2. At 08:00 in Wokwi, press and release red to simulate an incorrect identity, then green to match
   user 1. During release or verification, press and release blue once for one simulated passage.
   Show the resulting dispensed event in history. It does not establish ingestion.
3. Let the 08:02 dose pass without authorization. Its two-minute window expires at 08:04; the
   firmware emits a missed event and the service records a mock notification, without sending SMS.
4. Enable the 08:05 dose before it is due and wait for the applied revision. At 08:05 press green,
   but omit blue. Verification times out and latches ERROR without a second release attempt. Show
   this last: editing a schedule cannot clear a fault.

History timestamps are service receipt times because device `occurred_at` is currently null. If
the simulator retains state from an earlier disposable run, send `erase-demo` in its serial monitor
to clear that simulation's stored state and restart. This is not a physical recovery procedure.

## Stop, restart and troubleshoot

Stop Wokwi, press Ctrl+C in APP, API and BRIDGE, and close their windows. For a new disposable
session with the existing build, run `present.cmd --no-setup`; after source changes, run the full
command. A fresh session gets a new database and MQTT namespace: load its new Wokwi files.
To resume an existing database, pass `--session` followed by the exact session.json path printed
by the launcher. Retained device state is separate from the database and is not automatically reset.
`--local-only` starts APP and API without a bridge; `--prepare-only` prepares dependencies without
opening presentation windows. On Linux the launcher uses xterm for separate windows.

- **Port occupied:** stop prior project terminals or use alternate API/app ports. The launcher does
  not stop unrelated processes.
- **Saved but not applied:** check BRIDGE and Wokwi serial output, internet access, matching broker,
  namespace and device ID. Busy firmware may defer an update. A public broker has no uptime guarantee.
- **API test passes but no device history:** the API test only exercises the app-to-service path;
  inspect the separate MQTT and ESP32 path. Do not fabricate an acknowledgement or event.
- **Offline:** the firmware retains its applied schedule and retries queued events within its bounded
  storage. A service restart with the same session retains service data.

## Extend the project

App panels and API diagnostics live under `app/components/`; `app/lib/use-dashboard.ts` manages
polling/edits and `app/api/dashboard/route.ts` keeps the service token server-side. The integration
teammate owns `integration/service.py`, `integration/mqtt_bridge.py`, deployment, device provisioning,
access control and real SMS. Preserve revision conflicts, atomic saves and deduplicated event receipts.
The firmware teammate owns `DispenserCore.h`, transport headers and the sketch's board I/O; real
mechanism, fingerprint and passage-sensor drivers remain future work. Consult
[the hardware brief](MECHANISM_BRIEF.md) before implementing physical actuation.

See [VALIDATION.md](VALIDATION.md) for observed results; this walkthrough describes intended behavior
and is not evidence that every runtime step has passed.
