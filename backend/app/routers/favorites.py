from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/api/favorites", tags=["Favoriten"])


@router.get("", response_model=List[schemas.FavoriteOut])
def list_favorites(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return (
        db.query(models.Favorite)
        .options(joinedload(models.Favorite.listing))
        .filter(models.Favorite.user_id == current_user.id)
        .all()
    )


@router.post("", response_model=schemas.FavoriteOut, status_code=201)
def add_favorite(
    payload: schemas.FavoriteCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = db.query(models.Listing).filter(models.Listing.id == payload.listing_id).first()
    if not listing:
        raise HTTPException(404, "Angebot nicht gefunden.")

    existing = (
        db.query(models.Favorite)
        .filter(models.Favorite.user_id == current_user.id, models.Favorite.listing_id == payload.listing_id)
        .first()
    )
    if existing:
        raise HTTPException(400, "Bereits als Favorit gespeichert.")

    favorite = models.Favorite(user_id=current_user.id, listing_id=payload.listing_id, note=payload.note)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


@router.delete("/{favorite_id}", status_code=204)
def remove_favorite(
    favorite_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favorite = (
        db.query(models.Favorite)
        .filter(models.Favorite.id == favorite_id, models.Favorite.user_id == current_user.id)
        .first()
    )
    if not favorite:
        raise HTTPException(404, "Favorit nicht gefunden.")
    db.delete(favorite)
    db.commit()
