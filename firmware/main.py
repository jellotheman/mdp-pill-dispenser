"""MDP dispenser prototype: shared Python logic + MicroPython/Wokwi adapter.

Edit settings below. Importing this file on CPython never touches GPIO.
Buttons represent fingerprint results and pill-drop detection, NOT real biometrics.
"""
try:
    import ujson as json
except ImportError:
    import json
import os
from pysm import State, StateMachine, Event

# Simulation only. Keep True until real drivers and mechanism are agreed.
DEMO_MODE = True
AUTH_WINDOW_MS = 20000
REMINDER_INTERVAL_MS = 5000
VERIFY_TIMEOUT_MS = 8000
MOTOR_TIMEOUT_MS = 3000
STATUS_HOLD_MS = 2000
SCHEDULES = [
    {"id": "morning", "time": "08:00", "compartment": 1, "enabled": True},
    {"id": "evening", "time": "20:00", "compartment": 1, "enabled": True},
]
DEMO_DOSES = [
    {"id": "demo-1", "at_ms": 5000, "compartment": 1},
    {"id": "demo-2", "at_ms": 35000, "compartment": 1},
    {"id": "demo-3", "at_ms": 65000, "compartment": 1},
]


def validate_schedules(rows):
    """Small agreed app format. Only compartment 1 has a demo actuator."""
    if not isinstance(rows, list):
        raise ValueError("schedules must be a list")
    ids = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("each schedule must be an object")
        sid = row.get("id")
        if not isinstance(sid, str) or not sid or sid in ids:
            raise ValueError("schedule ids must be unique nonempty strings")
        ids.append(sid)
        clock = row.get("time", "")
        try:
            hour, minute = [int(p) for p in clock.split(":")]
        except (ValueError, AttributeError):
            raise ValueError("time must be HH:MM")
        if len(clock) != 5 or clock[2] != ":" or not clock[:2].isdigit() or not clock[3:].isdigit() or not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError("time must be HH:MM")
        if row.get("compartment") != 1:
            raise ValueError("prototype supports compartment 1 only")
        if not isinstance(row.get("enabled", True), bool):
            raise ValueError("enabled must be boolean")


def daily_candidates(rows, date_time, window_ms=120000):
    """RTC local time tuple: year, month, day, hour, minute, second.
    Each occurrence has a date-qualified id. Expired doses become missed.
    No catch-up dispensing for previous dates.
    """
    validate_schedules(rows)
    y, mo, d, h, mi, s = date_time
    current_ms = (h * 3600 + mi * 60 + s) * 1000
    result = []
    for row in rows:
        if not row.get("enabled", True):
            continue
        hh, mm = [int(p) for p in row["time"].split(":")]
        due_ms = (hh * 3600 + mm * 60) * 1000
        if current_ms >= due_ms:
            result.append((
                {"dose_id": "%04d-%02d-%02d:%s" % (y, mo, d, row["id"]),
                 "schedule_id": row["id"], "compartment": row["compartment"]},
                window_ms - (current_ms - due_ms)))
    return result


class Journal:
    """Demo occurrence ledger. Write before moving; never silently reset errors.

    Temporary-file replacement helps with interrupted writes, but is not a
    medical-grade guarantee against arbitrary flash/power faults.
    """
    def __init__(self, path):
        self.path = path
        self.records = {}
        self.healthy = True
        try:
            with open(path) as source:
                value = json.load(source)
            allowed = ("started", "dispensed", "missed", "error")
            if not isinstance(value, dict) or any(
                not isinstance(k, str) or v not in allowed for k, v in value.items()
            ):
                raise ValueError("invalid journal")
            self.records = value
        except OSError as exc:
            # ENOENT alone means a fresh project. All other read failures lock it.
            if not exc.args or exc.args[0] != 2:
                self.healthy = False
        except (ValueError, TypeError):
            self.healthy = False
        # A leftover temporary write needs inspection, even when main file exists.
        try:
            os.stat(path + ".tmp")
            self.healthy = False
        except OSError as exc:
            if not exc.args or exc.args[0] != 2:
                self.healthy = False

    def put(self, dose_id, status):
        if not self.healthy:
            raise OSError("journal needs inspection")
        updated = dict(self.records)
        updated[dose_id] = status
        temporary = self.path + ".tmp"
        with open(temporary, "w") as target:
            json.dump(updated, target)
            target.flush()
        if hasattr(os, "sync"):
            os.sync()
        if hasattr(os, "replace"):
            os.replace(temporary, self.path)
        else:
            os.rename(temporary, self.path)
        if hasattr(os, "sync"):
            os.sync()
        self.records = updated


