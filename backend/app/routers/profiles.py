from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/api/profiles", tags=["Suchprofile"])


@router.get("", response_model=List[schemas.SearchProfileOut])
def list_profiles(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return db.query(models.SearchProfile).filter(models.SearchProfile.user_id == current_user.id).all()


@router.post("", response_model=schemas.SearchProfileOut, status_code=201)
def create_profile(
    payload: schemas.SearchProfileCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = models.SearchProfile(user_id=current_user.id, **payload.model_dump())
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.put("/{profile_id}", response_model=schemas.SearchProfileOut)
def update_profile(
    profile_id: str,
    payload: schemas.SearchProfileCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(models.SearchProfile)
        .filter(models.SearchProfile.id == profile_id, models.SearchProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise HTTPException(404, "Suchprofil nicht gefunden.")
    for key, value in payload.model_dump().items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/{profile_id}", status_code=204)
def delete_profile(
    profile_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(models.SearchProfile)
        .filter(models.SearchProfile.id == profile_id, models.SearchProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        raise HTTPException(404, "Suchprofil nicht gefunden.")
    db.delete(profile)
    db.commit()
