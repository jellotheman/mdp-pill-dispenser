"use client";

import { useEffect, useRef, useState } from "react";
import { dashboardSchema } from "@/lib/contract";

type Result =
  | { state: "idle" | "running" }
  | { state: "success"; summary: string }
  | { state: "failure"; message: string };

export function ApiTestPanel() {
  const [result, setResult] = useState<Result>({ state: "idle" });
  const active = useRef<AbortController | null>(null);
  useEffect(() => () => { active.current?.abort(); }, []);

  async function testApi() {
    if (active.current) return;
    const controller = new AbortController();
    active.current = controller;
    setResult({ state: "running" });
    try {
      const response = await fetch("/api/dashboard", { cache: "no-store", signal: controller.signal });
      if (!response.ok) {
        const body: unknown = await response.json();
        const message = body && typeof body === "object" && "error" in body && typeof body.error === "string"
          ? body.error : `Service request failed (HTTP ${response.status}).`;
        throw new Error(message);
      }
      const data = dashboardSchema.parse(await response.json());
      if (!controller.signal.aborted) setResult({
        state: "success",
        summary: `Read successful: saved revision ${data.revision}, ${data.schedules.length} schedules and ${data.events.length} history records.`,
      });
    } catch (error) {
      if (!controller.signal.aborted) setResult({ state: "failure", message: error instanceof Error ? error.message : "The request failed." });
    } finally {
      if (active.current === controller) active.current = null;
    }
  }

  return <section className="panel" aria-labelledby="api-test-title">
    <div className="panel-head"><div><h2 id="api-test-title">Test integration API</h2><p className="panel-desc">Run a read-only check of the dashboard’s authenticated connection to the integration service.</p></div></div>
    <button className="secondary-btn" type="button" onClick={() => void testApi()} disabled={result.state === "running"}>
      {result.state === "running" ? "Testing…" : "Test API connection"}
    </button>
    <div aria-live="polite">
      {result.state === "success" && <p className="footer-note">✓ {result.summary}</p>}
      {result.state === "failure" && <p className="footer-note" role="alert">Test failed: {result.message}</p>}
    </div>
    <p className="footer-note">This checks the service response, not a live device connection. It does not change schedules or dispense medication.</p>
  </section>;
}
