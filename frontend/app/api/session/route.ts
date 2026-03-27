import { NextResponse, NextRequest } from "next/server";
import { createBackend } from "@/lib/backend";
import { getAccessToken } from "@/lib/supabase/server";

export async function GET() {
  try {
    const token = await getAccessToken();
    const backend = createBackend(token);
    const sessions = await backend.sessions.list();
    return NextResponse.json(sessions);
  } catch (err) {
    console.error("Failed to fetch sessions:", err);
    return NextResponse.json({ error: `Failed to fetch sessions ${err}` }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const { title } = await request.json();
    const token = await getAccessToken();
    const backend = createBackend(token);
    const session = await backend.sessions.create(title);
    return NextResponse.json(session);
  } catch (err) {
    console.error("Failed to create session:", err);
    return NextResponse.json({ error: `Failed to create session ${err}` }, { status: 500 });
  }
}
