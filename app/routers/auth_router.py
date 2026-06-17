from datetime import timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.models.config import get_config
from app.models.database import get_db
from app.models.schemas import UserRegisterRequest, UserLoginRequest, TokenResponse, UserPublic
from app.services.auth_service import create_user, authenticate_user, create_access_token

config = get_config()
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, summary="Register a new user")
def register(req: UserRegisterRequest, db: Session = Depends(get_db)):
    user = create_user(db, req)
    token = create_access_token(
        {"sub": str(user.id)},
        timedelta(minutes=config.access_token_expire_minutes),
    )
    return TokenResponse(
        access_token=token,
        expires_in=config.access_token_expire_minutes * 60,
        user=UserPublic.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse, summary="Login and receive JWT token")
def login(req: UserLoginRequest, db: Session = Depends(get_db)):
    user = authenticate_user(db, req.email, req.password)
    token = create_access_token(
        {"sub": str(user.id)},
        timedelta(minutes=config.access_token_expire_minutes),
    )
    return TokenResponse(
        access_token=token,
        expires_in=config.access_token_expire_minutes * 60,
        user=UserPublic.model_validate(user),
    )


@router.get("/me", response_model=UserPublic, summary="Get current user profile")
def me(
    db: Session = Depends(get_db),
    current_user=Depends(__import__("app.middleware.auth_dep", fromlist=["get_authenticated_user"]).get_authenticated_user),
):
    return UserPublic.model_validate(current_user)
