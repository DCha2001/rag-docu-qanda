/**
 * Client-side API module. Calls Next.js route handlers at relative paths.
 * Never imports server-only modules or accesses process.env directly.
 */
import { ApiError } from "./error";
import type { DocumentResponse, IngestResponse } from "@/app/models/documents";
import type { QueryResponse } from "@/app/models/query";

async function fetchApi<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) {
    throw new ApiError(
      res.status,
      res.statusText,
      `Request failed: ${res.status} ${res.statusText}`
    );
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
  },

  query: {
    send: (query: string): Promise<QueryResponse> =>
      fetchApi<QueryResponse>("/api/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      }),
  },
};
