# Questions to settle before a physical driver

The simulation's six slots and one item per slot are provisional implementation assumptions.
They are not an agreed team design or an instruction to purchase a motor.

Mechanical, electronics and firmware members should fill in this table together.

| Question | Needed detail | Status |
| --- | --- | --- |
| What is stored? | Complete preloaded dose per slot, one pill per slot, or bulk supply? | pending |
| How does a dose leave? | Sequence of movements; which movement can release another item? | pending |
| How is a compartment selected? | Slot numbering, direction, steps/angles, gear ratio and reference position | pending |
| How is home found? | Limit/Hall/optical sensor, signal polarity and timeout; or no homing required | pending |
| How is movement proved? | Encoder/limit feedback, or clearly stated open-loop limitations | pending |
| What is the passage sensor? | Exact module, placement, polarity, expected pulse width and sample traces | pending |
| What constitutes success? | Observable evidence and what the sensor cannot establish | pending |
| What happens on a jam? | Stop/close behavior, safe state, isolation and manual inspection | pending |
| How is refill recorded? | Who loads which slot, how contents are associated with schedules, stock confirmation | pending |
| What follows interrupted power? | Physical position uncertainty and inspection/reconciliation procedure | pending |
| What is the lock? | Physical access/actuator arrangement and how its state is known | pending |
| Which fingerprint module? | Matching/enrolment protocol and mapping template IDs to authorized users | pending |
| Which electrical interfaces? | Exact board, supply, drivers, logic levels, GPIO and connectors | pending |

## Firmware handoff from hardware teammates

Supply a drawing or short video of one complete release, an exact component list,
the movement/sensor sequence and rough timing limits. Editable CAD and an annotated wiring diagram
are more useful than screenshots alone.

A physical Mechanism implements:
- ready(): the device has a configured, reviewed driver and required sensors.
- home(now): begin establishing a known position.
- select(compartment, now): begin positioning the requested compartment.
- release(dose, now): begin the intended release, with the full Dose available.
- finished(now): report this operation's completion promptly; do not block.
- sensorClear(): inspect the passage sensor before release.
- stop(): place the actuator in the agreed safe condition.

The current interface returns success/failure for starting an operation and completion by polling.
Add richer fault/position feedback if the actual mechanism requires it.
Do not equate a motor command, elapsed time or an emitted event with observed physical motion.

## Sensor driver

The Wokwi pushbutton is deliberately not the real pill detector.
A physical beam sensor may generate pulses shorter than the main loop interval.
Measure the signal, then use an appropriate interrupt/input-capture buffer and filtering.
Discard events from before the valid release interval.
The simulation counts one passage and faults on a second observed passage during its active interval.
Its fixed timing and settling values are not physical calibration.

## Unsupported designs

Bulk feeding and arbitrary pill quantities are not implemented.
A compartment containing multiple loose pills might produce one or several sensor pulses.
The team must define what those pulses mean before calling the outcome dispensed.
A physical refill, fault-clear and enrolment workflow are also still required.
