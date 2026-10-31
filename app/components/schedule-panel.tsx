"use client";

import { useRef, useState, type FormEvent } from "react";
import type { Schedule } from "@/lib/contract";
import { prettyTime } from "@/lib/format";

type Props = {
  schedules: Schedule[];
  loading: boolean;
  disabled: boolean;
  onRefresh: () => Promise<void>;
  onSave: (schedules: Schedule[]) => Promise<boolean>;
};

export function SchedulePanel({ schedules, loading, disabled, onRefresh, onSave }: Props) {
  const [medication, setMedication] = useState("");
  const [time, setTime] = useState("08:00");
  const [compartment, setCompartment] = useState("1");
  const [user, setUser] = useState("1");
  const draftId = useRef<string | null>(null);

  async function addSchedule(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const id = draftId.current ?? `dose-${crypto.randomUUID().slice(0, 20)}`;
    draftId.current = id;
    const item: Schedule = {
      id, medication: medication.trim(),
      time, compartment: Number(compartment), enabled: true, auth_user_id: Number(user),
    };
    // Retain identity if a save committed but its response was lost, then polling recovered it.
    if (await onSave([...schedules.filter((schedule) => schedule.id !== id), item])) {
      draftId.current = null;
      setMedication("");
    }
  }

  return <div id="schedule">
    <section className="panel">
      <div className="panel-head"><div><h2>Medication schedule</h2><p className="panel-desc">Daily doses · Asia/Kolkata · six preloaded compartments.</p></div><button className="secondary-btn" disabled={loading} onClick={() => void onRefresh()}>Refresh</button></div>
      {loading ? <div className="empty">Loading schedules…</div> : schedules.length === 0 ? <div className="empty">No schedules yet. Add one using the form.</div> : <div className="schedule-list">
        {[...schedules].sort((a, b) => a.time.localeCompare(b.time)).map((s) => <div className="schedule-row" key={s.id}>
          <div className="time">{prettyTime(s.time)}</div>
          <div className="dose-info"><div className="pill-icon">▤</div><div><div className="dose-name">{s.medication}</div><div className="dose-sub">Compartment {s.compartment} · User {s.auth_user_id} · {s.id}</div></div></div>
          <button className={`tag ${s.enabled ? "enabled" : "disabled"}`} disabled={disabled} onClick={() => void onSave(schedules.map((row) => row.id === s.id ? { ...row, enabled: !row.enabled } : row))} aria-label={`${s.enabled ? "Pause" : "Enable"} ${s.medication}`}>{s.enabled ? "Enabled" : "Paused"}</button>
        </div>)}
      </div>}
    </section>

    <section className="panel">
      <div className="panel-head"><div><h2>Add a schedule</h2><p className="panel-desc">Medication label, time, compartment and matching user.</p></div></div>
      <form onSubmit={addSchedule}>
        <fieldset disabled={disabled || schedules.length >= 32}>
          <div className="form-grid">
            <div className="field full"><label htmlFor="medication">Medication label</label><input id="medication" value={medication} onChange={(e) => setMedication(e.target.value)} placeholder="e.g. Morning medication" required maxLength={80} pattern=".*\S.*" /></div>
            <div className="field"><label htmlFor="time">Dose time (India)</label><input id="time" type="time" value={time} onChange={(e) => setTime(e.target.value)} required /></div>
            <div className="field"><label htmlFor="compartment">Compartment number</label><select id="compartment" value={compartment} onChange={(e) => setCompartment(e.target.value)}>{[1, 2, 3, 4, 5, 6].map((n) => <option value={n} key={n}>Compartment {n}</option>)}</select></div>
            <div className="field"><label htmlFor="user">Authorized user ID</label><input id="user" type="number" min={1} max={1000} value={user} onChange={(e) => setUser(e.target.value)} required /></div>
          </div>
          <div className="form-actions"><button className="primary-btn" type="submit">＋ Add schedule</button><span className="panel-desc">Saved and applied are tracked separately</span></div>
        </fieldset>
        <p className="footer-note">Each compartment contains one preloaded item. A new schedule does not refill a used slot. Wokwi&apos;s green button represents user 1.</p>
      </form>
    </section>
  </div>;
}
