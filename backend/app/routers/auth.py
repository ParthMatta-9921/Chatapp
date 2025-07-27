from fastapi import APIRouter,Depends,HTTPException,status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from datetime import datetime,timezone
from sqlalchemy.future import select


from app.schemas import UserCreate,UserLogin,UserResponse,Token
from app.models import User
from app.database import get_db
from app.utils.auth import Hasher,Token as Tmanager
'''Note for future implementation:

    Implement refresh token storage and blacklisting in PostgreSQL database instead of in-memory Python set.

    Add RefreshToken model in models.py to track issued refresh tokens and their revoked status.

    Update login, refresh, and logout routes to interact with database for token validation and revocation.

    This will enable persistence across server restarts and multi-instance deployments, improving security and scalability.'''




router=APIRouter(prefix="/auth",tags=["Auth"])

"""# For token blacklisting in-memory (replace with DB in production)
blacklisted_tokens = set()"""


# SIGNUP ROUTE


@router.post("/signup",response_model=UserResponse,status_code=status.HTTP_201_CREATED)
async def signup( user_data: UserCreate, db: AsyncSession= Depends( get_db)):
    ''' Registers a new user and generates tokens.
    '''
    try:

        result=await db.execute(select(User).where(User.username ==user_data.username))
        existing_user=result.scalar_one_or_none()# gives if result empty or not so used for duplicate usernames
        if existing_user:# so 1 means there is existing username
            raise HTTPException(status_code=400,detail="Username already taken.")
        
        result= await db.execute(select(User).where(User.email == user_data.email))
        existing_email=result.scalar_one_or_none()
        if existing_email:#already exists email
            raise HTTPException(status_code=400,detail="Email already registered. ")
        


        # HASHING THE PASSWORD HERE
        hashed_password=Hasher.hash_password(user_data.password)

        # Create a new user object
        new_user=User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            created_at=datetime.now(timezone.utc),
            is_online=False,
           # is_active=True
           # # add lastseen too adter adding in models
        )
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        # Return the response in the expected format
        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            email=new_user.email,
            is_online=new_user.is_online,
            created_at=new_user.created_at,
        )# or juts new_user
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=500,detail="Database Integrity error")
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500,detail=str(e))
    




#LOGIN ROUTE
@router.post("/login")# return dict instead of TokenResponse model to avoid mismatch
async def login(credentials:UserLogin, db: AsyncSession= Depends(get_db)):
    """
    Logs in an existing user and generates new tokens."""
    try:
        result = await db.execute(select(User).where(User.email == credentials.email))
        user = result.scalar_one_or_none()

        if not user or not Hasher.verify_password(credentials.password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid email or password.")

        access_token = Tmanager.create_access_token({"sub": str(user.id), "username": user.username})
        refresh_token = Tmanager.create_refresh_token({"sub": str(user.id), "username": user.username})

        user.is_online = True
        await db.commit()
        await db.refresh(user)
    # Return tokens in JSON
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Login error: {str(e)}")



#REFRESH TOKENS ROUTE
@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str, db: AsyncSession = Depends(get_db)):
    """
        Refreshes an access token using a valid refresh token.
        """
    try:
        payload = Tmanager.verify_refresh_token(refresh_token)
        user_id = payload.get("sub")
        username = payload.get("username")

        if not user_id or not username:
            raise HTTPException(status_code=401, detail="Invalid refresh token.")
        #Optionally verify user still exists and is active
        result = await db.execute(select(User).where(User.id == int(user_id)))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found.")

        new_access_token = Tmanager.create_access_token(
            {"sub": user_id, "username": username}
        )
        new_refresh_token = Tmanager.create_refresh_token(
            {"sub": user_id, "username": username}
        )

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Refresh token invalid: {str(e)}")



#LOGOUT ROUTE
'''
@router.post("/logout")
async def logout(
    response: Response,
    access_token: Optional[str] = Cookie(None),
    refresh_token: Optional[str] = Cookie(None),
):
    # Blacklist tokens if they exist
    if access_token:
        blacklisted_tokens.add(access_token)
    if refresh_token:
        blacklisted_tokens.add(refresh_token)

    # Clear cookies on client
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")

    return {"detail": "Successfully logged out."}'''