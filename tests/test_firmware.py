import json
from pathlib import Path

import pytest
from main import (Controller, Journal, ServoGate, DebouncedButton, daily_candidates,
                  read_ds1307, validate_schedules, AUTH_WINDOW_MS, STATUS_HOLD_MS,
                  VERIFY_TIMEOUT_MS, MOTOR_TIMEOUT_MS)


class Motor:
    def __init__(self, fail=False, stuck=False):
        self.starts = 0
        self.stops = 0
        self.began = 0
        self.fail = fail
        self.stuck = stuck

    def start(self, now):
        if self.fail:
            raise OSError("disconnected")
        self.starts += 1
        self.began = now

    def finished(self, now):
        return not self.stuck and now - self.began >= 700

    def stop(self):
        self.stops += 1


@pytest.fixture
def system(tmp_path):
    motor, events = Motor(), []
    controller = Controller(motor, Journal(str(tmp_path / "journal.json")), events.append)
    return controller, motor, events


def dose(name="today:morning"):
    return {"dose_id": name, "schedule_id": "morning", "compartment": 1}


def succeed(controller, start=0):
    assert controller.offer(dose(), start)
    assert controller.authenticate(True, start + 100)
    controller.pill_detected(start + 200)
    controller.tick(start + 800)
    assert controller.state == "COMPLETED"


def test_full_cycle_and_repeat_auth_only_one_motor_command(system):
    c, motor, events = system
    c.offer(dose(), 0)
    c.authenticate(True, 100)
    c.authenticate(True, 200)
    c.pill_detected(300)
    c.tick(800)
    assert c.state == "COMPLETED"
    assert motor.starts == 1
    assert sum(e["event"] == "dispensed" for e in events) == 1
    assert not any(e["event"] == "taken" for e in events)


def test_auth_outside_window_does_nothing(system):
    c, motor, _ = system
    assert not c.authenticate(True, 0)
    assert motor.starts == 0


def test_failed_fingerprint_never_moves_motor_or_extends_window(system):
    c, motor, _ = system
    c.offer(dose(), 0)
    c.authenticate(False, AUTH_WINDOW_MS - 1)
    assert c.deadline == AUTH_WINDOW_MS
    c.tick(AUTH_WINDOW_MS)
    assert c.state == "MISSED"
    assert motor.starts == 0


@pytest.mark.parametrize("instant", [AUTH_WINDOW_MS, AUTH_WINDOW_MS + 1])
def test_exact_deadline_and_late_auth_are_rejected(system, instant):
    c, motor, _ = system
    c.offer(dose(), 0)
    assert not c.authenticate(True, instant)
    assert c.state == "MISSED"
    assert motor.starts == 0


def test_repeated_ticks_send_one_missed_notification(system):
    c, _, events = system
    c.offer(dose(), 0)
    for instant in range(AUTH_WINDOW_MS, AUTH_WINDOW_MS + 5000, 100):
        c.tick(instant)
    assert sum(e["event"] == "sms_requested" for e in events) == 1


def test_repeating_reminder_does_not_dispense(system):
    c, motor, events = system
    c.offer(dose(), 0)
    c.tick(5000)
    c.tick(10000)
    assert sum(e["event"] == "reminder" for e in events) == 3
    assert motor.starts == 0


def test_duplicate_suppressed_after_return_to_idle(system):
    c, motor, _ = system
    succeed(c)
    c.tick(800 + STATUS_HOLD_MS)
    assert c.state == "IDLE"
    assert not c.offer(dose(), 3000)
    assert motor.starts == 1


def test_duplicate_suppressed_after_reboot(system):
    c, _, _ = system
    succeed(c)
    motor = Motor()
    rebooted = Controller(motor, Journal(c.journal.path), lambda event: None)
    assert rebooted.state == "IDLE"
    assert not rebooted.offer(dose(), 0)
    assert motor.starts == 0


def test_power_loss_after_authorization_requires_inspection(system):
    c, _, _ = system
    c.offer(dose(), 0)
    c.authenticate(True, 100)
    motor = Motor()
    rebooted = Controller(motor, Journal(c.journal.path), lambda event: None)
    assert rebooted.state == "ERROR"
    assert not rebooted.offer(dose("another"), 0)
    assert not rebooted.authenticate(True, 0)
    assert motor.starts == 0


def test_corrupt_journal_locks_motor(tmp_path):
    path = tmp_path / "journal.json"
    path.write_text("not JSON")
    motor = Motor()
    c = Controller(motor, Journal(str(path)), lambda event: None)
    assert c.state == "ERROR"
    assert motor.starts == 0


def test_interrupted_journal_write_requires_inspection(tmp_path):
    path = tmp_path / "journal.json"
    path.write_text("{}")
    Path(str(path) + ".tmp").write_text("{}")
    assert not Journal(str(path)).healthy


def test_storage_failure_before_start_prevents_motor(system):
    c, motor, _ = system
    def broken(*args):
        raise OSError("disk full")
    c.journal.put = broken
    c.offer(dose(), 0)
    assert not c.authenticate(True, 100)
    assert c.state == "ERROR"
    assert motor.starts == 0


def test_drop_during_motor_movement_is_latched(system):
    c, _, _ = system
    c.offer(dose(), 0)
    c.authenticate(True, 100)
    c.pill_detected(200)
    c.tick(800)
    assert c.state == "COMPLETED"


def test_idle_drop_does_not_count_for_next_dose(system):
    c, _, _ = system
    c.pill_detected(0)
    c.offer(dose(), 10)
    c.authenticate(True, 100)
    c.tick(800)
    assert c.state == "VERIFYING"


def test_drop_timeout_locks_without_retry(system):
    c, motor, events = system
    c.offer(dose(), 0)
    c.authenticate(True, 100)
    c.tick(800)
    c.tick(800 + VERIFY_TIMEOUT_MS)
    assert c.state == "ERROR"
    assert c.journal.records[dose()["dose_id"]] == "error"
    assert not c.authenticate(True, 10000)
    assert motor.starts == 1
    assert any(e.get("reason") == "drop_not_detected" for e in events)


@pytest.mark.parametrize("failed,stuck,reason", [
    (True, False, "motor_start_failed"), (False, True, "motor_timeout")
])
def test_motor_failure_does_not_auto_retry(tmp_path, failed, stuck, reason):
    motor, events = Motor(failed, stuck), []
    c = Controller(motor, Journal(str(tmp_path / "journal.json")), events.append)
    c.offer(dose(), 0)
    c.authenticate(True, 100)
    c.tick(100 + MOTOR_TIMEOUT_MS)
    assert c.state == "ERROR"
    assert any(e.get("reason") == reason for e in events)


def test_second_dose_waits_until_first_finishes(system):
    c, _, _ = system
    c.offer(dose(), 0)
    assert not c.offer(dose("second"), 100)
    c.authenticate(True, 200)
    c.pill_detected(300)
    c.tick(900)
    c.tick(900 + STATUS_HOLD_MS)
    assert c.offer(dose("second"), 3000, 1000)


def test_already_expired_occurrence_is_missed_without_motor(system):
    c, motor, _ = system
    c.offer(dose(), 0, -1000)
    assert c.state == "MISSED"
    assert motor.starts == 0


def row(**changes):
    value = {"id": "morning", "time": "08:00", "compartment": 1, "enabled": True}
    value.update(changes)
    return value


@pytest.mark.parametrize("changes", [
    {"time": "25:00"}, {"time": "08:99"}, {"time": "8:00"},
    {"time": "garbage"}, {"compartment": 2}, {"id": ""}, {"enabled": "yes"},
])
def test_reject_invalid_schedule(changes):
    with pytest.raises(ValueError):
        validate_schedules([row(**changes)])


def test_reject_duplicate_schedule_ids():
    with pytest.raises(ValueError):
        validate_schedules([row(), row()])


def test_daily_scheduler_date_ids_remaining_window_and_no_early_dose():
    assert daily_candidates([row()], (2026, 10, 31, 7, 59, 59)) == []
    candidates = daily_candidates([row()], (2026, 10, 31, 8, 0, 15))
    assert candidates[0][0]["dose_id"] == "2026-10-31:morning"
    assert candidates[0][1] == 105000
    tomorrow = daily_candidates([row()], (2026, 11, 1, 8, 0, 0))
    assert tomorrow[0][0]["dose_id"] != candidates[0][0]["dose_id"]


def test_disabled_schedule_and_expired_schedule():
    assert daily_candidates([row(enabled=False)], (2026, 10, 31, 8, 0, 0)) == []
    assert daily_candidates([row()], (2026, 10, 31, 8, 3, 0))[0][1] < 0


def test_unlisted_state_transition_is_rejected(system):
    with pytest.raises(RuntimeError):
        system[0]._transition("COMPLETED")
    assert system[0].state == "IDLE"


class Pin:
    def __init__(self):
        self.level = 1
    def value(self):
        return self.level


def test_button_debounce_and_held_button_not_repeated():
    pin = Pin()
    button = DebouncedButton(pin)
    pin.level = 0
    assert not button.pressed(10)
    assert not button.pressed(30)
    assert button.pressed(50)
    assert not button.pressed(1000)
    pin.level = 1
    button.pressed(1100)
    assert not button.pressed(1140)
    pin.level = 0
    button.pressed(1200)
    assert button.pressed(1240)


def test_button_already_held_at_start_does_not_authorize():
    pin = Pin()
    pin.level = 0
    button = DebouncedButton(pin)
    assert not button.pressed(1000)


def test_servo_gate_closes_after_motion():
    class PWM:
        duty = None
        def duty_u16(self, value):
            self.duty = value
    pwm = PWM()
    motor = ServoGate(pwm)
    closed = pwm.duty
    motor.start(0)
    assert pwm.duty > closed
    assert not motor.finished(699)
    assert motor.finished(700)
    assert pwm.duty == closed


class I2C:
    def __init__(self, data):
        self.data = bytes(data)
    def readfrom_mem(self, address, register, count):
        assert (address, register, count) == (0x68, 0, 7)
        return self.data


def test_read_rtc():
    assert read_ds1307(I2C([0x59, 0x30, 0x08, 6, 0x31, 0x10, 0x26])) == (
        2026, 10, 31, 8, 30, 59)


@pytest.mark.parametrize("data", [
    [0x80, 0, 8, 1, 1, 1, 0x26],  # stopped
    [0, 0, 0x48, 1, 1, 1, 0x26],  # 12-hour mode
    [0x6A, 0, 8, 1, 1, 1, 0x26],  # invalid BCD
    [0, 0, 8, 1, 0x31, 0x02, 0x26],  # invalid date
])
def test_invalid_rtc_rejected(data):
    with pytest.raises(ValueError):
        read_ds1307(I2C(data))


def test_wokwi_inputs_and_outputs_match_firmware():
    diagram = json.loads((Path(__file__).parents[1] / "firmware" / "diagram.json").read_text())
    links = {frozenset((a, b)) for a, b, *_ in diagram["connections"]}
    for component, gpio in [("valid:1.l", 19), ("invalid:1.l", 23), ("drop:1.l", 32),
                            ("servo:PWM", 18)]:
        assert frozenset((component, "esp:" + str(gpio))) in links
