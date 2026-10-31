# Community libraries and references

Firmware dependencies are installed through Arduino/Wokwi Library Manager:

| Dependency | Version | Purpose / upstream |
| --- | --- | --- |
| AgileStateMachine | 1.0.7 | FSM transitions and entry callbacks — https://github.com/cotestatnt/AgileStateMachine/tree/1.0.7 |
| ArduinoJson | 7.4.2 | Configuration, events and persistent snapshots — https://github.com/bblanchon/ArduinoJson/tree/v7.4.2 |
| ESP32Servo | 3.0.9 | Simulated release servo — https://github.com/madhephaestus/ESP32Servo |
| RTClib | 2.1.4 | Simulation DS1307 clock — https://github.com/adafruit/RTClib |
| Adafruit BusIO | 1.17.2 | RTClib bus dependency — https://github.com/adafruit/Adafruit_BusIO |
| ESP32 Arduino core | 3.2.0 | GPIO, Wi-Fi, HTTP, FreeRTOS and Preferences/NVS — https://github.com/espressif/arduino-esp32 |

AgileStateMachine 1.0.8 as published through Library Manager failed strict ESP32 compilation
because its header contains extra member qualifications. The code uses the unmodified 1.0.7 release.
Native tests download the exact 1.0.7 commit (86caf5514103b9f393c041da0cbc2ce94c066de2),
matching the release used by the board build. No permissive compiler flag or patched library is required.
The controller owns dynamically registered transitions for this library version.

The generator combines only our application source. It does not copy library internals.
Retain the upstream libraries' licences when redistributing a firmware bundle or their source.

The reference service uses FastAPI, Pydantic, Uvicorn and Python's sqlite3/json;
development checks use pytest and httpx. Their installed dependencies are recorded by their package managers.

Design references (not copied source):
- https://github.com/Willykengineering/Automatic-Supplement-Pill-Dispenser
- https://github.com/Shaztech/Pilldispenser
- https://github.com/shriramprasannak/ESP32-Smart-Medicine-Reminder-and-Automatic-Pill-Dispensing-System

The team has not adopted any reference mechanism as its agreed physical construction.
The original MicroPython/pysm prototype and its attribution remain on legacy/micropython.
Check actual licences before reusing third-party CAD or source.
