from fastapi import Request


def get_client_ip(request: Request) -> str:
    """
    Extract the real client IP address.
    Next.js proxies all requests and forwards the browser's IP as X-Real-IP.
    Falls back to the direct connection IP when called without a proxy.
    """
    forwarded = request.headers.get("X-Real-IP")
    if forwarded:
        return forwarded
    return request.client.host if request.client else "unknown"
