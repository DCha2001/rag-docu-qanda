/**
 * Called only in the backend (route.ts files)
 * 
 */
import { ApiError } from "./error";
import type { DocumentResponse, IngestResponse } from "@/app/models/documents";
import type { QueryResponse } from "@/app/models/query";

const BASE_URL = process.env.API_URL ?? "http://localhost:8000";

async function fetchBackend<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, init);
  if (!res.ok) {
    throw new ApiError(
      res.status,
      res.statusText,
      `Backend request failed: ${res.status} ${res.statusText}`
    );
  }
  return res.json();
}

export const backend = {
  documents: {
    list: (): Promise<DocumentResponse[]> =>
      fetchBackend<DocumentResponse[]>("/documents"),

    upload: (file: File): Promise<IngestResponse> => {
      const form = new FormData();
      form.append("file", file);
      return fetchBackend<IngestResponse>("/ingest", { method: "POST", body: form });
    },
    delete: (id: string): Promise<void> =>
      fetchBackend<void>(`/document?id=${encodeURIComponent(id)}`, { method: "DELETE" }),
  },

  query: {
    send: (query: string): Promise<QueryResponse> =>
      fetchBackend<QueryResponse>(
        `/query?query=${encodeURIComponent(query)}`,
        { method: "POST" }
      ),
  },

  health: {
    ping: (): Promise<{ status: string }> =>
      fetchBackend<{ status: string }>("/health"),
  },
};
