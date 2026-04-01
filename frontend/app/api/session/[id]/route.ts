import { NextResponse, NextRequest } from "next/server";
import { createBackend } from "@/lib/backend";
import { getClientIp } from "@/lib/client-ip";

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const backend = createBackend(getClientIp(request));
    const result = await backend.sessions.delete(id);
    return NextResponse.json(result);
  } catch (err) {
    console.error("Failed to delete session:", err);
    return NextResponse.json({ error: `Failed to delete session ${err}` }, { status: 500 });
  }
}
