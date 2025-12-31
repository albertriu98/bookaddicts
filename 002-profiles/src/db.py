import os
from sqlmodel import Field, Session, SQLModel, create_engine, select
from typing import Annotated
from fastapi import Depends

user = os.getenv("POSTGRESQL_USER")
password = os.getenv("POSTGRESQL_PASSWORD")
address = os.getenv("POSTGRESQL_ADDRESS")
database = os.getenv("POSTGRESQL_DATABASE_NAME")

SQLALCHEMY_DATABASE_URL = f"postgresql://{user}:{password}@{address}:5432/{database}"


connect_args = {"check_same_thread": False}
engine = create_engine(SQLALCHEMY_DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]
