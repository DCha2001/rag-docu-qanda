import { NextResponse, NextRequest } from "next/server";
import { createBackend } from "@/lib/backend";
import { getClientIp } from "@/lib/client-ip";

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ id: string; docId: string }> }
) {
  try {
    const { id, docId } = await params;
    const backend = createBackend(getClientIp(request));
    const result = await backend.sessions.detachDocument(id, docId);
    return NextResponse.json(result);
  } catch (err) {
    console.error("Failed to detach document from session:", err);
    return NextResponse.json(
      { error: `Failed to detach document from session ${err}` },
      { status: 500 }
    );
  }
}
