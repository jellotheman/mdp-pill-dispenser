"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { dashboardSchema, type Dashboard, type Schedule } from "./contract";

type Connection =
  | { status: "loading" }
  | { status: "connected" }
  | { status: "unavailable"; error: string };
type Edit =
  | { status: "idle" }
  | { status: "saving" }
  | { status: "saved"; message: string }
  | { status: "failed"; error: string };

function message(cause: unknown) {
  return cause instanceof Error ? cause.message : "The request failed.";
}

async function readResponse(response: Response) {
  if (!response.ok) {
    const data: unknown = await response.json();
    throw new Error(
      data !== null && typeof data === "object" && "error" in data && typeof data.error === "string"
        ? data.error : "The request failed.",
    );
  }
  return response.json();
}

async function loadSnapshot(signal: AbortSignal) {
  return dashboardSchema.parse(await readResponse(await fetch("/api/dashboard", {
    cache: "no-store", signal,
  })));
}

export function useDashboard() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [connection, setConnection] = useState<Connection>({ status: "loading" });
  const [edit, setEdit] = useState<Edit>({ status: "idle" });
  const loadingRequest = useRef<AbortController | null>(null);
  const editingRequest = useRef<AbortController | null>(null);

  const refresh = useCallback(async () => {
    // One read at a time: slow responses must finish rather than being superseded by every poll.
    if (loadingRequest.current || editingRequest.current) return;
    const request = new AbortController();
    loadingRequest.current = request;
    try {
      const next = await loadSnapshot(request.signal);
      if (request.signal.aborted) return;
      setData(next);
      setConnection({ status: "connected" });
    } catch (cause) {
      if (!request.signal.aborted) setConnection({ status: "unavailable", error: message(cause) });
    } finally {
      if (loadingRequest.current === request) loadingRequest.current = null;
    }
  }, []);

  useEffect(() => {
    let disposed = false;
    let timer: ReturnType<typeof setTimeout>;
    const reads = loadingRequest;
    const edits = editingRequest;
    async function poll() {
      await refresh();
      if (!disposed) timer = setTimeout(() => void poll(), 3000);
    }
    void poll();
    return () => {
      disposed = true;
      clearTimeout(timer);
      reads.current?.abort();
      reads.current = null;
      edits.current?.abort();
      edits.current = null;
    };
  }, [refresh]);

  async function save(schedules: Schedule[]) {
    if (!data || editingRequest.current || connection.status !== "connected") return false;
    const request = new AbortController();
    editingRequest.current = request;
    loadingRequest.current?.abort();
    setEdit({ status: "saving" });
    let saved = false;
    try {
      await readResponse(await fetch("/api/dashboard", {
        method: "PUT", signal: request.signal, headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ expected_revision: data.revision, timezone: data.timezone, schedules }),
      }));
      saved = true;
      const next = await loadSnapshot(request.signal);
      if (!request.signal.aborted) {
        setData(next);
        setConnection({ status: "connected" });
        setEdit({ status: "saved", message: "Saved to the service. The device confirms application separately." });
      }
    } catch (cause) {
      if (!request.signal.aborted) {
        if (saved) {
          setConnection({ status: "unavailable", error: message(cause) });
          setEdit({ status: "saved", message: "Saved to the service. Refresh to check device application." });
        } else {
          setEdit({ status: "failed", error: message(cause) });
        }
      }
    } finally {
      if (editingRequest.current === request) editingRequest.current = null;
    }
    return saved;
  }

  return {
    data, refresh, save,
    loading: connection.status === "loading",
    connected: connection.status === "connected",
    saving: edit.status === "saving",
    error: connection.status === "unavailable" ? connection.error : edit.status === "failed" ? edit.error : "",
    notice: edit.status === "saved" ? edit.message : "",
  };
}
