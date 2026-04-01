import { NextResponse, NextRequest } from "next/server";
import { createBackend } from "@/lib/backend";
import { getClientIp } from "@/lib/client-ip";

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const backend = createBackend(getClientIp(request));
    const messages = await backend.sessions.getMessages(id);
    return NextResponse.json(messages);
  } catch (err) {
    console.error("Failed to fetch session messages:", err);
    return NextResponse.json({ error: `Failed to fetch session messages ${err}` }, { status: 500 });
  }
}
