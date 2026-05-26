import os
import httpx
from dotenv import load_dotenv

load_dotenv()

USDA_API_KEY = os.getenv("USDA_API_KEY", "DEMO_KEY")
BASE_URL = "https://api.nal.usda.gov/fdc/v1"

async def search_foods(query: str, max_results: int = 8) -> list[dict]:
    url = f"{BASE_URL}/foods/search"
    params = {"query": query, "api_key": USDA_API_KEY, "pageSize": max_results}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url, params=params)
        if resp.status_code != 200:
            return []
        foods = []
        for item in resp.json().get("foods", []):
            nutrients = {n["nutrientName"]: n["value"] for n in item.get("foodNutrients", [])}
            foods.append({
                "description": item["description"],
                "calories": nutrients.get("Energy", 0),
                "protein_g": nutrients.get("Protein", 0),
                "carbs_g": nutrients.get("Carbohydrate, by difference", 0),
                "fat_g": nutrients.get("Total lipid (fat)", 0),
            })
        return foods
    except Exception:
        return []
