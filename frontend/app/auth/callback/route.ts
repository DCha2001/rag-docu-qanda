import { NextResponse } from "next/server";
import { createClient } from "@/lib/supabase/server";

/**
 * OAuth callback handler.
 *
 * After Google (or any provider) redirects back here, Supabase passes a `code`
 * query param. We exchange it for a session and then redirect the user to the app.
 */
export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const code = searchParams.get("code");
  const next = searchParams.get("next") ?? "/";

  // Railway (and most reverse proxies) run Next.js on an internal address like
  // 0.0.0.0:8080, so `new URL(request.url).origin` returns that internal address
  // instead of the real public URL. Use x-forwarded headers or an explicit env
  // var to get the correct public origin.
  const forwardedHost = request.headers.get("x-forwarded-host");
  const forwardedProto =
    request.headers.get("x-forwarded-proto") ?? "https";
  const origin = process.env.NEXT_PUBLIC_SITE_URL
    ? process.env.NEXT_PUBLIC_SITE_URL.replace(/\/$/, "")
    : forwardedHost
    ? `${forwardedProto}://${forwardedHost}`
    : new URL(request.url).origin;

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`);
    }
  }

  // On error, redirect to login with a message
  return NextResponse.redirect(`${origin}/login?error=auth_callback_failed`);
}
