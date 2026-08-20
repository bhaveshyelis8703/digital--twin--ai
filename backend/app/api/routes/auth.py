from datetime import datetime, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token, decode_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import Token, UserLogin, UserOut, UserRegister
from app.schemas.user import ProfileResponse

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(token)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    return user


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(user: UserRegister, db: Session = Depends(get_db)) -> UserOut:
    existing = db.query(User).filter(User.email == user.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    db_user = User(
        name=user.name,
        email=user.email.lower(),
        hashed_password=get_password_hash(user.password),
        age=user.age,
        occupation=user.occupation,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return UserOut.model_validate(db_user)


@router.post("/login", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: Session = Depends(get_db)) -> Token:
    user = db.query(User).filter(User.email == form_data.username.lower()).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    access_token = create_access_token(user.id)
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=ProfileResponse)
def get_current_user_profile(current_user: User = Depends(get_current_user)) -> ProfileResponse:
    return ProfileResponse.model_validate(current_user)
