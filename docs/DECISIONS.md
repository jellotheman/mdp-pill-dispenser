# Shared project decisions

## Agreed software direction

- Five contribution folders remain: firmware, mechanical, electronics, app, integration.
- Firmware now uses Arduino/C++, following Sreeram's preference for simpler Wokwi/library setup.
- main is the default/current Arduino branch. The original Python prototype is preserved on legacy/micropython.
- The repository remains private.
- Use community libraries through package managers, with pinned firmware versions.
- The app already exists but has not been uploaded; inspect it before adapting UI/backend integration.
- Firmware and integration share schema version 2.
- HTTP is implemented as the initial device transport; the existing app/backend may replace the reference service.
- Real SMS delivery remains an integration task. The reference service records deduplicated mock notifications.
- A stored interrupted attempt requires inspection; no automatic release retry.

## Provisional simulation choices, not team-approved physical construction

- Six virtual compartments, one preloaded item each.
- Timed virtual homing and indexing; one servo visualizes release.
- Buttons simulate user matching and passage detection.
- The simulated user is template/user ID 1.
- Used compartments remain spent. Simulation reset is an explicit local command.
- Asia/Kolkata local daily schedules, fixed timezone, two-minute daily approval window.
- Physical mode deliberately refuses operation until a real mechanism is implemented.

## Team decisions still needed

| Decision | Members |
| --- | --- |
| Preloaded versus bulk dispensing; actual number of compartments | mechanical + electronics + firmware |
| Motor, driver, homing, position feedback, release and stop sequence | mechanical + electronics + firmware |
| Passage sensor, placement, pulse characteristics and success criteria | mechanical + electronics + firmware |
| Fingerprint reader, template ownership and enrolment | electronics + firmware |
| Physical lock, power, RTC and reviewed wiring | mechanical + electronics + firmware |
| Physical refill, fault recovery and long-term storage policy | mechanical + electronics + firmware |
| Existing app architecture, backend reuse and API adapter | app + integration + firmware |
| Development endpoint, HTTPS CA/time provisioning and device credentials | integration + firmware |
| Real SMS provider/module and delivery tracking | integration + electronics |

Record the actual decision, who agreed it, and when.
Use MECHANISM_BRIEF.md as the physical design handoff.
