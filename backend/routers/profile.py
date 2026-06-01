from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_user
from models import UserProfile
from schemas import UserProfileCreate, UserProfileOut

router = APIRouter(prefix="/profile", tags=["profile"])

@router.post("/", response_model=UserProfileOut)
def create_profile(
    data: UserProfileCreate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing = db.query(UserProfile).filter(UserProfile.supabase_user_id == user_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Perfil já existe para este usuário")
    profile = UserProfile(**data.model_dump(), supabase_user_id=user_id)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

@router.get("/me", response_model=UserProfileOut)
def get_profile(
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.supabase_user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    return profile

@router.put("/me", response_model=UserProfileOut)
def update_profile(
    data: UserProfileCreate,
    user_id: str = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = db.query(UserProfile).filter(UserProfile.supabase_user_id == user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    for key, value in data.model_dump().items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile
