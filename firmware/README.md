# ESP32 Arduino firmware — Sreeram

## What changed

The firmware uses Arduino/C++ and dependencies available through Arduino/Wokwi Library Manager.
There is no project-owned pysm.py to copy or explain. The earlier MicroPython implementation is in Git history.

| File in PillDispenser/ | Purpose |
| --- | --- |
| PillDispenser.ino | setup/loop, buttons, indicators, RTC, NVS adapter and wiring |
| DispenserCore.h | Schedule validation, durable state/outbox, FSM and mechanism contract |
| HttpSync.h | Queued HTTP requests in a separate ESP32 task |
| settings.h | Safe demonstration defaults; optional ignored settings.local.h override |
| diagram.json | Wokwi simulation circuit |
| libraries.txt | Exact Library Manager versions |

The source is separated to keep responsibilities readable.
scripts/build_wokwi.py combines our source into one sketch.ino for the website.
It does not copy third-party library internals or private local settings.

## Open in free browser Wokwi, step by step

1. Run python scripts/build_wokwi.py from the repository root.
   Alternatively, download the wokwi-arduino-and-example-events artifact from a successful Actions run.
2. Open https://wokwi.com/projects/new/esp32 .
3. Confirm the editor contains sketch.ino. This is an Arduino project.
4. Replace all of sketch.ino with output/wokwi/sketch.ino.
5. Replace diagram.json with output/wokwi/diagram.json.
6. Open Library Manager and press its + button.
7. Search for and add AgileStateMachine, ArduinoJson, ESP32Servo, RTClib and Adafruit BusIO.
8. Set the versions to those in output/wokwi/libraries.txt. You can create/edit libraries.txt and paste
   its contents directly to specify the versions.
9. Press Play.
10. After five simulated seconds, dose_due and reminder should appear.
11. Press/release red to simulate an incorrect user; no dispensing movement is authorized.
12. Press/release green to match user 1.
13. Observe homing, positioning and releasing. Homing/indexing are virtual;
    the servo visibly moves only for release.
14. During release or shortly afterward, press/release blue once for one simulated passage.
15. After release and a short verification settling period, look for dispensed and the green LED.
16. Ignore the dose at 35 seconds to show missed.
17. Authorize the dose at 65 seconds but omit the blue input to show an error without another attempt.

Do not press blue during homing/positioning: that input is intentionally ignored.
Holding blue before release should block release because the sensor is obstructed.
Two separate blue passages during the active verification interval should produce an error.
Button debouncing is a simulation input filter, not a driver for a fast physical beam sensor.

### What the library-manager screenshot means

Wokwi's Library Manager lists Arduino/C++ libraries. Its paid custom-library upload feature is
for Arduino library source packages. Our dependencies are standard manager entries, so custom upload is unnecessary.

The Python workflow instead imports Python modules from the simulated filesystem.
Sources: https://docs.wokwi.com/guides/libraries and https://docs.wokwi.com/guides/micropython .

### Repeat a disposable demonstration

The state survives whenever the simulator retains NVS. Used slots and occurrence IDs stay recorded.
In the serial monitor, send erase-demo followed by Enter to explicitly clear ONLY this disposable
simulation's NVS namespace and restart.

That command exists only when SIMULATION_PROFILE=true.
Never make clearing storage automatic or use it as a physical recovery/refill procedure.
Wokwi reset/power persistence is not evidence about arbitrary real power failures.

## Daily schedules and the clock

Set DEMO_TIMERS=false to use the DS1307 and synchronized daily schedules instead of the 5/35/65-second examples.
An empty schedule is intentional until a configuration is applied.
In the serial monitor, send this as one line:

~~~json
{"command":"apply_config","config":{"revision":1,"timezone":"Asia/Kolkata","schedules":[{"id":"morning","time":"08:00","compartment":1,"enabled":true,"auth_user_id":1}]}}
~~~

The supplied RTC starts at 07:59:55 on 31 October 2026. Configure before starting the run
or use a suitable future time; expired occurrences are marked missed, not immediately dispensed.
Use the backend and HTTP sync for the actual app route.

The daily authentication window is two minutes; timer demos use twenty seconds.
Occurrence identity is date + schedule ID, independent of configuration revision.
Editing a time does not grant a second release of the same occurrence on that date.
Timezone is fixed to Asia/Kolkata in this prototype; the RTC must be deliberately set to that local time.

## Connect the reference backend

1. Follow integration/README.md to start the API.
2. Copy settings.h to settings.local.h beside the sketch. Keep the override outside Git.
   The override should contain the settings constants from the default branch of settings.h.
3. Set ENABLE_NETWORK=true, DEMO_TIMERS=false, the Wi-Fi details, DEVICE_ID,
   BACKEND_URL and DEVICE_TOKEN.
4. Use the same token in the backend's MDP_DEVICE_TOKEN environment variable.
5. Use an address the ESP32 can reach. On a physical device this can be the development computer's LAN address.
6. Browser Wokwi's public gateway can reach internet-accessible endpoints, not your computer's localhost.
   A private Codespaces URL also requires GitHub authentication; it is not automatically an ESP32 endpoint.
7. For HTTPS, supply the correct issuing root CA in BACKEND_ROOT_CA.
   The worker obtains NTP time for certificate validation. Certificate verification is never disabled.
8. For Wokwi, modify the generated settings section in your private simulation copy.
   The generator deliberately does not embed settings.local.h.
9. Look for the backend's applied_revision acknowledgement and resulting device history.

The network task owns Wi-Fi and HTTP requests. Only copied strings cross the queues.
Only the main task touches the controller, NVS and actuators.
Local schedules remain usable during network interruption until bounded storage needs attention.

## Compile for ESP32

Install Arduino CLI, then run:

~~~sh
arduino-cli core update-index --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core install esp32:esp32@3.2.0 --additional-urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli lib install "AgileStateMachine@1.0.7" "ArduinoJson@7.4.2" "ESP32Servo@3.0.9" "RTClib@2.1.4" "Adafruit BusIO@1.17.2"
arduino-cli compile --fqbn esp32:esp32:esp32 firmware/PillDispenser
~~~

Arduino IDE can open PillDispenser.ino and install the same libraries via Library Manager.
GitHub Actions compiles the canonical sketch and generated Wokwi sketch.

## Physical hardware remains a separate implementation

SIMULATION_PROFILE=false selects an UnconfiguredMechanism that refuses operation.
It does not turn the simulation into a verified physical driver.
Read docs/MECHANISM_BRIEF.md before implementing a real Mechanism subclass.
Retain the shared controller and replace sensor/motor adapters only after the actual construction is understood.
