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

async def test_exercise_search_returns_exercises():
    from services.exercise_service import search_exercises
    mock_response = [
        {"name": "barbell squat", "bodyPart": "upper legs", "target": "quads", "equipment": "barbell"}
    ]
    with patch("services.exercise_service.RAPIDAPI_KEY", "test-key"), \
         patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = httpx.Response(200, json=mock_response)
        result = await search_exercises("upper legs")
    assert len(result) == 1
    assert result[0]["name"] == "barbell squat"
    assert result[0]["bodyPart"] == "upper legs"

async def test_exercise_search_empty_on_error():
    from services.exercise_service import search_exercises
    with patch("services.exercise_service.RAPIDAPI_KEY", "test-key"), \
         patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = httpx.Response(403, json={})
        result = await search_exercises("chest")
    assert result == []

async def test_generate_diet_plan_returns_final_refined_plan():
    from services.claude_service import generate_diet_plan
    profile = {
        "name": "Pedro", "age": 21, "weight_kg": 75.0, "height_cm": 178.0,
        "goal": "ganhar massa muscular", "dietary_restrictions": "",
        "fitness_level": "intermediário", "sex": "masculino",
    }
    foods_context = [
        {"description": "Frango grelhado", "calories": 165, "protein_g": 31.0, "carbs_g": 0.0, "fat_g": 3.6}
    ]

    def make_mock(text):
        return type("Msg", (), {"content": [type("Block", (), {"text": text})()]})()

    with patch("services.claude_service._client") as mock_client:
        mock_client.messages.create = AsyncMock(side_effect=[
            make_mock("# Rascunho dieta\nDia 1: frango..."),
            make_mock("Problemas: calorias abaixo do necessário para ganho de massa."),
            make_mock("# Dieta refinada\nDia 1: frango + arroz..."),
        ])
        result = await generate_diet_plan(profile, foods_context, days=7, meals_per_day=4)

    assert result == "# Dieta refinada\nDia 1: frango + arroz..."
    assert mock_client.messages.create.call_count == 3

async def test_generate_workout_plan_returns_final_refined_plan():
    from services.claude_service import generate_workout_plan
    profile = {
        "name": "Pedro", "age": 21, "weight_kg": 75.0, "height_cm": 178.0,
        "goal": "ganhar massa muscular", "dietary_restrictions": "",
        "fitness_level": "intermediário",
    }
    exercises_context = [
        {"name": "barbell squat", "bodyPart": "upper legs", "target": "quads", "equipment": "barbell"}
    ]

    def make_mock(text):
        return type("Msg", (), {"content": [type("Block", (), {"text": text})()]})()

    with patch("services.claude_service._client") as mock_client:
        mock_client.messages.create = AsyncMock(side_effect=[
            make_mock("# Rascunho treino\nDia A: agachamento..."),
            make_mock("Problemas: volume excessivo para intermediário, sem progressão clara."),
            make_mock("# Treino refinado\nDia A: agachamento 4x8..."),
        ])
        result = await generate_workout_plan(profile, exercises_context, days_per_week=4, focus="hipertrofia")

    assert result == "# Treino refinado\nDia A: agachamento 4x8..."
    assert mock_client.messages.create.call_count == 3
