# Communication and integration — reference service

A small FastAPI/SQLite backend connects the PillPilot app and the Arduino/C++ device contract.
The app's old memory store has been removed. Medication labels, schedules, device application
acknowledgements, history and mock notifications use this one database.

For a prepared local demonstration, start with `present.cmd` from the project root;
see [the presentation guide](../docs/PRESENTATION.md). The launcher opens separate local
terminals for this service and the dashboard. The existing Wokwi project runs the firmware.
The default launcher also opens an MQTT bridge and generates a session-specific Wokwi package.
Stop and close test terminals before restarting or finishing tests; leave only the final APP,
API and BRIDGE windows running for presentation.

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

## MQTT bridge for a synthetic demonstration

The reference HTTP API remains the source of truth. A separate bridge translates its desired
configuration, device acknowledgements and events to MQTT; the service does not send timed
dispense commands. With the API token set in `MDP_DEVICE_TOKEN`, run:

```powershell
python -m integration.mqtt_bridge --api http://127.0.0.1:8000 --device mdp-demo --namespace UNIQUE_DEMO --broker broker.hivemq.com --port 1883
```

Use a fresh 1–32 character namespace of letters, digits, underscores or hyphens. Topics are
`mdp-demo/<namespace>/<device>/{config,config-ack,events,event-ack}`. The bridge publishes the
strict device configuration without app-only medication labels and retains it at QoS 1. Firmware
publishes at QoS 0 with retries; it keeps events until the bridge acknowledges the specific event
after the API accepts it. Identical replays are deduplicated by the service. Firmware still owns
local RTC scheduling, authorization and mechanism decisions.

The shared public broker is untrusted and unencrypted on port 1883. Anyone can read or forge
messages; a namespace is not authorization. Use only synthetic data in a disposable simulation,
never real patient or medication information. For further development the bridge supports `--tls`
with the system trust store and optional `MDP_MQTT_USERNAME`/`MDP_MQTT_PASSWORD`; a production
design also needs provisioned identities, broker ACLs, reliable operation and thorough testing.
The current firmware MQTT client uses plaintext and is simulation-only even if the bridge uses TLS;
it is not an implementation of a secure physical-device connection.
The browser Wokwi public gateway reaches public services, not the laptop's localhost. The
[Wokwi private gateway](https://docs.wokwi.com/guides/esp32-wifi) can reach a local broker or API
but its web gateway is a paid feature. MQTT itself does not make a local server public.
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
- Expand device provisioning and deployment around the now-integrated app and shared contract.

Notifications currently say simulated and never contact a provider.
The API is a development reference with one shared bearer token, not a completed account system.

## Uploading changes

Keep service code, dependencies, startup instructions and .env.example placeholders here.
Never commit real tokens. Use a branch/PR for changes to shared contract fields.
