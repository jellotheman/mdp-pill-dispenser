# PillPilot companion app

The supplied Next.js/React/TypeScript app now lives here. Its dark sidebar, mint accents,
typography and dashboard layout are preserved. The service/data layer now connects to
`integration/service.py`, which is shared with the firmware rather than maintaining a
second database.

From the project root, run `present.cmd` on Windows, or `python scripts/present.py`.
This prepares dependencies, builds the app, and opens the app and service in local terminals.
See [the presentation guide](../docs/PRESENTATION.md) for the walkthrough and Wokwi differences.

## Manual development

Use Node.js 20.9 or newer and npm. Copy `.env.example` to `.env.local` and set the backend
URL, device ID and token to match the reference service. These variables are server-only;
do not add a `NEXT_PUBLIC_` prefix. The launcher's session environment takes precedence.

```powershell
cd app
npm ci
npm run dev -- --hostname 127.0.0.1
```

Start the backend separately as described in [integration/README.md](../integration/README.md).
For a production build use `npm run build`, followed by `npm run start -- --hostname 127.0.0.1`.
Checks are `npm run typecheck` and `npm run lint`.

## Behavior and ownership

- Add schedules and persist enabled/paused state with `expected_revision` conflict detection.
- Daily India-time schedules map to stable IDs, compartments 1–6 and an authorized user ID.
- Medication labels are stored separately from the strict device config, in the same SQLite
  transaction and database. Names are never sent into firmware's exact-field config parser.
- Display saved and applied revisions separately. Applied is a stored acknowledgement,
  not a device-online signal.
- The read-only **Test integration API** panel checks the authenticated app-to-service request
  and contract. It does not establish that the firmware or MQTT bridge is connected.
- Poll controller outcome history and mock notification counts every three seconds.
  Timestamps are labelled as service receipt time; a dispensed report does not prove ingestion.
- Sidebar links navigate to the existing schedule, history and integration sections.
- Sensor inputs belong to Wokwi buttons or the future physical device. The original
  dashboard buttons that invented dispensed/missed events have been removed.

`components/` owns the schedule, history and device panels; `lib/use-dashboard.ts` owns
loading, polling and edits; `lib/contract.ts` validates the typed UI/service boundary;
`app/api/dashboard/route.ts` is the server-side authenticated proxy. Fonts are served
locally so the presentation does not depend on Google Fonts being reachable.

The original prototype API spec is retained as `reference/original-openapi.yaml` for
provenance only. It describes the superseded in-memory API, not the connected application.
The current browser API is in `openapi.yaml`; the authoritative device/service API is
[INTERFACE.md](../integration/INTERFACE.md) and the running service's `/docs`.

The local launcher binds to loopback. User accounts, caregiver access, production
provisioning, physical refill/recovery and real SMS delivery remain future team work.
