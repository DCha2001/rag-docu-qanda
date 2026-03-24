import { NextResponse } from "next/server";
import { backend } from "@/lib/backend";

export async function DELETE(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const result = await backend.sessions.delete(id);
    return NextResponse.json(result);
  } catch (err) {
    console.error("Failed to delete session:", err);
    return NextResponse.json({ error: `Failed to delete session ${err}` }, { status: 500 });
  }
}
