# Communication and integration

This folder is reserved for the integration member. The firmware emits JSON
events; it does not yet send them over Wi-Fi or call a live backend.

Read [the team guide](../docs/TEAM_GUIDE.md) and [INTERFACE.md](INTERFACE.md).

## First milestone
- Implement a small backend/service using an appropriate community framework
  such as FastAPI if choosing Python.
- Accept schedules from the app and store dispensing-history entries.
- Replay the sample JSONL events into your service to demonstrate the contract.
- Print mock SMS requests; do not claim real messages were delivered.
- Document the exact setup/start command and provide example requests.

Choose the framework with the app member. A local SQLite database is enough for
the initial prototype if you need persistence. No cloud deployment is required.

Get sample events by running python scripts/demo.py from the repository root.
The generated output/demo-events.jsonl is ignored by Git. CI uploads it as an
artifact if its test/demo run completes.

## Coordinate before connecting the real device
Decide with Sreeram whether to use serial, HTTP or MQTT, how to sync schedules and
how to identify duplicate/replayed events. The current controller has only one
demo compartment. Do not add remote dispense commands that bypass its local
authorization and due-dose checks.

## Upload
Put your service source, dependency file, example replay client and setup README
here. Include .env.example with placeholders if needed; never upload actual keys.
Update INTERFACE.md through a branch/PR when changing agreed fields.
