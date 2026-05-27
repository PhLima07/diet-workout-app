import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from database import Base, get_db

TEST_DB_URL = "sqlite:///:memory:"
test_engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

def override_get_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()

from main import app
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

client = TestClient(app)

def test_create_profile():
    resp = client.post("/profile/", json={
        "name": "Pedro", "age": 21, "weight_kg": 75.0, "height_cm": 178.0,
        "goal": "ganhar massa", "dietary_restrictions": "", "fitness_level": "intermediário"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == 1
    assert data["name"] == "Pedro"

def test_get_profile():
    client.post("/profile/", json={
        "name": "Pedro", "age": 21, "weight_kg": 75.0, "height_cm": 178.0,
        "goal": "ganhar massa", "dietary_restrictions": "", "fitness_level": "intermediário"
    })
    resp = client.get("/profile/1")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Pedro"

def test_update_profile():
    client.post("/profile/", json={
        "name": "Pedro", "age": 21, "weight_kg": 75.0, "height_cm": 178.0,
        "goal": "ganhar massa", "dietary_restrictions": "", "fitness_level": "iniciante"
    })
    resp = client.put("/profile/1", json={
        "name": "Pedro", "age": 21, "weight_kg": 76.0, "height_cm": 178.0,
        "goal": "ganhar massa", "dietary_restrictions": "", "fitness_level": "intermediário"
    })
    assert resp.status_code == 200
    assert resp.json()["weight_kg"] == 76.0
    assert resp.json()["fitness_level"] == "intermediário"

def test_get_nonexistent_profile():
    resp = client.get("/profile/999")
    assert resp.status_code == 404

# ── Diet router ──────────────────────────────────────────────────────────────

from unittest.mock import patch, AsyncMock

def test_generate_diet_requires_existing_profile():
    resp = client.post("/diet/generate", json={"user_id": 999, "days": 7, "meals_per_day": 4})
    assert resp.status_code == 404

def test_generate_diet_saves_and_returns_plan():
    client.post("/profile/", json={
        "name": "Pedro", "age": 21, "weight_kg": 75.0, "height_cm": 178.0,
        "goal": "ganhar massa", "dietary_restrictions": "", "fitness_level": "intermediário"
    })
    with patch("routers.diet.generate_diet_plan", new_callable=AsyncMock) as mock_gen, \
         patch("routers.diet.search_foods", new_callable=AsyncMock) as mock_foods:
        mock_foods.return_value = []
        mock_gen.return_value = "# Dieta gerada\nDia 1: ..."
        resp = client.post("/diet/generate", json={"user_id": 1, "days": 7, "meals_per_day": 4})
    assert resp.status_code == 200
    data = resp.json()
    assert data["content"] == "# Dieta gerada\nDia 1: ..."
    assert data["user_id"] == 1
    assert data["id"] == 1

def test_diet_history_lists_plans():
    client.post("/profile/", json={
        "name": "Pedro", "age": 21, "weight_kg": 75.0, "height_cm": 178.0,
        "goal": "ganhar massa", "dietary_restrictions": "", "fitness_level": "intermediário"
    })
    with patch("routers.diet.generate_diet_plan", new_callable=AsyncMock) as mock_gen, \
         patch("routers.diet.search_foods", new_callable=AsyncMock) as mock_foods:
        mock_foods.return_value = []
        mock_gen.return_value = "# Dieta"
        client.post("/diet/generate", json={"user_id": 1, "days": 7, "meals_per_day": 4})
        client.post("/diet/generate", json={"user_id": 1, "days": 3, "meals_per_day": 3})
    resp = client.get("/diet/history/1")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

def test_get_diet_plan_by_id():
    client.post("/profile/", json={
        "name": "Pedro", "age": 21, "weight_kg": 75.0, "height_cm": 178.0,
        "goal": "ganhar massa", "dietary_restrictions": "", "fitness_level": "intermediário"
    })
    with patch("routers.diet.generate_diet_plan", new_callable=AsyncMock) as mock_gen, \
         patch("routers.diet.search_foods", new_callable=AsyncMock) as mock_foods:
        mock_foods.return_value = []
        mock_gen.return_value = "# Dieta"
        client.post("/diet/generate", json={"user_id": 1, "days": 7, "meals_per_day": 4})
    resp = client.get("/diet/1")
    assert resp.status_code == 200
    assert resp.json()["id"] == 1

# ── Workout router ────────────────────────────────────────────────────────────

def test_generate_workout_requires_existing_profile():
    resp = client.post("/workout/generate", json={"user_id": 999, "days_per_week": 4, "focus": ""})
    assert resp.status_code == 404

def test_generate_workout_saves_and_returns_plan():
    client.post("/profile/", json={
        "name": "Pedro", "age": 21, "weight_kg": 75.0, "height_cm": 178.0,
        "goal": "ganhar massa", "dietary_restrictions": "", "fitness_level": "intermediário"
    })
    with patch("routers.workout.generate_workout_plan", new_callable=AsyncMock) as mock_gen, \
         patch("routers.workout.search_exercises", new_callable=AsyncMock) as mock_exs:
        mock_exs.return_value = []
        mock_gen.return_value = "# Treino 4x\nDia A: ..."
        resp = client.post("/workout/generate", json={"user_id": 1, "days_per_week": 4, "focus": "hipertrofia"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["content"] == "# Treino 4x\nDia A: ..."
    assert data["focus"] == "hipertrofia"
    assert data["user_id"] == 1

def test_generate_workout_uses_goal_when_focus_empty():
    client.post("/profile/", json={
        "name": "Pedro", "age": 21, "weight_kg": 75.0, "height_cm": 178.0,
        "goal": "emagrecimento", "dietary_restrictions": "", "fitness_level": "iniciante"
    })
    with patch("routers.workout.generate_workout_plan", new_callable=AsyncMock) as mock_gen, \
         patch("routers.workout.search_exercises", new_callable=AsyncMock) as mock_exs:
        mock_exs.return_value = []
        mock_gen.return_value = "# Treino"
        resp = client.post("/workout/generate", json={"user_id": 1, "days_per_week": 3, "focus": ""})
    assert resp.status_code == 200
    assert resp.json()["focus"] == "emagrecimento"

def test_workout_history_lists_plans():
    client.post("/profile/", json={
        "name": "Pedro", "age": 21, "weight_kg": 75.0, "height_cm": 178.0,
        "goal": "ganhar massa", "dietary_restrictions": "", "fitness_level": "intermediário"
    })
    with patch("routers.workout.generate_workout_plan", new_callable=AsyncMock) as mock_gen, \
         patch("routers.workout.search_exercises", new_callable=AsyncMock) as mock_exs:
        mock_exs.return_value = []
        mock_gen.return_value = "# Treino"
        client.post("/workout/generate", json={"user_id": 1, "days_per_week": 4, "focus": "força"})
        client.post("/workout/generate", json={"user_id": 1, "days_per_week": 3, "focus": "cardio"})
    resp = client.get("/workout/history/1")
    assert resp.status_code == 200
    assert len(resp.json()) == 2
