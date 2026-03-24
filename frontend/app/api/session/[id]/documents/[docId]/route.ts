import { NextResponse } from "next/server";
import { backend } from "@/lib/backend";

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string; docId: string }> }
) {
  try {
    const { id, docId } = await params;
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
