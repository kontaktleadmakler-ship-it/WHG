from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(prefix="/api/notifications", tags=["Benachrichtigungen"])


@router.get("/settings", response_model=schemas.NotificationSettingsOut)
def get_settings(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    return current_user.notification_settings


@router.put("/settings", response_model=schemas.NotificationSettingsOut)
def update_settings(
    payload: schemas.NotificationSettingsUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings_row = current_user.notification_settings
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(settings_row, key, value)
    db.commit()
    db.refresh(settings_row)
    return settings_row
