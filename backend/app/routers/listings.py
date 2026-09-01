from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/api/listings", tags=["Angebote & Matches"])


@router.get("/matches", response_model=List[schemas.MatchOut])
def get_matches(
    profile_id: Optional[str] = None,
    min_score: float = Query(0, ge=0, le=100),
    sort_by: str = Query("score", pattern="^(score|price|size|date)$"),
    order: str = Query("desc", pattern="^(asc|desc)$"),
    city: Optional[str] = None,
    max_price: Optional[float] = None,
    min_size: Optional[float] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(models.Match)
        .join(models.SearchProfile)
        .join(models.Listing)
        .options(joinedload(models.Match.listing))
        .filter(models.SearchProfile.user_id == current_user.id)
        .filter(models.Match.score >= min_score)
    )
    if profile_id:
        query = query.filter(models.Match.profile_id == profile_id)
    if city:
        query = query.filter(models.Listing.city.ilike(f"%{city}%"))
    if max_price:
        query = query.filter(models.Listing.price_total <= max_price)
    if min_size:
        query = query.filter(models.Listing.size_sqm >= min_size)

    sort_column = {
        "score": models.Match.score,
        "price": models.Listing.price_total,
        "size": models.Listing.size_sqm,
        "date": models.Listing.first_seen_at,
    }[sort_by]
    query = query.order_by(sort_column.desc() if order == "desc" else sort_column.asc())

    return query.limit(200).all()


@router.get("/{listing_id}", response_model=schemas.ListingOut)
def get_listing_detail(
    listing_id: str,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    listing = db.query(models.Listing).filter(models.Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(404, "Angebot nicht gefunden.")
    return listing
