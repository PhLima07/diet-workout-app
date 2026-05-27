from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import UserProfile
from schemas import UserProfileCreate, UserProfileOut

router = APIRouter(prefix="/profile", tags=["profile"])

@router.post("/", response_model=UserProfileOut)
def create_profile(data: UserProfileCreate, db: Session = Depends(get_db)):
    profile = UserProfile(**data.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

@router.get("/{profile_id}", response_model=UserProfileOut)
def get_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.get(UserProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    return profile

@router.put("/{profile_id}", response_model=UserProfileOut)
def update_profile(profile_id: int, data: UserProfileCreate, db: Session = Depends(get_db)):
    profile = db.get(UserProfile, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil não encontrado")
    for key, value in data.model_dump().items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile
