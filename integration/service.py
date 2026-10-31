"""Reference app/device API. Run with uvicorn integration.service:create_app --factory.
The app teammate can adapt this service or implement the same contract in an existing backend.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import hmac
import json
import os
from pathlib import Path
import sqlite3
from typing import Annotated, Literal

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictInt, model_validator

Identifier = Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,32}$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Schedule(StrictModel):
    id: Identifier
    time: Annotated[str, Field(pattern=r"^(?:[01][0-9]|2[0-3]):[0-5][0-9]$")]
    compartment: Annotated[StrictInt, Field(ge=1, le=6)]
    enabled: StrictBool
    auth_user_id: Annotated[StrictInt, Field(ge=1, le=1000)]


class ConfigUpdate(StrictModel):
    expected_revision: Annotated[StrictInt, Field(ge=0, le=4294967294)]
    timezone: Literal["Asia/Kolkata"]
    schedules: Annotated[list[Schedule], Field(max_length=32)]

    @model_validator(mode="after")
    def unique_ids(self):
        ids = [row.id for row in self.schedules]
        if len(set(ids)) != len(ids):
            raise ValueError("duplicate schedule id")
        return self


class ConfigAck(StrictModel):
    revision: Annotated[StrictInt, Field(ge=0, le=4294967295)]
    status: Literal["applied", "deferred", "rejected"]
    reason: Annotated[str, Field(max_length=256)] = ""


class CompanionSchedule(Schedule):
    medication: Annotated[str, Field(min_length=1, max_length=80, strict=True)]

    @model_validator(mode="after")
    def trim_label(self):
        self.medication = self.medication.strip()
        if not self.medication:
            raise ValueError("medication label must not be blank")
        return self


class CompanionUpdate(ConfigUpdate):
    schedules: Annotated[list[CompanionSchedule], Field(max_length=32)]


class DeviceEvent(StrictModel):
    schema_version: Literal[2]
    event_id: Annotated[str, Field(min_length=1, max_length=128)]
    device_id: Identifier
    session_id: Annotated[str, Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")]
    event: Literal["dose_due", "authorized", "dispensed", "missed", "error"]
    state: Literal["IDLE", "WAITING_FOR_FINGERPRINT", "HOMING", "POSITIONING",
                   "RELEASING", "VERIFYING", "COMPLETED", "MISSED", "ERROR"]
    elapsed_ms: Annotated[StrictInt, Field(ge=0)]
    occurred_at: None = None  # Calendar timestamps are not implemented by this firmware yet.
    dose_id: Annotated[str | None, Field(max_length=96)]
    schedule_id: Identifier | None
    compartment: Annotated[StrictInt, Field(ge=0, le=6)]
    revision: Annotated[StrictInt, Field(ge=0, le=4294967295)]
    reason: Annotated[str | None, Field(max_length=128)]
    observed_count: Annotated[StrictInt, Field(ge=0)]
    simulated: StrictBool


def create_app(db_path=None, token=None):
    token = token or os.environ.get("MDP_DEVICE_TOKEN")
    if not token:
        raise RuntimeError("Set MDP_DEVICE_TOKEN before starting the reference service.")
    path = Path(db_path or os.environ.get("MDP_DB", "output/integration.sqlite3"))
    path.parent.mkdir(parents=True, exist_ok=True)

    @contextmanager
    def database():
        connection = sqlite3.connect(path, timeout=10)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    with database() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS devices(
          id TEXT PRIMARY KEY, config TEXT NOT NULL, applied_revision INTEGER NOT NULL DEFAULT 0,
          config_result TEXT);
        CREATE TABLE IF NOT EXISTS events(
          event_id TEXT PRIMARY KEY, device_id TEXT NOT NULL, payload TEXT NOT NULL, received_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS notifications(
          event_id TEXT PRIMARY KEY, device_id TEXT NOT NULL, status TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS medication_labels(
          device_id TEXT NOT NULL, schedule_id TEXT NOT NULL, medication TEXT NOT NULL,
          PRIMARY KEY(device_id, schedule_id));
        """)

    def authorize(authorization: str = Header(default="")):
        if not hmac.compare_digest(authorization, "Bearer " + token):
            raise HTTPException(401, "invalid device/demo token")

    def device(db, device_id):
        baseline = json.dumps({"revision": 0, "timezone": "Asia/Kolkata", "schedules": []})
        db.execute("INSERT OR IGNORE INTO devices(id, config) VALUES(?,?)", (device_id, baseline))
        return db.execute("SELECT * FROM devices WHERE id=?", (device_id,)).fetchone()

    app = FastAPI(title="MDP reference integration service", version="2")
    guarded = [Depends(authorize)]

    def save_config(db, device_id, update):
        current = json.loads(device(db, device_id)["config"])
        if current["revision"] != update.expected_revision:
            raise HTTPException(409, "configuration changed; refresh before editing again")
        result = {"revision": current["revision"] + 1, "timezone": update.timezone,
                  "schedules": [s.model_dump(include=set(Schedule.model_fields)) for s in update.schedules]}
        db.execute("UPDATE devices SET config=? WHERE id=?", (json.dumps(result), device_id))
        return result

    def config_status(row):
        desired = json.loads(row["config"])["revision"]
        return {"desired_revision": desired, "applied_revision": row["applied_revision"],
                "synchronized": desired == row["applied_revision"],
                "last_config_result": json.loads(row["config_result"]) if row["config_result"] else None}

    def history_records(db, device_id):
        rows = db.execute("SELECT payload, received_at FROM events WHERE device_id=? ORDER BY rowid DESC",
                          (device_id,)).fetchall()
        events = [dict(json.loads(r["payload"]), received_at=r["received_at"]) for r in rows]
        return [e for e in events if e["event"] in ("dispensed", "missed", "error")]

    def notification_records(db, device_id):
        return [dict(r) for r in db.execute("SELECT * FROM notifications WHERE device_id=?", (device_id,))]

    @app.get("/health")
    def health():
        return {"ok": True, "schema_version": 2}

    @app.get("/api/v1/devices/{device_id}/config", dependencies=guarded)
    def get_config(device_id: Identifier):
        with database() as db:
            return json.loads(device(db, device_id)["config"])

    @app.put("/api/v1/devices/{device_id}/config", dependencies=guarded)
    def put_config(device_id: Identifier, update: ConfigUpdate):
        with database() as db:
            db.execute("BEGIN IMMEDIATE")
            return save_config(db, device_id, update)

    @app.post("/api/v1/devices/{device_id}/config-acks", dependencies=guarded)
    def acknowledge_config(device_id: Identifier, ack: ConfigAck):
        with database() as db:
            db.execute("BEGIN IMMEDIATE")
            row = device(db, device_id)
            desired = json.loads(row["config"])["revision"]
            if ack.revision > desired:
                raise HTTPException(409, "unknown future revision")
            applied = max(row["applied_revision"], ack.revision) if ack.status == "applied" else row["applied_revision"]
            db.execute("UPDATE devices SET applied_revision=?, config_result=? WHERE id=?",
                       (applied, ack.model_dump_json(), device_id))
            return {"accepted": True, "applied_revision": applied}

    @app.get("/api/v1/devices/{device_id}/status", dependencies=guarded)
    def get_status(device_id: Identifier):
        with database() as db:
            row = device(db, device_id)
            return config_status(row)

    @app.get("/api/v1/devices/{device_id}/companion", dependencies=guarded)
    def companion(device_id: Identifier):
        # One database snapshot keeps labels, revisions and history coherent for the UI.
        with database() as db:
            db.execute("BEGIN")
            row = device(db, device_id)
            config = json.loads(row["config"])
            labels = {r["schedule_id"]: r["medication"] for r in db.execute(
                "SELECT * FROM medication_labels WHERE device_id=?", (device_id,))}
            schedules = [dict(s, medication=labels.get(s["id"], s["id"])) for s in config["schedules"]]
            return {"device_id": device_id, "revision": config["revision"], "timezone": config["timezone"],
                    "schedules": schedules, "status": config_status(row),
                    "events": history_records(db, device_id), "notifications": notification_records(db, device_id)}

    @app.put("/api/v1/devices/{device_id}/companion", dependencies=guarded)
    def save_companion(device_id: Identifier, update: CompanionUpdate):
        # App-only metadata never enters the strict firmware config. Both writes commit together.
        with database() as db:
            db.execute("BEGIN IMMEDIATE")
            result = save_config(db, device_id, update)
            db.execute("DELETE FROM medication_labels WHERE device_id=?", (device_id,))
            db.executemany("INSERT INTO medication_labels VALUES(?,?,?)",
                           [(device_id, s.id, s.medication) for s in update.schedules])
            return result

    @app.post("/api/v1/devices/{device_id}/events", dependencies=guarded)
    def ingest(device_id: Identifier, event: DeviceEvent):
        prefix = f"{device_id}:{event.session_id}:"
        suffix = event.event_id.removeprefix(prefix)
        if event.device_id != device_id or not event.event_id.startswith(prefix) or not suffix.isdecimal() or int(suffix) < 1:
            raise HTTPException(422, "event/device identity mismatch")
        payload = json.dumps(event.model_dump(), sort_keys=True, separators=(",", ":"))
        received = datetime.now(timezone.utc).isoformat()
        with database() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute("SELECT payload FROM events WHERE event_id=?", (event.event_id,)).fetchone()
            if existing:
                if existing["payload"] != payload:
                    raise HTTPException(409, "event id reused with different content")
                return {"accepted": True, "duplicate": True, "event_id": event.event_id}
            device(db, device_id)
            db.execute("INSERT INTO events VALUES(?,?,?,?)", (event.event_id, device_id, payload, received))
            if event.event in ("missed", "error"):
                db.execute("INSERT INTO notifications VALUES(?,?,?)",
                           (event.event_id, device_id, "simulated"))
            return {"accepted": True, "duplicate": False, "event_id": event.event_id}

    @app.get("/api/v1/devices/{device_id}/history", dependencies=guarded)
    def history(device_id: Identifier):
        with database() as db:
            return history_records(db, device_id)

    @app.get("/api/v1/devices/{device_id}/notifications", dependencies=guarded)
    def notifications(device_id: Identifier):
        with database() as db:
            return notification_records(db, device_id)
    return app
