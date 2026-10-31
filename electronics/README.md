# Electronics and hardware

Follow [the team guide](../docs/TEAM_GUIDE.md) for access and upload instructions.

## Put these here
- components.csv: exact modules, quantities, approximate prices and links.
- wiring.pdf or wiring.png: labelled diagram, including all power/ground lines.
- editable schematic/Fritzing/KiCad file where available.
- pin-map.csv: review the existing provisional simulation map.
- power.md: supply needs, motor driver, common ground and voltage compatibility.

## First milestone
Choose plausible components and show how they connect. Coordinate board/motor
dimensions with mechanical design and pins/interfaces with Sreeram.

The existing diagram.json in firmware/ is only a Wokwi simulation. Its buttons
replace a fingerprint module and pill-drop sensor. Its one servo is a demonstration
gate, and its DS1307 wiring is not an approved physical wiring plan.

Do not power a real motor from a GPIO. Check the selected supply, driver, current,
pull-ups/logic levels and shared ground before construction. Confirm RTC and
fingerprint module electrical requirements using their actual documentation.

## Decisions to report
1. Exact ESP32 board.
2. Motor type, driver and control interface.
3. Fingerprint module with onboard matching and its interface.
4. RTC model and clock-setting plan.
5. Pill sensor and output signal.
6. Physical lock arrangement.
7. SMS transport proposal, coordinated with integration.
8. Wiring/power assumptions still waiting on another member.

## References
- https://github.com/Willykengineering/Automatic-Supplement-Pill-Dispenser
- https://github.com/Shaztech/Pilldispenser
- https://github.com/shriramprasannak/ESP32-Smart-Medicine-Reminder-and-Automatic-Pill-Dispensing-System

After uploading, state which diagrams/files are editable, which parts are selected
and which wiring has actually been checked.
