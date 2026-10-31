# MDP Smart Pill Dispenser

Shared workspace for a first-year, 2-credit multidisciplinary project.

**Start here:** [Team collaboration guide](docs/TEAM_GUIDE.md).
**Sreeram's part:** [Firmware and simulation guide](firmware/README.md).

## Where everyone's work goes

| Folder | Owner / work |
| --- | --- |
| firmware/ | Sreeram: ESP32 MicroPython code and Wokwi circuit |
| mechanical/ | Pill tray, mechanism, enclosure, CAD and assembly |
| electronics/ | Component list, wiring, power and pin map |
| app/ | Companion app for schedules and dispensing history |
| integration/ | App/device data exchange, history and SMS workflow |
| docs/ | Shared instructions, decisions and demonstration steps |
| tests/ | Firmware behaviour tests |

Other members' folders begin with instructions, not finished implementations.

## Work entirely in the browser

1. Open this repository on GitHub.
2. Choose **Code → Codespaces → Create codespace on main**.
3. Wait for setup to finish. Python and pytest are configured automatically.
4. In its terminal run:

```sh
python -m pytest -q
python scripts/demo.py
```

Use `python scripts/demo.py --interactive` to control a virtual dispenser yourself.

No local Python, Docker or ESP32 is needed for these commands. Codespaces uses
your GitHub account's allowance/billing; stop it when finished. The light
github.dev editor also works for edits/uploads but cannot run these commands.

For the actual animated ESP32 circuit, follow the Wokwi steps in
[firmware/README.md](firmware/README.md). Wokwi is a separate browser tab; it
does not automatically sync with this private repository.

## Implemented in the prototype

- Explicit FSM using the community pysm library.
- Due-dose scheduling; fingerprint success/failure supplied by simulation buttons.
- Reminder LEDs and buzzer, servo gate demonstration.
- Pill-drop confirmation, missed-dose and motor/verification timeout handling.
- Duplicate suppression using an occurrence journal and inspection-required
  restart after an interrupted dispensing attempt.
- JSON events for the integration teammate; SMS requests are mock events.
- Terminal demo, pytest scenarios, and a GitHub Actions test workflow.

This demonstrates **one compartment and one gate**. It does not yet index a
multi-compartment carousel. The fingerprint reader, real SMS delivery, physical
lock, network transport, app and finished mechanical hardware are not implemented.
All actuation is for simulation; real motor/power/RTC/fingerprint drivers must be
agreed and checked with the hardware members first.

Do not use this prototype to dispense real medication. A confirmed pill drop
does not prove someone took medication.

## Test status

The workflow runs tests on pushes affecting firmware and on manual runs from
**Actions → Firmware checks → Run workflow**. Read the latest run to see the
actual result. Inclusion of tests alone does not mean they have passed.

[Demonstration walkthrough](docs/DEMO.md) ·
[Shared data interface](integration/INTERFACE.md) ·
[Project decisions](docs/DECISIONS.md) ·
[References and library licences](THIRD_PARTY.md)
