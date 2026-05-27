from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import UserProfile, DietPlan
from schemas import GenerateDietRequest, DietPlanOut
from services.claude_service import generate_diet_plan
from services.usda_service import search_foods

router = APIRouter(prefix="/diet", tags=["diet"])

@router.post("/generate", response_model=DietPlanOut)
async def generate(req: GenerateDietRequest, db: Session = Depends(get_db)):
    profile = db.get(UserProfile, req.user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

    foods = await search_foods(profile.goal, max_results=10)
    content = await generate_diet_plan(
        profile=profile.to_dict(),
        foods_context=foods,
        days=req.days,
        meals_per_day=req.meals_per_day,
    )

    plan = DietPlan(
        user_id=profile.id,
        content=content,
        calories_target=_estimate_calories(
            profile.weight_kg, profile.height_cm, profile.age, profile.sex, profile.goal
        ),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan

@router.get("/history/{user_id}", response_model=list[DietPlanOut])
def get_history(user_id: int, db: Session = Depends(get_db)):
    return (
        db.query(DietPlan)
        .filter(DietPlan.user_id == user_id)
        .order_by(DietPlan.created_at.desc())
        .all()
    )

@router.get("/{plan_id}", response_model=DietPlanOut)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = db.get(DietPlan, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    return plan

def _estimate_calories(weight_kg: float, height_cm: float, age: int, sex: str, goal: str) -> int:
    # Mifflin-St Jeor com multiplicador de atividade moderada (1.55)
    if sex.lower() in ("masculino", "male", "m"):
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    tdee = int(bmr * 1.55)
    goal_lower = goal.lower()
    if any(w in goal_lower for w in ["massa", "ganhar", "bulking", "hipertrofia"]):
        return tdee + 400
    if any(w in goal_lower for w in ["emagrecer", "perder", "cutting", "secar"]):
        return tdee - 400
    return tdee
