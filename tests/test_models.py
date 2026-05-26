import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from database import Base
from models import UserProfile, DietPlan, WorkoutPlan

@pytest.fixture
def engine():
    e = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(e)
    return e

def test_tables_created(engine):
    tables = inspect(engine).get_table_names()
    assert "user_profiles" in tables
    assert "diet_plans" in tables
    assert "workout_plans" in tables

def test_user_profile_columns(engine):
    cols = {c["name"] for c in inspect(engine).get_columns("user_profiles")}
    assert {"id", "name", "age", "weight_kg", "height_cm", "goal", "dietary_restrictions",
            "fitness_level", "sex", "available_equipment"} <= cols

def test_diet_plan_columns(engine):
    cols = {c["name"] for c in inspect(engine).get_columns("diet_plans")}
    assert {"id", "user_id", "created_at", "content", "calories_target"} <= cols

def test_workout_plan_columns(engine):
    cols = {c["name"] for c in inspect(engine).get_columns("workout_plans")}
    assert {"id", "user_id", "created_at", "content", "focus"} <= cols

def test_insert_profile(engine):
    Session = sessionmaker(bind=engine)
    db = Session()
    p = UserProfile(name="Pedro", age=21, weight_kg=75.0, height_cm=178.0,
                    goal="ganhar massa", dietary_restrictions="", fitness_level="intermediário",
                    sex="masculino", available_equipment="")
    db.add(p)
    db.commit()
    assert p.id == 1
    db.close()
