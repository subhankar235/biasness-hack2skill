import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import jwt

from app.config import settings
from app.db.models import User, Org
from app.dependencies import get_db

router = APIRouter(prefix="/auth", tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class Token(BaseModel):
    access_token: str
    token_type: str


class UserCreate(BaseModel):
    email: str
    password: str
    org_name: str = "Default Org"


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalar_one_or_none()
    
    if not user or user.hashed_password != form_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    
    expires = datetime.utcnow() + timedelta(hours=24)
    payload = {"sub": str(user.id), "exp": expires}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return Token(access_token=token, token_type="bearer")


@router.post("/register", response_model=Token)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    org = Org(
        id=str(uuid.uuid4()),
        name=user_data.org_name,
        slug=f"org-{uuid.uuid4().hex[:8]}",
    )
    db.add(org)
    await db.commit()
    
    user = User(
        id=str(uuid.uuid4()),
        org_id=org.id,
        email=user_data.email,
        hashed_password=user_data.password,
    )
    db.add(user)
    await db.commit()
    
    expires = datetime.utcnow() + timedelta(hours=24)
    payload = {"sub": str(user.id), "exp": expires}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return Token(access_token=token, token_type="bearer")