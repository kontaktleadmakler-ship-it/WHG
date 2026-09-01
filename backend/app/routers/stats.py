from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/api/stats", tags=["Statistiken"])


@router.get("/market", response_model=schemas.MarketStats)
def market_stats(
    city: str,
    district: Optional[str] = None,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    history_query = db.query(models.PriceHistory).filter(models.PriceHistory.city.ilike(city))
    if district:
        history_query = history_query.filter(models.PriceHistory.district.ilike(district))
    history = history_query.order_by(models.PriceHistory.date.asc()).all()

    listing_query = db.query(models.Listing).filter(
        models.Listing.city.ilike(city), models.Listing.is_active.is_(True)
    )
    if district:
        listing_query = listing_query.filter(models.Listing.district.ilike(district))

    current_avg = listing_query.with_entities(func.avg(models.Listing.price_per_sqm)).scalar() or 0
    current_count = listing_query.count()

    return schemas.MarketStats(
        city=city,
        district=district,
        history=[
            schemas.PriceStatPoint(
                date=h.date, avg_price_per_sqm=h.avg_price_per_sqm, listing_count=h.listing_count
            )
            for h in history
        ],
        current_avg_price_per_sqm=round(current_avg, 2),
        current_listing_count=current_count,
    )


@router.get("/density")
def offer_density(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Anzahl aktiver Angebote pro Stadt (für Angebotsdichte-Diagramme)."""
    rows = (
        db.query(models.Listing.city, func.count(models.Listing.id))
        .filter(models.Listing.is_active.is_(True))
        .group_by(models.Listing.city)
        .all()
    )
    return [{"city": city, "count": count} for city, count in rows if city]
