# Firmware and integration architecture

## Device responsibilities

The controller owns scheduling eligibility, matching-user authorization, single-attempt policy,
stage deadlines and local occurrence state. It receives a Dose with occurrence ID, schedule ID,
compartment, authorized user ID and configuration revision.

AgileStateMachine owns permitted transitions and entry callbacks:

IDLE → WAITING_FOR_FINGERPRINT → HOMING → POSITIONING → RELEASING → VERIFYING → COMPLETED → IDLE

An expired occurrence becomes MISSED → IDLE. A fault leads to latched ERROR.

The mechanism owns how homing, selecting, releasing and detecting completion actually work.
Its methods return promptly; finished() is polled. A physical mechanism may implement home/select as
immediate no-ops if its construction does not require them. A bulk pill-counting mechanism may need
a different contract/workflow and is not represented by the current preloaded-item simulation.

## Persistence and inventory

Store commits one versioned JSON snapshot through a Persistence adapter.
On ESP32, Preferences writes that snapshot to one NVS key and reads it back for verification.
The native tests use an in-memory persistence port with failures injected.

The snapshot includes desired/applied local config, occurrence statuses, compartment statuses,
a latched fault and pending critical events. Before the first movement, the attempt and authorized
event are persisted together and the selected compartment is quarantined.
On successful verification the compartment becomes spent.
A missed authentication window leaves it loaded.
An interrupted attempt or fault requires inspection; it is never automatically retried.

There is no physical refill/recovery implementation yet. Simulation erase-demo is an explicit,
local convenience for disposable state only. A fresh physical profile starts with unknown inventory.

Snapshots are bounded to 12,000 serialized bytes; at most 24 pending critical events are allowed.
No old event is silently discarded to make room for another dose. Records are not automatically
pruned: long-term retention, flash wear and maintenance need physical-product design work.
Only critical events are queued durably; reminders and stage traces are serial diagnostics.

NVS/readback tests and software tests do not establish correctness under every flash/power fault.
NVS writes still have latency; measure that latency on the actual board.

## Configuration synchronization

1. The app saves a configuration using expected_revision.
2. The service increments the desired revision.
3. The ESP32 fetches it and checks the exact schema and supported capabilities.
4. While busy it returns deferred without changing the active dose.
5. While idle it persists the config, then acknowledges applied.
6. The app compares desired_revision and applied_revision.

Same revision/same content is idempotent. Reused revision/different content and older revisions are rejected.
An applied configuration acknowledgement does not mean a dose has been dispensed.
An error-state device cannot clear its fault by downloading another config.

## Event synchronization

Critical events have IDs composed of device, random boot session and sequence.
They are stored before transmission. The HTTP worker may send them repeatedly until the backend
acknowledges the same ID. Only then does the main task remove the outbox entry.
The backend accepts an identical replay once and rejects changed content using an existing ID.
History and mock notification records therefore remain idempotent.

The callback still prints all events for debugging. Parsing the console is not the network transport.

## Concurrency

PillDispenser.ino owns the main control loop. It reads inputs, ticks the FSM, reads the RTC while
idle, handles serial config commands, persists changes and handles network results.

HttpSync.h runs blocking HTTPClient calls in another FreeRTOS task.
FreeRTOS queues pass copied request/response strings.
The worker never touches JsonDocument objects shared with the controller, Preferences, or GPIO.
Only the main task dispatches AgileStateMachine callbacks.

The worker uses bounded requests/retries. An offline service does not pause the control loop.
An exhausted durable outbox or failed local storage locks new work instead of losing critical state.

## Application and service

The provided FastAPI/SQLite service is a reference implementation.
The existing app has not been supplied or inspected. Its backend may replace this service if it
implements the agreed contract. A fifth team role does not imply a second incompatible database.

The reference service supports one development bearer-token configuration.
Patient accounts, multiple production device credentials, real SMS delivery, deployment and
the existing app's UI are future integration work, not completed product features.

## What validation can establish

Native C++ tests use the actual controller and community FSM/JSON libraries.
The HTTP replay demonstration uses actual emitted C++ events and a real loopback HTTP service.
ESP32 compilation checks board APIs and dependency compatibility.
The generated single-file sketch is compiled separately.

Those checks do not execute ESP32 Wi-Fi/FreeRTOS, animate Wokwi, read a real fingerprint,
move a physical carousel, or establish the meaning/reliability of a real passage sensor.
