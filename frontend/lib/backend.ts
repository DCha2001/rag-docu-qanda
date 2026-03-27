/**
 * Called only in the backend (route.ts files).
 * Use createBackend(token) to create an authenticated client.
 */
import { ApiError } from "./error";
import type { DocumentResponse, IngestResponse } from "@/app/models/documents";
import type { QueryResponse } from "@/app/models/query";
import type { SessionResponse, MessageOut } from "@/app/models/session";

const BASE_URL = process.env.API_URL ?? "http://localhost:8000";

function buildHeaders(
  token: string | undefined,
  extra?: Record<string, string>
): Record<string, string> {
  const headers: Record<string, string> = { ...extra };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

async function fetchBackend<T>(
  path: string,
  init?: RequestInit,
  token?: string
): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: buildHeaders(token, init?.headers as Record<string, string>),
  });
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

/**
 * Create an authenticated backend client.
 * Pass the Supabase access_token from the server-side session.
 */
export function createBackend(token?: string) {
  const fetch = <T>(path: string, init?: RequestInit) =>
    fetchBackend<T>(path, init, token);

  return {
    documents: {
      list: (): Promise<DocumentResponse[]> =>
        fetch<DocumentResponse[]>("/document/list"),

      upload: (file: File): Promise<IngestResponse> => {
        const form = new FormData();
        form.append("file", file);
        return fetch<IngestResponse>("/ingest", { method: "POST", body: form });
      },

      delete: (id: string): Promise<void> =>
        fetch<void>(`/document?id=${encodeURIComponent(id)}`, { method: "DELETE" }),
    },

    query: {
      send: (query: string, session_id: string): Promise<QueryResponse> =>
        fetch<QueryResponse>("/query", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query, session_id }),
        }),
    },

    sessions: {
      list: (): Promise<SessionResponse[]> =>
        fetch<SessionResponse[]>("/sessions"),

      create: (title?: string | null): Promise<SessionResponse> =>
        fetch<SessionResponse>("/sessions", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: title ?? null }),
        }),

      delete: (id: string): Promise<{ detail: string }> =>
        fetch<{ detail: string }>(`/sessions/${encodeURIComponent(id)}`, {
          method: "DELETE",
        }),

      getMessages: (id: string): Promise<MessageOut[]> =>
        fetch<MessageOut[]>(`/sessions/${encodeURIComponent(id)}/messages`),

      getDocuments: (id: string): Promise<DocumentResponse[]> =>
        fetch<DocumentResponse[]>(`/sessions/${encodeURIComponent(id)}/documents`),

      attachDocument: (sessionId: string, documentId: string): Promise<DocumentResponse> =>
        fetch<DocumentResponse>(
          `/sessions/${encodeURIComponent(sessionId)}/documents/${encodeURIComponent(documentId)}`,
          { method: "POST" }
        ),

      detachDocument: (sessionId: string, documentId: string): Promise<{ detail: string }> =>
        fetch<{ detail: string }>(
          `/sessions/${encodeURIComponent(sessionId)}/documents/${encodeURIComponent(documentId)}`,
          { method: "DELETE" }
        ),
    },

    health: {
      ping: (): Promise<{ status: string }> =>
        fetch<{ status: string }>("/health"),
    },
  };
}

/** Unauthenticated client kept for backward compat (health checks etc.) */
export const backend = createBackend();
