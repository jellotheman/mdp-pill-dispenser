# Shared project decisions

Keep this short. Add the decision, who agreed it and when.

## Current prototype choices
- Five contribution folders: firmware, mechanical, electronics, app, integration.
- Firmware: MicroPython on ESP32, with pysm for the FSM.
- Development: browser Codespaces for Python logic and tests; online Wokwi for
  the interactive circuit. They are separate tools, not automatically synchronized.
- One servo gate and one compartment in the first simulation.
- Buttons stand in for biometric matching and pill-drop detection.
- JSON events over the serial console; SMS requests are mocked.
- A recorded interrupted/error dispensing attempt requires inspection, not retry.

## Team decisions still needed
| Question | Members who should agree | Decision |
| --- | --- | --- |
| Final tray/gate mechanism and compartment count | mechanical + electronics + firmware | pending |
| Motor, driver, homing and position feedback | mechanical + electronics + firmware | pending |
| Fingerprint module and enrolment method | electronics + firmware | pending |
| Pill sensor and physical lock | mechanical + electronics + firmware | pending |
| RTC and power arrangement | electronics + firmware | pending |
| App framework and backend framework | app + integration | pending |
| Serial/HTTP/MQTT transport and schedule sync | integration + firmware + app | pending |
| Real SMS transport | electronics + integration | pending |

Do not silently treat a simulated part as the final hardware choice.
