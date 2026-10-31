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

The snapshot includes applied local config, occurrence statuses, compartment statuses,
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
They are stored before transmission. The transport may send them repeatedly until the backend
acknowledges the same ID. Only then does the main task remove the outbox entry.
The backend accepts an identical replay once and rejects changed content using an existing ID.
History and mock notification records therefore remain idempotent.

The callback still prints all events for debugging. Parsing the console is not the network transport.

## Concurrency

PillDispenser.ino owns the main control loop. It reads inputs, ticks the FSM, reads the RTC while
idle, handles serial config commands, persists changes and handles network results.

HttpSync.h runs blocking HTTPClient calls in another FreeRTOS task.
The optional MqttSync.h uses a separate network task and queues as well; it is restricted to the
simulation profile and communicates through the integration MQTT bridge. MQTT delivery to a broker
is not a service receipt: only an application-level acknowledgement of the event ID clears the outbox.
FreeRTOS queues pass copied request/response strings.
The worker never touches JsonDocument objects shared with the controller, Preferences, or GPIO.
Only the main task dispatches AgileStateMachine callbacks.

The worker uses bounded requests/retries. An offline service does not pause the control loop.
An exhausted durable outbox or failed local storage locks new work instead of losing critical state.

## Application and service

The supplied PillPilot Next.js app uses a server-side adapter to the FastAPI/SQLite reference service.
The browser sends expected-revision schedule edits to Next.js; its server supplies the service token.
The service commits medication labels and the desired configuration together. Labels remain separate
from strict firmware config and map to stable schedule IDs. One database owns this data and history.
The dashboard polls actual service history and distinguishes desired and applied revisions.

The reference service supports one development bearer-token configuration.
Patient accounts, multiple production device credentials, real SMS delivery and deployment remain
integration-team work. The connected reference path is deliberately small and can be replaced by a
backend implementing the same contract; it is not a finished production service.

## Presentation setup

`scripts/present.py` prepares dependencies and opens separate app, API and MQTT bridge terminal windows.
The firmware runs on the ESP32 or in the existing Wokwi project; there is no additional device
simulator. Each new service presentation uses an ignored session directory for SQLite and settings.
The bridge exchanges synthetic messages through a public broker reachable from browser Wokwi. A
generated session Wokwi package contains its random topic namespace; the canonical standalone
defaults are unchanged. The public broker is untrusted and cannot be used with real patient data.
See PRESENTATION.md for the three project roles and walkthrough.

The firmware can operate on its local persisted schedule without the app/service. The reference
service is needed for companion-app schedule synchronization and history. Browser Wokwi needs a
reachable endpoint rather than the laptop's localhost; saving an app schedule alone does not mean
the ESP32 has applied it.

## What validation can establish

Native C++ tests use the actual controller and community FSM/JSON libraries.
The HTTP replay demonstration uses actual emitted C++ events and a real loopback HTTP service.
ESP32 compilation checks board APIs and dependency compatibility.
The generated single-file sketch is compiled separately.

Those checks do not execute ESP32 Wi-Fi/FreeRTOS, animate Wokwi, read a real fingerprint,
move a physical carousel, or establish the meaning/reliability of a real passage sensor.
