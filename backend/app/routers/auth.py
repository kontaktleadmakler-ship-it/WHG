from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import create_access_token, hash_password, verify_password, get_current_user
from app.database import get_db

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=schemas.UserOut, status_code=201)
def register(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    if not payload.accept_privacy_policy:
        raise HTTPException(400, "Zustimmung zur Datenschutzerklärung ist erforderlich.")

    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(400, "E-Mail-Adresse bereits registriert.")

    user = models.User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        marketing_opt_in=payload.marketing_opt_in,
        consent_given_at=datetime.utcnow(),
    )
    db.add(user)
    db.flush()

    # Standard-Benachrichtigungseinstellungen anlegen
    db.add(models.NotificationSettings(user_id=user.id))
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "E-Mail oder Passwort falsch.")
    token = create_access_token(subject=user.id)
    return schemas.Token(access_token=token)


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user


@router.delete("/me", status_code=204)
def delete_account(
    current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """DSGVO Art. 17 - Recht auf Löschung."""
    db.delete(current_user)
    db.commit()
