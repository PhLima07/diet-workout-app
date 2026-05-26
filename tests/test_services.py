import pytest
import httpx
from unittest.mock import AsyncMock, patch
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

async def test_usda_search_returns_foods():
    from services.usda_service import search_foods
    mock_response = {
        "foods": [
            {
                "description": "Banana, raw",
                "foodNutrients": [
                    {"nutrientName": "Energy", "value": 89, "unitName": "KCAL"},
                    {"nutrientName": "Protein", "value": 1.09, "unitName": "G"},
                    {"nutrientName": "Carbohydrate, by difference", "value": 23.0, "unitName": "G"},
                    {"nutrientName": "Total lipid (fat)", "value": 0.33, "unitName": "G"},
                ]
            }
        ]
    }
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = httpx.Response(200, json=mock_response)
        result = await search_foods("banana")
    assert len(result) == 1
    assert result[0]["description"] == "Banana, raw"
    assert result[0]["calories"] == 89
    assert result[0]["protein_g"] == 1.09

async def test_usda_search_empty_on_http_error():
    from services.usda_service import search_foods
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = httpx.Response(500, json={})
        result = await search_foods("xyz_nonexistent")
    assert result == []
