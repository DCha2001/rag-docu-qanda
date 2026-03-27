import { NextResponse, NextRequest } from "next/server";
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
    const token = await getAccessToken();
    const backend = createBackend(token);
    const document = await backend.sessions.attachDocument(id, document_id);
    return NextResponse.json(document);
  } catch (err) {
    console.error("Failed to attach document to session:", err);
    return NextResponse.json({ error: `Failed to attach document to session ${err}` }, { status: 500 });
  }
}
