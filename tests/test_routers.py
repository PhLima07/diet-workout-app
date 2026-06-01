import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, AsyncMock
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

os.environ["SUPABASE_JWT_SECRET"] = "test-secret"

from database import Base, get_db
from dependencies import get_current_user

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

TEST_USER_ID = "550e8400-e29b-41d4-a716-446655440000"

from main import app
app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = lambda: TEST_USER_ID

@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)

client = TestClient(app)

PROFILE_BODY = {
    "name": "Pedro", "age": 21, "weight_kg": 75.0, "height_cm": 178.0,
    "goal": "ganhar massa", "dietary_restrictions": "", "fitness_level": "intermediário",
}

# ── Profile ──────────────────────────────────────────────────────────────────

def test_create_profile():
    resp = client.post("/profile/", json=PROFILE_BODY)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Pedro"

def test_get_profile_me():
    client.post("/profile/", json=PROFILE_BODY)
    resp = client.get("/profile/me")
    assert resp.status_code == 200
    assert resp.json()["name"] == "Pedro"

def test_update_profile():
    client.post("/profile/", json=PROFILE_BODY)
    resp = client.put("/profile/me", json={**PROFILE_BODY, "weight_kg": 76.0})
    assert resp.status_code == 200
    assert resp.json()["weight_kg"] == 76.0

def test_get_nonexistent_profile():
    resp = client.get("/profile/me")
    assert resp.status_code == 404

# ── Diet ─────────────────────────────────────────────────────────────────────

def test_generate_diet_requires_profile():
    resp = client.post("/diet/generate", json={"days": 7, "meals_per_day": 4})
    assert resp.status_code == 404

def test_generate_diet_saves_and_returns_plan():
    client.post("/profile/", json=PROFILE_BODY)
    with patch("routers.diet.generate_diet_plan", new_callable=AsyncMock) as mock_gen, \
         patch("routers.diet.search_foods", new_callable=AsyncMock) as mock_foods:
        mock_foods.return_value = []
        mock_gen.return_value = "# Dieta gerada\nDia 1: ..."
        resp = client.post("/diet/generate", json={"days": 7, "meals_per_day": 4})
    assert resp.status_code == 200
    data = resp.json()
    assert data["content"] == "# Dieta gerada\nDia 1: ..."

def test_diet_history_lists_plans():
    client.post("/profile/", json=PROFILE_BODY)
    with patch("routers.diet.generate_diet_plan", new_callable=AsyncMock) as mock_gen, \
         patch("routers.diet.search_foods", new_callable=AsyncMock) as mock_foods:
        mock_foods.return_value = []
        mock_gen.return_value = "# Dieta"
        client.post("/diet/generate", json={"days": 7, "meals_per_day": 4})
        client.post("/diet/generate", json={"days": 3, "meals_per_day": 3})
    resp = client.get("/diet/history")
    assert resp.status_code == 200
    assert len(resp.json()) == 2

# ── Workout ───────────────────────────────────────────────────────────────────

def test_generate_workout_requires_profile():
    resp = client.post("/workout/generate", json={"days_per_week": 4, "focus": ""})
    assert resp.status_code == 404

def test_generate_workout_saves_and_returns_plan():
    client.post("/profile/", json=PROFILE_BODY)
    with patch("routers.workout.generate_workout_plan", new_callable=AsyncMock) as mock_gen, \
         patch("routers.workout.search_exercises", new_callable=AsyncMock) as mock_exs:
        mock_exs.return_value = []
        mock_gen.return_value = "# Treino 4x\nDia A: ..."
        resp = client.post("/workout/generate", json={"days_per_week": 4, "focus": "hipertrofia"})
    assert resp.status_code == 200
    assert resp.json()["content"] == "# Treino 4x\nDia A: ..."
    assert resp.json()["focus"] == "hipertrofia"

def test_generate_workout_uses_goal_when_focus_empty():
    client.post("/profile/", json=PROFILE_BODY)
    with patch("routers.workout.generate_workout_plan", new_callable=AsyncMock) as mock_gen, \
         patch("routers.workout.search_exercises", new_callable=AsyncMock) as mock_exs:
        mock_exs.return_value = []
        mock_gen.return_value = "# Treino"
        resp = client.post("/workout/generate", json={"days_per_week": 3, "focus": ""})
    assert resp.status_code == 200
    assert resp.json()["focus"] == "ganhar massa"

def test_workout_history_lists_plans():
    client.post("/profile/", json=PROFILE_BODY)
    with patch("routers.workout.generate_workout_plan", new_callable=AsyncMock) as mock_gen, \
         patch("routers.workout.search_exercises", new_callable=AsyncMock) as mock_exs:
        mock_exs.return_value = []
        mock_gen.return_value = "# Treino"
        client.post("/workout/generate", json={"days_per_week": 4, "focus": "força"})
        client.post("/workout/generate", json={"days_per_week": 3, "focus": "cardio"})
    resp = client.get("/workout/history")
    assert resp.status_code == 200
    assert len(resp.json()) == 2
