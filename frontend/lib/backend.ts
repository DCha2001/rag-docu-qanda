/**
 * Called only in the backend (route.ts files)
 *
 */
import { ApiError } from "./error";
import type { DocumentResponse, IngestResponse } from "@/app/models/documents";
import type { QueryResponse } from "@/app/models/query";
import type { SessionResponse, MessageOut } from "@/app/models/session";

const BASE_URL = process.env.API_URL ?? "http://localhost:8000";

async function fetchBackend<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, init);
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
      else if (body?.error) detail = body.error;
    } catch {}
    throw new ApiError(res.status, res.statusText, `${res.status}: ${detail}`);
  }
  return res.json();
}

export const backend = {
  documents: {
    list: (): Promise<DocumentResponse[]> =>
      fetchBackend<DocumentResponse[]>("/document/list"),

    upload: (file: File): Promise<IngestResponse> => {
      const form = new FormData();
      form.append("file", file);
      return fetchBackend<IngestResponse>("/ingest", { method: "POST", body: form });
    },
    delete: (id: string): Promise<void> =>
      fetchBackend<void>(`/document?id=${encodeURIComponent(id)}`, { method: "DELETE" }),
  },

  query: {
    send: (query: string, session_id: string): Promise<QueryResponse> =>
      fetchBackend<QueryResponse>("/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, session_id }),
      }),
  },

  sessions: {
    list: (): Promise<SessionResponse[]> =>
      fetchBackend<SessionResponse[]>("/sessions"),

    create: (title?: string | null): Promise<SessionResponse> =>
      fetchBackend<SessionResponse>("/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: title ?? null }),
      }),

    delete: (id: string): Promise<{ detail: string }> =>
      fetchBackend<{ detail: string }>(`/sessions/${encodeURIComponent(id)}`, {
        method: "DELETE",
      }),

    getMessages: (id: string): Promise<MessageOut[]> =>
      fetchBackend<MessageOut[]>(`/sessions/${encodeURIComponent(id)}/messages`),

    getDocuments: (id: string): Promise<DocumentResponse[]> =>
      fetchBackend<DocumentResponse[]>(`/sessions/${encodeURIComponent(id)}/documents`),

    attachDocument: (sessionId: string, documentId: string): Promise<DocumentResponse> =>
      fetchBackend<DocumentResponse>(
        `/sessions/${encodeURIComponent(sessionId)}/documents/${encodeURIComponent(documentId)}`,
        { method: "POST" }
      ),

    detachDocument: (sessionId: string, documentId: string): Promise<{ detail: string }> =>
      fetchBackend<{ detail: string }>(
        `/sessions/${encodeURIComponent(sessionId)}/documents/${encodeURIComponent(documentId)}`,
        { method: "DELETE" }
      ),
  },

  health: {
    ping: (): Promise<{ status: string }> =>
      fetchBackend<{ status: string }>("/health"),
  },
};
