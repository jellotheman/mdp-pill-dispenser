# Community libraries and references

## Library included in the firmware
- pysm 0.4.0 by Piotr Gularski, MIT: https://github.com/pgularski/pysm/tree/v0.4.0
- firmware/pysm.py contains upstream pysm/pysm.py from that tag, with an added source/licence header; library code is unchanged.
- Copyright and permission notice: third_party/PYSM-LICENSE.txt.
- The controller uses State, StateMachine and Event for explicit permitted transitions.
- It is included in the repository so Wokwi needs no network or package installation.
- Python's json/os and MicroPython's machine/time provide storage, GPIO, PWM and timing.
- pytest 8.4.2 runs development tests; it is not installed on the ESP32.

## Design references (not copied firmware)
- https://github.com/shriramprasannak/ESP32-Smart-Medicine-Reminder-and-Automatic-Pill-Dispensing-System
  Inspected ESP32_Smart_Medicine_Reminder.ino.ino and diagram.json: reminder, servo and simulated wiring example. Our controller adds authorization before motor movement.
- https://github.com/Willykengineering/Automatic-Supplement-Pill-Dispenser
  Inspected src/main.cpp: nonblocking motor progress, scheduling and browser control.
  Its stepper carousel is not implemented by our one-servo simulation.
- https://github.com/Shaztech/Pilldispenser
  Inspected Arduino/PillDispenser/Check_Alerts.ino and Dispense_Rooutine.ino:
  staged motor actions, reminders, persistent dose status and notification concepts.
  No touchscreen, Telegram implementation or multi-tray mechanism is copied.

This is original application logic around the included library. Teammates should
check and retain the license for any further source code or CAD they reuse.
