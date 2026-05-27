import os
import httpx
from dotenv import load_dotenv

load_dotenv()

RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
BASE_URL = "https://exercisedb.p.rapidapi.com/exercises"
HEADERS = {
    "X-RapidAPI-Key": RAPIDAPI_KEY,
    "X-RapidAPI-Host": "exercisedb.p.rapidapi.com",
}

VALID_BODY_PARTS = [
    "back", "cardio", "chest", "lower arms", "lower legs",
    "neck", "shoulders", "upper arms", "upper legs", "waist",
]

async def search_exercises(body_part: str, limit: int = 8) -> list[dict]:
    if not RAPIDAPI_KEY:
        return []
    url = f"{BASE_URL}/bodyPart/{body_part}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, headers=HEADERS, params={"limit": limit})
        if resp.status_code != 200:
            return []
        return [
            {
                "name": e["name"],
                "bodyPart": e["bodyPart"],
                "target": e["target"],
                "equipment": e["equipment"],
            }
            for e in resp.json()
        ]
    except Exception:
        return []
