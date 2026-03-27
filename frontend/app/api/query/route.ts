import { NextResponse, NextRequest } from "next/server";
import { createBackend } from "@/lib/backend";
import { getAccessToken } from "@/lib/supabase/server";

export async function POST(request: NextRequest) {
  try {
    const { query, session_id } = await request.json();
    const token = await getAccessToken();
    const backend = createBackend(token);
    const data = await backend.query.send(query, session_id);
    return NextResponse.json(data);
  } catch (err) {
    console.error("Query failed:", err);
    return NextResponse.json({ error: `Query failed ${err}` }, { status: 500 });
  }
}