class Controller:
    """Nonblocking FSM. Times are accumulated monotonic milliseconds."""
    def __init__(self, motor, journal, emit=print):
        self.motor = motor
        self.journal = journal
        self.emit = emit
        self._setup_fsm()
        self.dose = None
        self.deadline = 0
        self.last_reminder = 0
        self.motor_started = 0
        self.verify_started = 0
        self.finished_at = 0
        self.drop_seen = False
        if not journal.healthy or "started" in journal.records.values() or "error" in journal.records.values():
            self._error("recovery_required", 0)

    def _setup_fsm(self):
        names = ("IDLE", "WAITING_FOR_FINGERPRINT", "DISPENSING", "VERIFYING",
                 "COMPLETED", "MISSED", "ERROR")
        states = {name: State(name) for name in names}
        self.fsm = StateMachine("dispenser")
        for name in names:
            self.fsm.add_state(states[name], initial=(name == "IDLE"))
        links = (
            ("IDLE", "WAITING_FOR_FINGERPRINT"), ("IDLE", "MISSED"),
            ("WAITING_FOR_FINGERPRINT", "DISPENSING"),
            ("WAITING_FOR_FINGERPRINT", "MISSED"),
            ("DISPENSING", "VERIFYING"), ("VERIFYING", "COMPLETED"),
            ("COMPLETED", "IDLE"), ("MISSED", "IDLE"),
        )
        for source, target in links:
            self.fsm.add_transition(states[source], states[target], ["to_" + target])
        for source in names:
            if source != "ERROR":
                self.fsm.add_transition(states[source], states["ERROR"], ["to_ERROR"])
        self.fsm.initialize()

    @property
    def state(self):
        return self.fsm.state.name

    def _transition(self, target):
        if target == self.state:
            return
        self.fsm.dispatch(Event("to_" + target))
        if self.state != target:
            raise RuntimeError("invalid transition to " + target)

    def _event(self, name, now, **extra):
        event = {"schema_version": 1, "event": name, "state": self.state,
                 "elapsed_ms": now, "dose_id": None}
        if self.dose is not None:
            event.update(self.dose)
        event.update(extra)
        self.emit(event)

    def _save(self, status, now):
        try:
            self.journal.put(self.dose["dose_id"], status)
            return True
        except Exception:
            self._error("storage_failed", now)
            return False

    def _error(self, reason, now):
        self._transition("ERROR")
        try:
            self.motor.stop()
        except Exception:
            pass
        self._event("error", now, reason=reason)
        self._event("sms_requested", now, reason=reason, simulated=True)

    def _finish(self, success, now, reason):
        status = "dispensed" if success else "missed"
        if not self._save(status, now):
            return
        self._transition("COMPLETED" if success else "MISSED")
        self.finished_at = now
        self._event(status, now, reason=reason)
        if not success:
            self._event("sms_requested", now, reason=reason, simulated=True)

    def _motor_error(self, reason, now):
        if self._save("error", now):
            self._error(reason, now)

    def offer(self, dose, now, remaining_ms=AUTH_WINDOW_MS):
        """Scheduler offers a due occurrence; busy/duplicate offers are ignored."""
        if self.state != "IDLE" or dose["dose_id"] in self.journal.records:
            return False
        if dose.get("compartment") != 1:
            raise ValueError("unsupported compartment")
        self.dose = dict(dose)
        self.drop_seen = False
        self.deadline = now + remaining_ms
        self.last_reminder = now
        if remaining_ms <= 0:
            self._finish(False, now, "schedule_expired")
        else:
            self._transition("WAITING_FOR_FINGERPRINT")
            self._event("dose_due", now, remaining_ms=remaining_ms)
            self._event("reminder", now)
        return True

    def authenticate(self, valid, now):
        self.tick(now)  # Deadline wins, including at the exact expiry instant.
        if self.state != "WAITING_FOR_FINGERPRINT":
            return False
        if not valid:
            self._event("authentication_failed", now)
            return False
        # Commit attempt BEFORE any actuator command, including across resets.
        if not self._save("started", now):
            return False
        self._transition("DISPENSING")
        self.motor_started = now
        self._event("authorized", now)
        try:
            self.motor.start(now)
        except Exception:
            self._motor_error("motor_start_failed", now)
            return False
        self._event("motor_started", now)
        return True

    def pill_detected(self, now):
        # Ignore stale/idle detections. Board adapter supplies fresh edges only.
        if self.state in ("DISPENSING", "VERIFYING"):
            self.drop_seen = True
            self._event("pill_detected", now)

    def tick(self, now):
        if self.state in ("COMPLETED", "MISSED"):
            if now - self.finished_at >= STATUS_HOLD_MS:
                self._transition("IDLE")
                self.dose = None
            return
        if self.state == "WAITING_FOR_FINGERPRINT":
            if now >= self.deadline:
                self._finish(False, now, "authentication_timeout")
            elif now - self.last_reminder >= REMINDER_INTERVAL_MS:
                self.last_reminder = now
                self._event("reminder", now)
        elif self.state == "DISPENSING":
            try:
                done = self.motor.finished(now)
            except Exception:
                self._motor_error("motor_failed", now)
                return
            if done:
                self._transition("VERIFYING")
                self.verify_started = now
                self._event("verifying", now)
            elif now - self.motor_started >= MOTOR_TIMEOUT_MS:
                self._motor_error("motor_timeout", now)
        if self.state == "VERIFYING":
            if self.drop_seen:
                self._finish(True, now, "drop_detected")
            elif now - self.verify_started >= VERIFY_TIMEOUT_MS:
                self._motor_error("drop_not_detected", now)


