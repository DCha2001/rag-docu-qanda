import { NextResponse } from "next/server";
import { createBackend } from "@/lib/backend";
import { getAccessToken } from "@/lib/supabase/server";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const token = await getAccessToken();
    const backend = createBackend(token);
    const messages = await backend.sessions.getMessages(id);
    return NextResponse.json(messages);
  } catch (err) {
    console.error("Failed to fetch session messages:", err);
    return NextResponse.json({ error: `Failed to fetch session messages ${err}` }, { status: 500 });
  }
}
