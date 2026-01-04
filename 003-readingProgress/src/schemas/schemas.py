from pydantic import EmailStr, HttpUrl, BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4
from sqlmodel import Field, Session, SQLModel, create_engine, select

class readingProgress(SQLModel, table=True):
    __tablename__ = "reading_progress"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    profile_id: UUID = Field(default_factory=uuid4, index=True) 
    book_id: str = Field(index=True)
    readingProgress: int = Field(..., ge=0, le=100, default=0)  # percentage from 0 to 100
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status : str = Field(default="reading")  # e.g., reading, completed