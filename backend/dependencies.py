import os
from typing import Optional
import httpx
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

_SUPABASE_URL = os.getenv("SUPABASE_URL", "")
_SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")


async def _fetch_supabase_user(token: str) -> Optional[dict]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(
            f"{_SUPABASE_URL}/auth/v1/user",
            headers={"Authorization": f"Bearer {token}", "apikey": _SUPABASE_ANON_KEY},
        )
    return resp.json() if resp.status_code == 200 else None


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    user = await _fetch_supabase_user(credentials.credentials)
    if not user or "id" not in user:
        raise HTTPException(status_code=401, detail="Token inválido")
    return user["id"]
