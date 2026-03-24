export interface SessionResponse {
  id: string;
  title: string | null;
  created_at: string | null;
}

export interface MessageOut {
  id: string;
  session_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string | null;
}
