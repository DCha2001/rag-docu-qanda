export type DocumentStatus =
  | "uploaded"
  | "parsing"
  | "chunking"
  | "embedding"
  | "completed"
  | "failed";

/** Shape returned by GET /documents */
export interface DocumentResponse {
  id: string;
  filename: string;
  status: DocumentStatus;
  chunk_count: number;
  created_at: string | null;
  is_demo?: boolean;
}

/** Shape returned by POST /ingest (full ORM object) */
export interface IngestResponse {
  id: string;
  filename: string;
  file_hash: string | null;
  status: DocumentStatus;
  page_count: number | null;
  chunk_count: number;
  created_at: string | null;
  updated_at: string | null;
}
