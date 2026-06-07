import json
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_user
from models import UserProfile, DietPlan
from schemas import GenerateDietRequest, DietPlanOut
from services.claude_service import generate_diet_plan, generate_diet_plan_stream
from services.usda_service import search_foods

router = APIRouter(prefix="/diet", tags=["diet"])


@router.post("/generate")
async def generate(
    req: GenerateDietRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.supabase_user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

    foods = await search_foods(profile.goal, max_results=10)
    calories = _estimate_calories(profile.weight_kg, profile.height_cm, profile.age, profile.sex, profile.goal)

    async def stream():
        content = None
        try:
            async for chunk in generate_diet_plan_stream(
                profile=profile.to_dict(),
                foods_context=foods,
                days=req.days,
                meals_per_day=req.meals_per_day,
            ):
                msg = json.loads(chunk)
                yield f"data: {chunk}\n\n"
                if msg["type"] == "done":
                    content = msg["content"]

            plan = DietPlan(user_id=profile.id, content=content, calories_target=calories)
            db.add(plan)
            db.commit()
            db.refresh(plan)
            yield f"data: {json.dumps({'type': 'saved', 'id': plan.id, 'content': content, 'calories_target': plan.calories_target})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)[:300]})}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/history", response_model=list[DietPlanOut])
def get_history(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.supabase_user_id == user_id).first()
    if not profile:
        return []
    return (
        db.query(DietPlan)
        .filter(DietPlan.user_id == profile.id)
        .order_by(DietPlan.created_at.desc())
        .all()
    )


@router.get("/{plan_id}", response_model=DietPlanOut)
def get_plan(
    plan_id: int,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.supabase_user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    plan = db.query(DietPlan).filter(
        DietPlan.id == plan_id, DietPlan.user_id == profile.id
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    return plan


def _estimate_calories(weight_kg: float, height_cm: float, age: int, sex: str, goal: str) -> int:
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
