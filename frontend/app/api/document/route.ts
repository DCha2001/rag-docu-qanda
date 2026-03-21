import { NextResponse, NextRequest } from "next/server";
import { backend } from "@/lib/backend";

export async function GET() {
  try {
    const docs = await backend.documents.list();

    
    return NextResponse.json(docs);
  } catch (err) {
    console.error("Failed to fetch documents:", err);
    return NextResponse.json({ error: "Failed to fetch documents" }, { status: 500 });
  }
}

export async function DELETE(request: NextRequest) {
  const id = request.nextUrl.searchParams.get("id");
  if (!id) {
    return NextResponse.json({ error: "Missing id" }, { status: 400 });
  }
  try {
    await backend.documents.delete(id);
    return NextResponse.json({ success: true });
  } catch (err) {
    console.error("Failed to delete document:", err);
    return NextResponse.json({ error: "Failed to delete document" }, { status: 500 });
  }
}

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const doc = await backend.documents.upload(formData.get("file") as File);
    return NextResponse.json(doc);
  } catch (err) {
    console.error("Failed to upload document:", err);
    return NextResponse.json({ error: "Failed to upload document" }, { status: 500 });
  }
}
