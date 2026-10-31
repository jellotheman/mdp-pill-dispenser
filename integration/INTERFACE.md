# App/device contract — version 2

Implemented by the Arduino firmware and reference service.
This supersedes the original draft version-1 serial-only format.
The PillPilot Next.js companion in app/ now uses this service through a server-side proxy.

## Conventions

- API prefix: /api/v1/devices/{device_id}. API route version and event schema version are different.
- Identifiers: 1–32 ASCII letters/numbers, hyphen or underscore.
- Development service authentication: Authorization: Bearer TOKEN.
- No remote command directly operates the mechanism or impersonates a fingerprint.
- Device profile currently supports six compartments, each containing one preloaded item.
- This contract does not represent bulk pill counting, arbitrary quantities, weekdays or multiple timezones.

## Save and synchronize schedules

### Companion metadata

The browser uses GET/PUT `/api/dashboard` on the Next.js server. That server keeps the bearer
token private and forwards to GET/PUT `/api/v1/devices/{device_id}/companion` here.
The companion PUT accepts `expected_revision`, `timezone` and `schedules`, with the same
device schedule fields below plus `medication` (a nonblank label, at most 80 characters).
Labels and the new device configuration commit in one SQLite transaction. Stale revisions
return 409 without changing either. The PUT returns the strict device config below.

The companion GET returns `device_id`, `revision`, `timezone`, labelled `schedules`,
`status` (the same object as /status), newest-first outcome `events` (the same records as
/history), and mock `notifications`. This is a consistent snapshot from the shared database.
If a schedule was created directly through /config, its ID is used as its label until the
app saves a label. Editing config through /config retains existing labels by schedule ID.

Medication labels never enter the firmware payload. The firmware GET /config and all
event/acknowledgement routes remain unchanged. The original prototype's /api/schedules and
/api/events endpoints are superseded; the browser cannot fabricate dose outcomes.

### Device configuration

App:
PUT /api/v1/devices/mdp-demo/config

~~~json
{"expected_revision":0,"timezone":"Asia/Kolkata","schedules":[{"id":"morning","time":"08:00","compartment":1,"enabled":true,"auth_user_id":1}]}
~~~

The service returns a new config:

~~~json
{"revision":1,"timezone":"Asia/Kolkata","schedules":[{"id":"morning","time":"08:00","compartment":1,"enabled":true,"auth_user_id":1}]}
~~~

A conflicting expected_revision returns 409. Fetch the current config before resolving the edit.
Fields are explicit and extra fields are rejected; do not silently drop medication data from the app.
App-only names/instructions may remain in the app/backend and map to stable schedule IDs.

Device:
GET /api/v1/devices/mdp-demo/config

The device validates the schema and revision. It persists a new config while IDLE.
A busy device defers it. An older revision or changed content under the same revision is rejected.
Same revision and same content is idempotent.
A config cannot unlock an ERROR device.

Device:
POST /api/v1/devices/mdp-demo/config-acks

~~~json
{"revision":1,"status":"applied","reason":"applied"}
~~~

Other statuses are deferred and rejected. The service accepts only known revisions.
GET /api/v1/devices/mdp-demo/status returns desired_revision, applied_revision and synchronized.
The app must distinguish saved-to-service from applied-to-device.

The firmware retains its applied config during network loss.
Changing configuration does not refill a physical slot or reset occurrence history.

## Dose identity and ownership

schedule ID: morning
occurrence ID: 2026-10-31:morning
compartment: 1
auth_user_id: 1

The occurrence ID stays the same for that schedule/date after configuration edits.
Use a distinct schedule ID for a genuinely separate daily occurrence.
The template/user ID is the sensor's matching identity, not a fingerprint template or image.
Do not send biometric templates through this API.

## Critical events and acknowledgements

Device:
POST /api/v1/devices/mdp-demo/events

~~~json
{"schema_version":2,"event_id":"mdp-demo:0123456789abcdef:7","device_id":"mdp-demo","session_id":"0123456789abcdef","event":"dispensed","state":"COMPLETED","elapsed_ms":6000,"occurred_at":null,"dose_id":"2026-10-31:morning","schedule_id":"morning","compartment":1,"revision":1,"reason":"one_passage_observed","observed_count":1,"simulated":true}
~~~

Response:

~~~json
{"accepted":true,"duplicate":false,"event_id":"mdp-demo:0123456789abcdef:7"}
~~~

An identical replay receives accepted=true and duplicate=true without another record.
Reusing an event ID with different content returns 409.
The firmware removes a pending event only after receiving the same acknowledged ID.

Durable events: dose_due, authorized, dispensed, missed, error.
Serial-only diagnostics: reminders, rejected matching, stage progress and simulated passages.
The service deliberately accepts the durable subset. Do not post arbitrary console lines.

elapsed_ms is monotonic time since this boot, not a wall-clock timestamp.
occurred_at is null until trusted device calendar timestamp support is implemented.
The backend adds received_at in UTC; delayed upload time must not be presented as the original dose time.
A startup error can have null dose_id/schedule_id and compartment 0.

The authorized event is committed before movement and may have WAITING_FOR_FINGERPRINT state:
it records the accepted authorization, immediately before entering HOMING.

## History and notifications

GET /api/v1/devices/mdp-demo/history returns dispensed, missed and error events plus received_at.
GET /api/v1/devices/mdp-demo/notifications returns mock SMS records for missed/error events.

A simulated passage is evidence only of the simulated condition.
A physical passage would still not establish pill identity or medication ingestion.
Do not rename dispensed to taken in the app.

The reference service records one mock notification per missed/error event.
It does not contact an SMS provider and does not claim delivery.
The integration teammate should retain idempotency when adding a real provider.

## Serial configuration diagnostic

The sketch also accepts one serial line:

~~~json
{"command":"apply_config","config":{"revision":1,"timezone":"Asia/Kolkata","schedules":[]}}
~~~

It returns config_result. This is a local diagnostic and does not replace network synchronization.
Unknown commands cannot operate the motor, authorize a patient or clear a physical fault.
