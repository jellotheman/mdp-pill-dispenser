import type { Dashboard } from "@/lib/contract";

export function DevicePanel({ data, connected }: { data: Dashboard | null; connected: boolean }) {
  const status = data?.status;
  const currentResult = status?.last_config_result?.revision === status?.desired_revision ? status?.last_config_result : null;
  return <section className="panel" id="device">
    <div className="panel-head"><div><h2>Integration status</h2><p className="panel-desc">{data?.device_id ?? "Device"} · project demonstration</p></div></div>
    <div className="history-list">
      <div className="history-row"><div className="event-dot">✓</div><div><div className="history-title">Web dashboard</div><div className="history-meta">Original PillPilot interface · Next.js</div></div><span className="tag enabled">Ready</span></div>
      <div className="history-row"><div className="event-dot">{connected ? "✓" : "!"}</div><div><div className="history-title">Schedule &amp; history API</div><div className="history-meta">One persistent SQLite database</div></div><span className={`tag ${connected ? "enabled" : "pending"}`}>{connected ? "Connected" : "Unavailable"}</span></div>
      <div className="history-row"><div className="event-dot">⌁</div><div><div className="history-title">Device configuration</div><div className="history-meta">Saved r{status?.desired_revision ?? "—"} · Applied r{status?.applied_revision ?? "—"}<br />{currentResult ? `${currentResult.status}: ${currentResult.reason}` : "Waiting for device acknowledgement"}</div></div><span className={`tag ${status?.synchronized && connected ? "enabled" : "pending"}`}>{!connected ? "Unknown" : status?.synchronized ? "Applied" : "Pending"}</span></div>
      <div className="history-row"><div className="event-dot">≋</div><div><div className="history-title">SMS notifications</div><div className="history-meta">{data?.notifications.length ?? 0} mock records · no provider connected</div></div><span className="tag pending">Simulated</span></div>
    </div>
    <p className="footer-note">Applied confirms a configuration was stored by the device; it is not a live connectivity indicator. Physical hardware and real SMS remain team integration work.</p>
  </section>;
}
