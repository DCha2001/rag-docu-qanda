import { NextResponse } from "next/server";
import { createBackend } from "@/lib/backend";
import { getAccessToken } from "@/lib/supabase/server";

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const token = await getAccessToken();
    const backend = createBackend(token);
    const result = await backend.sessions.delete(id);
    return NextResponse.json(result);
  } catch (err) {
    console.error("Failed to delete session:", err);
    return NextResponse.json({ error: `Failed to delete session ${err}` }, { status: 500 });
  }
}
