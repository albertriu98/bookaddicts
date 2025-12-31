
from sqlmodel import Field, Session, SQLModel, create_engine, select
from typing import Optional
from pydantic import EmailStr, HttpUrl

class BaseBook(SQLModel):
    title: str
    author: list  | None
    thumbnail: Optional[str] = None
    identifier : str

class Book(BaseBook):
    description: str 
    published_year: str
