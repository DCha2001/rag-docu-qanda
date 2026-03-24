import { NextResponse } from "next/server";
import { backend } from "@/lib/backend";

export async function GET(
  _request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const messages = await backend.sessions.getMessages(id);
    return NextResponse.json(messages);
  } catch (err) {
    console.error("Failed to fetch session messages:", err);
    return NextResponse.json({ error: `Failed to fetch session messages ${err}` }, { status: 500 });
  }
}
