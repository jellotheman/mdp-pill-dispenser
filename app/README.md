# Companion app

The existing application is ready for source upload but has not yet been inspected.
Put source, dependency manifests and exact setup/start instructions here.
Keep node_modules, build caches, credentials and private data outside Git.

Read docs/TEAM_GUIDE.md for beginner upload/branch instructions.
Read integration/INTERFACE.md for schema version 2.
The reference backend is integration/service.py; reuse the existing app's backend if appropriate
instead of creating a second incompatible data store.

## Integration checklist after upload

- Identify framework, existing backend, data models, routes and current mock data.
- Preserve useful UI; adapt its service/data layer based on actual source.
- Map medication names/instructions to stable device schedule IDs.
- Send expected_revision when saving changes and handle 409 edit conflicts.
- Distinguish saved desired revision from applied device revision.
- Fetch actual dispensed/missed/error history.
- Display queued/delivered SMS truthfully once real delivery exists.
- Do not expose a control that bypasses local due-dose and matching-user checks.
- Do not call a dispensed event proof of ingestion.

The device currently supports daily Asia/Kolkata schedules and six simulated preloaded-item slots.
Bulk quantities, recurrence by weekday, arbitrary timezones and physical refill need explicit decisions.
