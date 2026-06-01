import asyncio
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_user
from models import UserProfile, WorkoutPlan
from schemas import GenerateWorkoutRequest, WorkoutPlanOut
from services.claude_service import generate_workout_plan
from services.exercise_service import search_exercises, VALID_BODY_PARTS

router = APIRouter(prefix="/workout", tags=["workout"])

@router.post("/generate", response_model=WorkoutPlanOut)
async def generate(
    req: GenerateWorkoutRequest,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.supabase_user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")

    results = await asyncio.gather(
        *[search_exercises(part, limit=3) for part in VALID_BODY_PARTS[:6]]
    )
    exercises: list[dict] = [ex for sublist in results for ex in sublist]

    effective_focus = req.focus or profile.goal
    content = await generate_workout_plan(
        profile=profile.to_dict(),
        exercises_context=exercises,
        days_per_week=req.days_per_week,
        focus=effective_focus,
    )

    plan = WorkoutPlan(user_id=profile.id, content=content, focus=effective_focus)
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan

@router.get("/history", response_model=list[WorkoutPlanOut])
def get_history(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.supabase_user_id == user_id).first()
    if not profile:
        return []
    return (
        db.query(WorkoutPlan)
        .filter(WorkoutPlan.user_id == profile.id)
        .order_by(WorkoutPlan.created_at.desc())
        .all()
    )

@router.get("/{plan_id}", response_model=WorkoutPlanOut)
def get_plan(
    plan_id: int,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.supabase_user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    plan = db.query(WorkoutPlan).filter(
        WorkoutPlan.id == plan_id, WorkoutPlan.user_id == profile.id
    ).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")
    return plan
