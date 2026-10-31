# Draft shared interface

This is a starting agreement for app, integration and firmware. It describes
data, not an implemented network API. Confirm changes together.

## Schedule

```json
{"id":"morning","time":"08:00","compartment":1,"enabled":true}
```

- id: unique, nonempty schedule id, retained when editing its time.
- time: daily local HH:MM, 24-hour format.
- compartment: 1 in the current simulation. More compartments need the real
  indexing mechanism and a coordinated firmware change.
- enabled: boolean.
- Local time zone for deployment is India (Asia/Kolkata). The physical RTC must
  be deliberately set to local time; it cannot infer a time zone.
- The controller's date-qualified occurrence id is separate from the schedule id,
  e.g. 2026-10-31:morning. This prototype supports one occurrence per schedule per
  date. Do not reuse an id for an additional dose on that date.

The firmware currently reads SCHEDULES in main.py. Network schedule upload,
validation acknowledgement and persistence are future integration work.

## Device event (one JSON object per serial line)

```json
{"schema_version":1,"event":"dispensed","state":"COMPLETED","elapsed_ms":800,
 "dose_id":"2026-10-31:morning","schedule_id":"morning","compartment":1,
 "reason":"drop_detected"}
```

The short timer demonstration uses demo-1, demo-2 and demo-3 instead of dated ids.

Events include dose_due, reminder, authentication_failed, authorized,
motor_started, verifying, pill_detected, dispensed, missed, error and sms_requested.

- elapsed_ms is accumulated time since boot, not a calendar timestamp.
- Some startup errors have dose_id null and no schedule_id/compartment.
- Human-readable startup lines are also printed. An integration reader should
  parse lines beginning with a JSON object and skip other text.
- sms_requested has simulated=true. It means a mock notification request, not
  proof of delivery.
- dispensed means the simulated drop was detected after an authorized attempt.
  It does not mean the medicine was taken.
- error is latched; it does not request another dispense attempt.

The service should add received_at in an explicit time zone and identify the
device/session when real transport is introduced. Duplicate handling for history,
replayed reminder events, ordering and real SMS delivery must be agreed at that
stage. Do not turn each replayed notification event into another real SMS.

## Suggested service operations, to be agreed

The backend may expose schedule listing/updating and history listing to the app,
plus an event-ingestion operation for the device/replay script. These are proposed
responsibilities, not working endpoints in the repository yet.

Do not expose a bypass that operates the motor directly from the app.
