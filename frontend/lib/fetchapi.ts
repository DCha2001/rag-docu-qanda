/**
 * Client-side API module. Calls Next.js route handlers at relative paths.
 * Never imports server-only modules or accesses process.env directly.
 */
import { ApiError } from "./error";
import type { DocumentResponse, IngestResponse } from "@/app/models/documents";
import type { SessionResponse, MessageOut } from "@/app/models/session";

async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
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

export const api = {
  documents: {
    list: (): Promise<DocumentResponse[]> =>
      fetchApi<DocumentResponse[]>("/api/document"),

    upload: (file: File): Promise<IngestResponse> => {
      const form = new FormData();
      form.append("file", file);
      return fetchApi<IngestResponse>("/api/document", { method: "POST", body: form });
    },
    delete: (id: string): Promise<void> =>
      fetchApi<void>(`/api/document?id=${encodeURIComponent(id)}`, { method: "DELETE" }),
  },

  sessions: {
    list: (): Promise<SessionResponse[]> =>
      fetchApi<SessionResponse[]>("/api/session"),

    create: (title?: string | null): Promise<SessionResponse> =>
      fetchApi<SessionResponse>("/api/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: title ?? null }),
      }),

    delete: (id: string): Promise<{ detail: string }> =>
      fetchApi<{ detail: string }>(`/api/session/${encodeURIComponent(id)}`, {
        method: "DELETE",
      }),

    getMessages: (id: string): Promise<MessageOut[]> =>
      fetchApi<MessageOut[]>(`/api/session/${encodeURIComponent(id)}/messages`),

    getDocuments: (id: string): Promise<DocumentResponse[]> =>
      fetchApi<DocumentResponse[]>(`/api/session/${encodeURIComponent(id)}/documents`),

    attachDocument: (sessionId: string, documentId: string): Promise<DocumentResponse> =>
      fetchApi<DocumentResponse>(`/api/session/${encodeURIComponent(sessionId)}/documents`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ document_id: documentId }),
      }),

    detachDocument: (sessionId: string, documentId: string): Promise<{ detail: string }> =>
      fetchApi<{ detail: string }>(
        `/api/session/${encodeURIComponent(sessionId)}/documents/${encodeURIComponent(documentId)}`,
        { method: "DELETE" }
      ),
  },
};
