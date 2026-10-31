"""Runs on the real MicroPython Unix interpreter in CI, with a fake motor."""
import sys
import os
sys.path.insert(0, "firmware")
from main import Controller, Journal, daily_candidates

class Motor:
    def __init__(self):
        self.starts = 0
        self.at = 0
    def start(self, now):
        self.starts += 1
        self.at = now
    def finished(self, now):
        return now - self.at >= 700
    def stop(self):
        pass

try:
    os.mkdir("output")
except OSError:
    pass
path = "output/micropython-journal.json"
motor, events = Motor(), []
c = Controller(motor, Journal(path), events.append)
dose = {"dose_id": "micropython:morning", "schedule_id": "morning", "compartment": 1}
assert c.state == "IDLE"
assert c.offer(dose, 0)
assert not c.authenticate(False, 10)
assert motor.starts == 0
assert c.authenticate(True, 100)
assert not c.authenticate(True, 200)
c.pill_detected(300)
c.tick(800)
assert c.state == "COMPLETED"
assert motor.starts == 1
c.tick(2800)
assert not c.offer(dose, 3000)
rebooted = Controller(Motor(), Journal(path), events.append)
assert not rebooted.offer(dose, 0)
assert daily_candidates(
    [{"id": "a", "time": "08:00", "compartment": 1}],
    (2026, 10, 31, 8, 0, 0))[0][1] == 120000
os.remove(path)
print("PASS: real MicroPython imports, pysm transitions, JSON journal, duplicate suppression and scheduler")
