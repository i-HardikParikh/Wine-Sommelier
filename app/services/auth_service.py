from datetime import datetime, timedelta
from typing import Optional

try:
    import bcrypt
    _original_hashpw = bcrypt.hashpw
    bcrypt.hashpw = lambda p, s: _original_hashpw(p[:72], s) if len(p) > 72 else _original_hashpw(p, s)
except ImportError:
    pass

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.config import get_config
from app.models.db_models import User
from app.models.schemas import UserRegisterRequest

config = get_config()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


# ─── Password Utilities ──────────────────────────────────────────────────────

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# ─── JWT Utilities ───────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=config.access_token_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, config.jwt_secret_key, algorithm=config.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, config.jwt_secret_key, algorithms=[config.jwt_algorithm])
        return payload
    except JWTError:
        raise CREDENTIALS_EXCEPTION


# ─── User CRUD ───────────────────────────────────────────────────────────────

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, req: UserRegisterRequest) -> User:
    if get_user_by_email(db, req.email):
        raise HTTPException(status_code=400, detail="Email already registered.")
    user = User(
        email=req.email,
        full_name=req.full_name,
        hashed_password=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> User:
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user.")
    return user


def get_current_user(token: str, db: Session) -> User:
    payload = decode_token(token)
    user_id: int = payload.get("sub")
    if user_id is None:
        raise CREDENTIALS_EXCEPTION
    user = get_user_by_id(db, int(user_id))
    if user is None:
        raise CREDENTIALS_EXCEPTION
    return user
