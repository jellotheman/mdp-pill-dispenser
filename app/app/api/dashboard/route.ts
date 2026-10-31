import { NextResponse } from "next/server";
import { configSchema, dashboardSchema, updateSchema } from "@/lib/contract";
import { acceptsOrigin } from "@/lib/request-origin.mjs";

export const dynamic = "force-dynamic";

async function forward(method: "GET" | "PUT", body?: string) {
  const base = process.env.MDP_BACKEND_URL;
  const device = process.env.MDP_DEVICE_ID;
  const token = process.env.MDP_DEVICE_TOKEN;
  if (!base || !device || !token) {
    return NextResponse.json({ error: "Start the dashboard using the presentation launcher, or configure app/.env.local." }, { status: 503 });
  }
  try {
    const response = await fetch(`${base.replace(/\/$/, "")}/api/v1/devices/${encodeURIComponent(device)}/companion`, {
      method, body, cache: "no-store", signal: AbortSignal.timeout(5000),
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    });
    if (!response.ok) {
      const messages: Record<number, string> = {
        401: "The dashboard's service token does not match the integration service.",
        409: "Another edit changed the schedules. Refresh and try again.",
        422: "Invalid schedule. Check the time, label, user ID and compartment (1–6).",
      };
      return NextResponse.json({ error: messages[response.status] ?? "The integration service could not complete the request." }, { status: response.status });
    }
    const data: unknown = await response.json();
    return NextResponse.json(method === "GET" ? dashboardSchema.parse(data) : configSchema.parse(data));
  } catch {
    return NextResponse.json({ error: "Integration service unavailable or returned an incompatible response. Check its terminal and refresh." }, { status: 502 });
  }
}

export async function GET() { return forward("GET"); }

export async function PUT(request: Request) {
  // The presentation app is local-only. Reject cross-origin browser writes.
  if (!acceptsOrigin(request)) {
    return NextResponse.json({ error: "Cross-origin edits are not allowed." }, { status: 403 });
  }
  let body: unknown;
  try { body = await request.json(); }
  catch { return NextResponse.json({ error: "Request body must be valid JSON." }, { status: 400 }); }
  const parsed = updateSchema.safeParse(body);
  if (!parsed.success) {
    return NextResponse.json({ error: "Invalid schedule data. Check the time, label, user ID and compartment (1–6)." }, { status: 400 });
  }
  return forward("PUT", JSON.stringify(parsed.data));
}
