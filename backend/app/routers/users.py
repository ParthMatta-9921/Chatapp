from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.security import OAuth2PasswordBearer


from app.database import get_db
from app.models import User
from app.schemas import UserResponse
from app.utils.auth import Token as tokenmanager
from typing import List



router = APIRouter(prefix="/users", tags=["Users"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = tokenmanager.decode_token(token)
        user_id: int = int(payload.get("sub"))

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token payload.")

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found.")

        return user

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Could not validate credentials: {str(e)}")







# 1. Get Current User's Profile
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


# 2. Search for Users by Partial Username Match
@router.get("/search", response_model=List[UserResponse])
async def search_users(
    username: str = Query(..., min_length=1),
    limit: int = 10,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    stmt = select(User).where(User.username.ilike(f"%{username}%")).limit(limit).offset(offset)
    result = await db.execute(stmt)
    users = result.scalars().all()

    if not users:
        raise HTTPException(status_code=404, detail="No users found")
    return users


# 3. Get Public Profile of Another User by Exact Username
@router.get("/{username}", response_model=UserResponse)
async def get_user_by_username(username: str, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.username == username)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

#deleetew illbe added later