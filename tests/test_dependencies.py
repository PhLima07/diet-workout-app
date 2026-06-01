import pytest
import jwt
import time
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

os.environ["SUPABASE_JWT_SECRET"] = "test-secret"

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

def make_token(user_id: str, secret: str = "test-secret", expired: bool = False) -> str:
    payload = {
        "sub": user_id,
        "role": "authenticated",
        "aud": "authenticated",
        "exp": int(time.time()) + (-3600 if expired else 3600),
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def test_get_current_user_valid_token():
    from dependencies import get_current_user
    token = make_token("user-uuid-123")
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    result = get_current_user(creds)
    assert result == "user-uuid-123"

def test_get_current_user_expired_token():
    from dependencies import get_current_user
    token = make_token("user-uuid-123", expired=True)
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
    with pytest.raises(HTTPException) as exc:
        get_current_user(creds)
    assert exc.value.status_code == 401

def test_get_current_user_invalid_token():
    from dependencies import get_current_user
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token-invalido")
    with pytest.raises(HTTPException) as exc:
        get_current_user(creds)
    assert exc.value.status_code == 401