class DebouncedButton:
    def __init__(self, pin, now=0):
        self.pin = pin
        self.raw = pin.value()
        self.stable = self.raw
        self.changed_at = now

    def pressed(self, now):
        reading = self.pin.value()
        if reading != self.raw:
            self.raw = reading
            self.changed_at = now
        if reading != self.stable and now - self.changed_at >= 40:
            self.stable = reading
            return reading == 0
        return False


class ServoGate:
    """One demonstration gate. Replace this adapter for an indexed carousel."""
    def __init__(self, pwm):
        self.pwm = pwm
        self.started = None
        self.closed = True
        self.stop()

    def angle(self, degrees):
        pulse_us = 500 + degrees * 2000 // 180
        self.pwm.duty_u16(pulse_us * 65535 // 20000)

    def start(self, now):
        self.started = now
        self.closed = False
        self.angle(90)

    def finished(self, now):
        if self.started is not None and now - self.started >= 700:
            self.stop()
            return True
        return False

    def stop(self):
        self.angle(0)
        self.closed = True


def read_ds1307(i2c):
    """Read the simulation RTC; reject stopped clock, 12h mode and bad data."""
    data = i2c.readfrom_mem(0x68, 0, 7)
    if data[0] & 128 or data[2] & 64:
        raise ValueError("RTC stopped or not in 24-hour mode")
    def bcd(value):
        if (value & 15) > 9 or (value >> 4) > 9:
            raise ValueError("bad RTC BCD")
        return (value >> 4) * 10 + (value & 15)
    s, m, h = bcd(data[0]), bcd(data[1]), bcd(data[2])
    d, mo, y = bcd(data[4]), bcd(data[5]), 2000 + bcd(data[6])
    days = (31, 29 if y % 4 == 0 else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    if not (0 <= s <= 59 and 0 <= m <= 59 and 0 <= h <= 23 and
            1 <= mo <= 12 and 1 <= d <= days[mo - 1]):
        raise ValueError("invalid RTC date/time")
    return (y, mo, d, h, m, s)


def run_board():
    import time
    from machine import Pin, PWM, I2C
    motor = ServoGate(PWM(Pin(18), freq=50))
    red = Pin(26, Pin.OUT, value=0)
    green = Pin(27, Pin.OUT, value=0)
    buzzer = PWM(Pin(25), freq=1500, duty_u16=0)
    valid = DebouncedButton(Pin(19, Pin.IN, Pin.PULL_UP))
    invalid = DebouncedButton(Pin(23, Pin.IN, Pin.PULL_UP))
    drop = DebouncedButton(Pin(32, Pin.IN, Pin.PULL_UP))
    def emit(event):
        print(json.dumps(event))
    try:
        validate_schedules(SCHEDULES)
        journal = Journal("dose-journal.json")
        controller = Controller(motor, journal, emit)
        i2c = None if DEMO_MODE else I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
        print("SIMULATION ONLY: green=valid fingerprint, red=invalid, blue=pill drop")
        print("demo doses at 5s, 35s, 65s; approve then press blue; never means medicine taken")
        elapsed = 0
        previous = time.ticks_ms()
        last_clock = -1000
        candidates = []
        while True:
            current = time.ticks_ms()
            elapsed += time.ticks_diff(current, previous)
            previous = current
            controller.tick(elapsed)
            # Read all buttons every loop. A held input cannot authorize a later dose.
            good_edge = valid.pressed(elapsed)
            bad_edge = invalid.pressed(elapsed)
            drop_edge = drop.pressed(elapsed)
            if DEMO_MODE:
                candidates = [
                    ({"dose_id": row["id"], "schedule_id": row["id"], "compartment": 1},
                     AUTH_WINDOW_MS - (elapsed - row["at_ms"]))
                    for row in DEMO_DOSES if elapsed >= row["at_ms"]
                ]
            elif elapsed - last_clock >= 1000 and controller.state != "ERROR":
                # Re-read at most once/second. Never cache a shrinking auth window.
                last_clock = elapsed
                candidates = daily_candidates(SCHEDULES, read_ds1307(i2c))
            else:
                candidates = []
            for dose, remaining in candidates:
                if controller.offer(dose, elapsed, remaining):
                    break
            # Conflicting fingerprint signals are treated as failure.
            if bad_edge:
                controller.authenticate(False, elapsed)
            elif good_edge:
                controller.authenticate(True, elapsed)
            if drop_edge:
                controller.pill_detected(elapsed)
            waiting = controller.state == "WAITING_FOR_FINGERPRINT"
            pulse = waiting and elapsed % 1000 < 200
            red.value(1 if controller.state in ("ERROR", "MISSED") or pulse else 0)
            green.value(1 if controller.state == "COMPLETED" else 0)
            buzzer.duty_u16(8000 if pulse else 0)
            time.sleep_ms(20)
    finally:
        motor.stop()
        buzzer.duty_u16(0)
        red.value(0)
        green.value(0)


if __name__ == "__main__":
    run_board()
