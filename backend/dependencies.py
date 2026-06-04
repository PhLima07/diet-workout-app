import os
import base64
import jwt
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def _get_secret() -> bytes:
    raw = os.getenv("SUPABASE_JWT_SECRET")
    if not raw:
        raise HTTPException(status_code=500, detail="SUPABASE_JWT_SECRET não configurado")
    try:
        return base64.b64decode(raw)
    except Exception:
        return raw.encode()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    try:
        payload = jwt.decode(
            credentials.credentials,
            _get_secret(),
            algorithms=["HS256"],
            audience="authenticated",
        )
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido")
