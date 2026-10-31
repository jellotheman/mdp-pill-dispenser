import type { DoseEvent, Schedule } from "@/lib/contract";
import { prettyDate } from "@/lib/format";

const labels = { dispensed: "Dispensed", missed: "Missed dose", error: "Device error" };
const icons = { dispensed: "✓", missed: "!", error: "×" };

export function HistoryPanel({ events, schedules }: { events: DoseEvent[]; schedules: Schedule[] }) {
  const names = new Map(schedules.map((s) => [s.id, s.medication]));
  return <section className="panel" id="history">
    <div className="panel-head"><div><h2>Recent dose history</h2><p className="panel-desc">Controller outcomes · updated every three seconds.</p></div></div>
    {events.length === 0 ? <div className="empty">No dose outcomes yet. Connect Wokwi and complete or miss a scheduled dose.</div> : <div className="history-list">
      {events.slice(0, 8).map((event) => <div className="history-row" key={event.event_id}>
        <div className="event-dot">{icons[event.event]}</div>
        <div><div className="history-title">{(event.schedule_id && names.get(event.schedule_id)) || event.schedule_id || "Device startup"}</div><div className="history-meta">Received {prettyDate(event.received_at)} IST · {event.simulated ? "Simulated" : "Device report"}<br />{event.reason?.replaceAll("_", " ")}<br />{event.dose_id}</div></div>
        <span className={`tag ${event.event}`}>{labels[event.event]}</span>
      </div>)}
    </div>}
    <p className="footer-note">Times show service receipt, not the original dose time. Dispensed does not establish ingestion. Simulated outcomes come from the controller, with no real medication released.</p>
  </section>;
}
