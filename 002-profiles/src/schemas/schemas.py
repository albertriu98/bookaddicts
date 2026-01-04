from pydantic import EmailStr, HttpUrl, BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, Session, SQLModel, create_engine, select


class BaseProfile(SQLModel):
    username: str =Field(..., max_length=30, index=True, primary_key=True)
    email: EmailStr
    avatar_url: Optional[HttpUrl] = None

class ProfileSQL(BaseProfile, table=True):
    __tablename__ = "profiles"
    
    #id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    password: str = Field(..., min_length=8)
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    fav_genre: Optional[str] = None

class ProfileCreate(BaseProfile):
    password: str =Field(..., min_length=8)
    fav_genre: Optional[str] = None

class ProfileOut(BaseProfile):
    bio: Optional[str] = None
    fav_genre: Optional[str] = None
    id: UUID

class CurrentUser(BaseProfile):
    id: UUID = Field(default_factory=uuid4)

class Token(BaseModel):
    access_token: str
    token_type: str