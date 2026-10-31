"use client";

import { useState } from "react";
import { useDashboard } from "@/lib/use-dashboard";
import { indiaDate } from "@/lib/format";
import { SchedulePanel } from "@/components/schedule-panel";
import { HistoryPanel } from "@/components/history-panel";
import { DevicePanel } from "@/components/device-panel";
import { ApiTestPanel } from "@/components/api-test-panel";

const navigation = [
  ["overview", "▦", "Overview"], ["schedule", "◷", "Medication schedule"],
  ["history", "≋", "Dose history"], ["device", "⚙", "Device settings"],
] as const;

export default function Home() {
  const { data, connected, error, notice, loading, saving, refresh, save } = useDashboard();
  const [section, setSection] = useState("overview");
  const schedules = data?.schedules ?? [];
  const enabledCount = schedules.filter((s) => s.enabled).length;
  const receivedToday = data?.events.filter((e) => e.event === "dispensed" && indiaDate(e.received_at) === indiaDate(new Date())).length ?? 0;
  const synchronized = data?.status.synchronized;

  return (
    <div className="shell" id="overview">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark">✳</div><span>PillPilot</span></div>
        <nav aria-label="Workspace">
          <div className="nav-label">Workspace</div>
          {navigation.map(([id, icon, name]) => <a key={id} href={`#${id}`} onClick={() => setSection(id)} className={`nav-item ${section === id ? "active" : ""}`}><span aria-hidden="true">{icon}</span>{name}</a>)}
        </nav>
        <div className="side-note"><strong>Project prototype</strong>Connected schedules and controller history. Sensors and mechanism are simulated. SMS records are mock notifications.</div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div><div className="eyebrow">SMART DISPENSER / DASHBOARD</div><h1>Good day 👋</h1><p className="subtitle">Your medication schedule at a glance.</p></div>
          <div className="top-actions"><span className={`status-pill ${connected ? "" : "offline"}`}>● {connected ? "Service connected" : loading ? "Connecting…" : "Service unavailable"}</span><div className="avatar">P</div></div>
        </header>

        {error && <div className="notice error" role="alert">{error}</div>}
        {notice && <div className="notice" role="status">{notice}</div>}

        <section className="metrics" aria-label="Summary">
          <div className="metric"><div className="metric-top"><span>Active schedules</span><span className="metric-icon">◷</span></div><div className="metric-value">{loading ? "—" : enabledCount}</div><div className="metric-foot">of {schedules.length} configured schedules</div></div>
          <div className="metric"><div className="metric-top"><span>Dispense reports received today</span><span className="metric-icon">✓</span></div><div className="metric-value">{loading ? "—" : receivedToday}</div><div className="metric-foot">By service receipt date · India time</div></div>
          <div className="metric"><div className="metric-top"><span>Configuration status</span><span className="metric-icon">⌁</span></div><div className="metric-value config-value">{!connected ? "Unavailable" : synchronized ? `Applied r${data?.status.applied_revision}` : `Saved r${data?.revision}`}</div><div className="metric-foot">{synchronized ? "Device acknowledged this revision" : "Awaiting device application"}</div></div>
        </section>

        <div className="content-grid">
          <SchedulePanel schedules={schedules} loading={loading} disabled={saving || !connected} onRefresh={refresh} onSave={save} />
          <div>
            <HistoryPanel events={data?.events ?? []} schedules={schedules} />
            <DevicePanel data={data} connected={connected} />
            <ApiTestPanel />
          </div>
        </div>
      </main>
    </div>
  );
}
