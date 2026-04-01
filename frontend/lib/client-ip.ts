import { NextRequest } from "next/server";

/**
 * Extract the real client IP from an incoming Next.js request.
 * Reads X-Forwarded-For (set by proxies/load balancers) or X-Real-IP.
 */
export function getClientIp(request: NextRequest): string {
  return (
    request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ??
    request.headers.get("x-real-ip") ??
    "unknown"
  );
}
