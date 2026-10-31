"""Run: python scripts/demo.py [--interactive]. No electronics required."""
import argparse
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "firmware"))
from main import Controller, Journal, AUTH_WINDOW_MS, STATUS_HOLD_MS, VERIFY_TIMEOUT_MS


class FakeMotor:
    def __init__(self):
        self.starts = 0
        self.start_time = None

    def start(self, now):
        self.starts += 1
        self.start_time = now

    def finished(self, now):
        return self.start_time is not None and now - self.start_time >= 700

    def stop(self):
        pass


def automatic(folder):
    """Three scenarios in virtual time; no sleeps or changing your computer clock."""
    events = []
    def emit(event):
        events.append(event)
        print(json.dumps(event))
    controller = Controller(FakeMotor(), Journal(str(folder / "journal.json")), emit)
    dose = lambda name: {"dose_id": name, "schedule_id": name, "compartment": 1}
    controller.offer(dose("demo-success"), 0)
    controller.authenticate(False, 100)
    assert controller.motor.starts == 0
    controller.authenticate(True, 200)
    controller.pill_detected(400)
    controller.tick(900)
    assert controller.state == "COMPLETED"
    controller.tick(900 + STATUS_HOLD_MS)
    assert not controller.offer(dose("demo-success"), 3000)
    controller.offer(dose("demo-missed"), 4000)
    controller.tick(4000 + AUTH_WINDOW_MS)
    assert controller.state == "MISSED"
    controller.tick(4000 + AUTH_WINDOW_MS + STATUS_HOLD_MS)
    controller.offer(dose("demo-no-drop"), 30000)
    controller.authenticate(True, 30100)
    controller.tick(30800)
    controller.tick(30800 + VERIFY_TIMEOUT_MS)
    assert controller.state == "ERROR"
    output = Path("output")
    output.mkdir(exist_ok=True)
    with open(output / "demo-events.jsonl", "w") as target:
        for event in events:
            target.write(json.dumps(event) + "\n")
    print("PASS: success, rejected fingerprint, duplicate, missed dose, missing pill.")
    print("Events: " + str(output / "demo-events.jsonl"))


def interactive(folder):
    controller = Controller(FakeMotor(), Journal(str(folder / "journal.json")),
                            lambda event: print(json.dumps(event)))
    now = 0
    counter = 0
    print("Virtual clock: no real waiting. Commands: due, valid, invalid, drop,")
    print("advance MILLISECONDS, status, quit. ERROR stays locked; restart for fresh demo.")
    while True:
        command = input("dispenser> ").strip().lower()
        if command == "quit":
            return
        if command == "due":
            counter += 1
            controller.offer({"dose_id": "manual-%d" % counter,
                              "schedule_id": "manual", "compartment": 1}, now)
        elif command in ("valid", "invalid"):
            controller.authenticate(command == "valid", now)
        elif command == "drop":
            controller.pill_detected(now)
        elif command.startswith("advance "):
            try:
                step = int(command.split()[1])
                if step < 0:
                    raise ValueError
                now += step
            except (ValueError, IndexError):
                print("Use advance 1000, with a nonnegative integer.")
        elif command != "status":
            print("Unknown command.")
        controller.tick(now)
        print("time=%dms state=%s motor_starts=%d" %
              (now, controller.state, controller.motor.starts))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interactive", action="store_true")
    args = parser.parse_args()
    # Keeps repeated teaching demos independent; no real device journal is erased.
    with tempfile.TemporaryDirectory(prefix="mdp-demo-") as location:
        folder = Path(location)
        if args.interactive:
            interactive(folder)
        else:
            automatic(folder)
