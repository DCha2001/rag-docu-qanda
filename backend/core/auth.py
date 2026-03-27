import jwt
from jwt import PyJWKClient
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from core.config import SUPABASE_URL

security = HTTPBearer()

# Fetch and cache Supabase's public keys from their JWKS endpoint.
# PyJWKClient handles automatic key rotation — no secret needed.
# Supabase uses ECC P-256 (ES256) asymmetric signing:
#   - Supabase signs tokens with their private key
#   - We verify with the public key fetched from the JWKS endpoint
_jwks_client = PyJWKClient(
    f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json",
    cache_keys=True,
)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Verify the Supabase JWT using the project's JWKS public key (ES256)
    and return the user's UUID (sub claim).

    Raises 401 if the token is missing, expired, or invalid.
    This dependency is added to any endpoint that requires authentication.
    """
    token = credentials.credentials
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
        )
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing user ID")
        return user_id
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
