from datetime import datetime
from typing import Literal
from pydantic import BaseModel

class UserProfileCreate(BaseModel):
    name: str
    age: int
    weight_kg: float
    height_cm: float
    goal: str
    dietary_restrictions: str = ""
    fitness_level: Literal["iniciante", "intermediário", "avançado"]
    sex: str = "masculino"
    available_equipment: str = ""

class UserProfileOut(UserProfileCreate):
    id: int
    model_config = {"from_attributes": True}

class DietPlanOut(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    content: str
    calories_target: int
    model_config = {"from_attributes": True}

class WorkoutPlanOut(BaseModel):
    id: int
    user_id: int
    created_at: datetime
    content: str
    focus: str
    model_config = {"from_attributes": True}

class GenerateDietRequest(BaseModel):
    user_id: int
    days: int = 7
    meals_per_day: int = 4

class GenerateWorkoutRequest(BaseModel):
    user_id: int
    days_per_week: int = 4
    focus: str = ""
