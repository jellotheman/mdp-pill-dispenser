# Thermo Nuclear code quality review

Reviewed the companion integration on 31 October 2026 using the requested
`thermo-nuclear-code-quality-review` skill. Findings below were fixed in the working branch.
The review focused on `app/`, its shared service boundary in `integration/`, and preservation
of the firmware's existing responsibilities. It did not treat the reference service as a
finished production backend.

## Intended design

The project aims to combine scheduled compartment release, matching-user authorization
within a time window, local alerts and eventual caregiver notifications. The current
Arduino/C++ controller owns scheduling eligibility, authorization, inventory, persistent
attempts and fault handling. The companion edits desired schedules and displays history.
The integration service connects those parts through versioned configuration and
acknowledged events.

The supplied Next.js app's familiar visual design is retained. Its former memory store,
preview-only pause operation and browser-created dose outcomes have been removed. One
SQLite database now owns labels, configuration, acknowledgements, history and mock
notifications. Medication labels remain outside the strict firmware payload.

The user's companion-app references were background context, not instructions to replace
the supplied app or introduce Flutter, Firebase, remote dispensing or caregiver accounts:
[Smart Medical Management System](https://github.com/Dhaksin-Kaarthick/Smart-Medical-Management-System),
[Pilldispenser](https://github.com/Shaztech/Pilldispenser), and
[Automatic Supplement Pill Dispenser](https://github.com/Willykengineering/Automatic-Supplement-Pill-Dispenser).

## Findings and fixes

1. **Overlapping polling could starve every successful response.** The original integration
   started a request every three seconds and discarded any response superseded by a later
   request. A consistently slower service could therefore leave the dashboard disconnected
   indefinitely. Reads are now single-flight, and the next poll is scheduled after the
   preceding read finishes. Obsolete reads are aborted when an edit begins or the component
   unmounts.

2. **Connection and edit feedback had conflicting ownership.** Successful background polls
   erased failed-edit feedback, and edit controls could become available before the new
   configuration revision had been fetched. The hook now has explicit connection and edit
   states. Polling updates connection state, while edit feedback survives polls. The edit
   stays locked through its follow-up read. A confirmed write followed by a failed read is
   still reported as saved, so the form does not invite an unnecessary retry.

3. **Same-origin writes used the wrong hostname boundary.** Next.js can normalize an internal
   request URL to `localhost` even when the browser uses `127.0.0.1`. Comparing browser Origin
   with that internal URL rejected legitimate schedule edits. A small origin policy now
   compares the public Host and request protocol, normalizes default ports, rejects malformed
   origins, and does not trust arbitrary forwarded-host headers. Six Node-native regression
   tests cover the policy without adding a test framework.

4. **A lost save response could create another logical schedule on retry.** The form
   previously generated a new schedule ID on every submit. It now retains the draft ID until
   a confirmed save, and replaces that same record if polling already recovered a committed
   edit. This keeps schedule identity stable across an ambiguous response failure.

5. **The browser/service contract accepted silent shape changes.** Schedule request objects
   now reject extra fields, and the proxy validates successful configuration-write responses
   as well as dashboard reads. The device response schema is derived from the existing
   schedule schema with its app-only label removed, rather than maintaining another field list.

6. **Atomic metadata/config writes needed failure evidence.** The service already commits
   both writes in one transaction. A new regression injects failure at label storage after
   configuration writing and verifies rollback of both revision and metadata. Existing tests
   also cover stale edits, persistent pause state, unsupported fields and strict device config.

## Structural assessment

The final ownership boundaries are small and direct: page composition, three panel components,
one dashboard hook, a typed contract, an origin policy and one authenticated server-side proxy.
The integration service has one shared configuration-write function for app and device routes.
No production source file crosses 1,000 lines, and no custom scheduling engine, JSON parser,
event transport or second application database was introduced into the app.

The optional native presentation simulator was reviewed as additional orchestration, but the
user prefers their existing Wokwi firmware demonstration. It should not be required to run
or understand the companion. The app's empty history guidance now refers directly to Wokwi.
The firmware remains independent of the app, while the integration service connects them.

## Checks performed by the reviewer

- `npm test`: six origin-policy regressions passed.
- `npm run typecheck`: passed.
- `npm run lint`: passed with no warnings.
- Python companion/reference-service checks: 29 passed, including injected transaction failure.
- `npm audit --omit=dev`: zero production dependency findings at review time.

The parent agent performs the final production rebuild, real-browser edit/history checks and
presentation startup after these fixes. Those outcomes belong in `VALIDATION.md` once observed.

## Remaining limits

The complete npm audit still reports 14 moderate findings in the legacy ESLint/minimatch
development-tool dependency chain. Production dependencies are clean. No unsafe global
minimatch major-version override or forced package downgrade was applied merely to suppress
the audit; the legacy linter should be migrated with its supported plugin versions separately.

Wokwi connectivity must be demonstrated against an endpoint it can reach; compilation alone
does not establish a connected run. Real fingerprint enrollment, physical mechanism and
lock reliability, refill/recovery, production accounts/provisioning and real SMS delivery
remain team work. The abstract's proposed benefits are goals, not clinical validation of
this software prototype. No remaining structural blocker was identified for this scoped
companion/reference-service integration after the fixes above.
