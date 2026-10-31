# Communication and integration — reference service

A small FastAPI/SQLite backend connects the PillPilot app and the Arduino/C++ device contract.
The app's old memory store has been removed. Medication labels, schedules, device application
acknowledgements, history and mock notifications use this one database.

For a prepared local demonstration, start with `present.cmd` from the project root;
see [the presentation guide](../docs/PRESENTATION.md). The launcher opens separate local
terminals for this service and the dashboard. The existing Wokwi project runs the firmware.

This is a working seam for the integration teammate to expand, not a finished account,
deployment or SMS system. The canonical routes and ownership boundaries are in
[INTERFACE.md](INTERFACE.md). FastAPI serves the live OpenAPI schema at `/openapi.json` and `/docs`.

## Start locally

From the repository root:

~~~sh
python -m pip install -r requirements-dev.txt
~~~

Set a development token, then start the service.

Windows PowerShell:

~~~powershell
$env:MDP_DEVICE_TOKEN = "choose-a-local-demo-token"
python -m uvicorn integration.service:create_app --factory --host 127.0.0.1 --port 8000
~~~

Linux/macOS:

~~~sh
export MDP_DEVICE_TOKEN='choose-a-local-demo-token'
python -m uvicorn integration.service:create_app --factory --host 127.0.0.1 --port 8000
~~~

Open http://127.0.0.1:8000/docs for the interactive API documentation.
All device/app endpoints require the Authorization header documented in INTERFACE.md.
The default SQLite file is output/integration.sqlite3. Set MDP_DB to choose another path.
Use one worker for this small development setup.

To connect a physical ESP32 over the LAN, bind to 0.0.0.0 and use the computer's LAN address.
Keep the service token configured on both ends.
An internet-hosted/Wokwi test requires a reachable endpoint and appropriate HTTPS configuration.
A service on localhost is not automatically reachable from browser Wokwi.

## Demonstrate without hardware

~~~sh
python scripts/check_native.py --events
python scripts/http_demo.py
~~~

The first command executes the actual C++ controller and saves its critical events.
The second starts a temporary backend, uses real loopback HTTP to save/fetch config,
sends an explicitly simulated applied acknowledgement, replays those C++ events twice,
and checks that history contains one outcome.

This proves the API/replay path. It does not execute the sketch's ESP32 HTTP task.
Use the Wokwi/physical network configuration in firmware/README.md to check that separate path.

## Responsibilities now

- Maintain the connected app's saved/applied status and controller history.
- Preserve atomic label/config edits, expected-revision conflicts and event idempotency.
- Extend metadata through stable schedule IDs without adding fields to firmware config.
- Test the ESP32/Wokwi Wi-Fi path against a reachable endpoint. The native C++ tests
  exercise controller behavior; they do not execute ESP32 networking.
- Add real SMS delivery, provider IDs, failure handling and deduplication.
- Decide device provisioning and deployment after the existing app is inspected.

Notifications currently say simulated and never contact a provider.
The API is a development reference with one shared bearer token, not a completed account system.

## Uploading changes

Keep service code, dependencies, startup instructions and .env.example placeholders here.
Never commit real tokens. Use a branch/PR for changes to shared contract fields.
