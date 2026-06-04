import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from unittest.mock import AsyncMock, patch
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


def make_creds(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


async def _call_with_mock(result):
    with patch("dependencies._fetch_supabase_user", new=AsyncMock(return_value=result)):
        from dependencies import get_current_user
        return await get_current_user(make_creds("any-token"))


@pytest.mark.asyncio
async def test_get_current_user_valid():
    result = await _call_with_mock({"id": "user-uuid-123", "email": "a@b.com"})
    assert result == "user-uuid-123"


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    with pytest.raises(HTTPException) as exc:
        await _call_with_mock(None)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_supabase_error_response():
    with pytest.raises(HTTPException) as exc:
        await _call_with_mock({"error": "invalid_token"})
    assert exc.value.status_code == 401
