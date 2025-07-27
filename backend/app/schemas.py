from pydantic import BaseModel,Field,EmailStr,field_validator
from datetime import datetime
from re import search
from enum import Enum
from typing import Optional, Literal

class FriendshipStatus(str, Enum):
    pending = "pending"
    accepted = "accepted"
    declined = "declined"

#------------------
#user schemas

#user creation schema
class UserCreate(BaseModel):
    username: str =Field(...,min_length=4,max_length=10,description="Username must be between 4 and 10 characters.")
    email: EmailStr=Field(...,description="Valid Email Address.")
    password: str= Field(..., description="Password must be at least 8 characters,contain 1 uppercase,lowercase,number and a special character.")
    # hash the password in utils/auth.py before saving usercreate to db

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        allowed_domains = { # only using domains that majority of them use willl try to chaneg so that other domains can also be there
            "gmail.com",
            "yahoo.com",
            "outlook.com",
            "hotmail.com",
            "icloud.com",
            "aol.com"
        }
        domain = value.split("@")[-1].lower()
        if domain not in allowed_domains:
            raise ValueError(f"Email domain '{domain}' is not allowed. Please use a major email provider like Gmail, Yahoo, Outlook, etc.")
        return value
    

    @field_validator("password")
    @classmethod
    def validate_password(cls, value:str) -> str:
        if(len(value)<8):
            raise ValueError("Password must be atleast 8 characters long.")
        if not search(r"[A-Z]",value):
            raise ValueError("Password must contain at least one uppercase letter.")
        if not search(r"[a-z]", value):
            raise ValueError("Password must contain at least one lowercase letter.")
        if not search(r"[0-9]", value):
            raise ValueError("Password must contain at least one digit.")
        if not search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise ValueError("Password must contain at least one special character.")
        return value


#User login schema
class UserLogin(BaseModel):
    email: EmailStr = Field(..., description="Valid email address.")
    password: str = Field(..., min_length=6, description="Password must be at least 8 characters,contain 1 uppercase,lowercase,number and a special character.")

class UserResponse(BaseModel):
    id:int
    username:str
    email:EmailStr
    is_online:bool
    created_at:datetime

    model_config={"from_attributes" :True}



#---------------------
# Friendship schema
class FriendshipResponse(BaseModel):
    id: int
    user: UserResponse
    friend: UserResponse
    status: FriendshipStatus
    created_at: datetime

    model_config={"from_attributes": True}


class FriendshipCreate(BaseModel):
    receiver_id: int  # ID of the user being sent the request


class FriendshipRespond(BaseModel):
    sender_id: int
    action: str  # accept or reject

class FriendshipOut(BaseModel):
    id: int
    sender_id: int
    receiver_id: int
    status: Literal["pending", "accepted", "declined"]
    created_at: datetime


# -------------------------------
# Message Schemas

#message creation schema    
class MessageCreate(BaseModel):
    receiver_id: int
    content: str=Field(...,max_length=1000,description="message cannot extend 1000 characters.")

# Message response schema
class MessageResponse(BaseModel):
    id: int
    sender: UserResponse
    content: str
    timestamp: datetime
    model_config={"from_attributes": True}



#-----------------
# token schemas
class Token(BaseModel):
    access_token: str
    refresh_token:str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[int] = None