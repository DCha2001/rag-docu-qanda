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
    const documents = await backend.sessions.getDocuments(id);
    return NextResponse.json(documents);
  } catch (err) {
    console.error("Failed to fetch session documents:", err);
    return NextResponse.json({ error: `Failed to fetch session documents ${err}` }, { status: 500 });
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
    const { document_id } = await request.json();
    const backend = createBackend(getClientIp(request));
    const document = await backend.sessions.attachDocument(id, document_id);
    return NextResponse.json(document);
  } catch (err) {
    console.error("Failed to attach document to session:", err);
    return NextResponse.json({ error: `Failed to attach document to session ${err}` }, { status: 500 });
  }
}
