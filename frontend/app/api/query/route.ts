import { NextResponse, NextRequest } from "next/server";
import { backend } from "@/lib/backend";

export async function POST(request: NextRequest) {
  try {
    const { query } = await request.json();
    const data = await backend.query.send(query);
    return NextResponse.json(data);
  } catch (err) {
    console.error("Query failed:", err);
    return NextResponse.json({ error: `Query failed ${err}` }, { status: 500 });
  }
}
