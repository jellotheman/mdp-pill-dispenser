# First milestone demonstration

## 1. Show the shared workspace
Open the repository and show the five contribution folders. Open the team guide
so reviewers can see responsibilities and coordination.

## 2. Show firmware tests and terminal behaviour
In Codespaces run python -m pytest -q, then python scripts/demo.py.

The automatic demonstration asserts:
- failed authentication causes no motor start;
- valid authentication plus fresh drop detection completes one dispense;
- offering the same occurrence again is rejected;
- a missed authentication window produces a missed event and mock SMS request;
- no drop confirmation produces ERROR without another motor attempt.

The terminal script uses virtual time and fake hardware. A passing run demonstrates
controller behaviour, not the actual ESP32, physical reliability or real messaging.

## 3. Show Wokwi
Follow firmware/README.md. Demonstrate one successful dose, one missed dose and
one missing-drop failure. Show the servo, reminder LEDs/buzzer and serial events.
Say explicitly that fingerprint and drop sensors are simulated by buttons.

## 4. Show each teammate's current contribution
Mechanical: editable CAD and how the mechanism should work.
Electronics: components, wiring, power and provisional/agreed pins.
App: working screens and whether data is mock.
Integration: service/replayed events and mock notification behaviour.

Do not present placeholder READMEs as completed work.

## 5. Explain what remains
Agree the real mechanism and components; implement actual sensor/motor/lock
drivers; connect the app transport; validate physical operation and notification
delivery. Use test pills or inert objects for prototype demonstrations.

No software history entry proves medication was swallowed.
