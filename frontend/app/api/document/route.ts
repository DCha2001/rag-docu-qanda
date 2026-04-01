import { NextResponse, NextRequest } from "next/server";
import { createBackend } from "@/lib/backend";
import { getClientIp } from "@/lib/client-ip";

export async function GET(request: NextRequest) {
  try {
    const backend = createBackend(getClientIp(request));
    const docs = await backend.documents.list();
    return NextResponse.json(docs);
  } catch (err) {
    console.error("Failed to fetch documents:", err);
    return NextResponse.json({ error: `Failed to fetch documents ${err}` }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest) {
  const id = request.nextUrl.searchParams.get("id");
  if (!id) {
    return NextResponse.json({ error: "Missing id" }, { status: 400 });
  }
  try {
    const backend = createBackend(getClientIp(request));
    await backend.documents.delete(id);
    return NextResponse.json({ success: true });
  } catch (err) {
    console.error("Failed to delete document:", err);
    return NextResponse.json({ error: `Failed to delete document ${err}` }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const backend = createBackend(getClientIp(request));
    const doc = await backend.documents.upload(formData.get("file") as File);
    return NextResponse.json(doc);
  } catch (err) {
    console.error("Failed to upload document:", err);
    return NextResponse.json({ error: `Failed to upload document ${err}` }, { status: 500 });
  }
}
