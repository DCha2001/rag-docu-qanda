import { NextRequest } from "next/server";
import { getClientIp } from "@/lib/client-ip";

export async function POST(request: NextRequest) {
  const { query, session_id } = await request.json();
  const ip = getClientIp(request);

  const upstream = await fetch(`${process.env.API_URL}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Real-IP": ip,
    },
    body: JSON.stringify({ query, session_id }),
  });

  if (!upstream.ok) {
    const body = await upstream.json().catch(() => ({}));
    const detail = body?.detail ?? upstream.statusText;
    return new Response(JSON.stringify({ error: detail }), {
      status: upstream.status,
      headers: { "Content-Type": "application/json" },
    });
  }

  return new Response(upstream.body, {
    headers: {
      "Content-Type": "text/event-stream",
      "Cache-Control": "no-cache",
    },
  });
}
