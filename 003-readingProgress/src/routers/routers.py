from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import EmailStr
from ..db import  SessionDep
from ..schemas.schemas import 
from uuid import UUID, uuid4
from typing import Annotated
from sqlmodel import select
import pika


router = APIRouter(
    tags=["profiles"],
    prefix="/profiles"
)

def decode_token(token: Annotated[str, Depends(oauth2_scheme)], db: SessionDep):
    data = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    user  = db.exec(select(ProfileSQL).where(ProfileSQL.username == data.get("sub"))).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid username or password")
    return user

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: SessionDep) -> CurrentUser:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user = decode_token(token, db)
    except InvalidTokenError:
        raise credentials_exception
    user_db  =  db.exec(select(ProfileSQL).where(ProfileSQL.username == user.username)).first()
    current_user = CurrentUser(username=user_db.username, email = user_db.email, avatar_url = user_db.avatar_url, id = user_db.id)
    return current_user

@router.post("/start-reading", response_model=readingProgress)
async def start_reading(db: SessionDep, current_user: Annotated[BaseProfile, book_id, Depends(get_current_user)]):
    new_progress = readingProgress(
        profile_id=current_user.id,
        book_id=book_id,
        readingProgress=0,
        status="reading"
    )
    db.add(new_progress)
    db.commit()
    db.refresh(new_progress)
    #send event to queue
    return new_progress

@router.patch("/update-progress/{book_id}", response_model=readingProgress)
async def update_progress(
    book_id: str,
    progress: int = Query(..., ge=0, le=100),
    db: SessionDep = Depends(),
    current_user: Annotated[BaseProfile, Depends(get_current_user)]
):
    reading_record = db.exec(
        select(readingProgress).where(
            (readingProgress.profile_id == current_user.id) & 
            (readingProgress.book_id == book_id)
        )
    ).first()

    if not reading_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reading record not found")

    reading_record.readingProgress = progress
    reading_record.updated_at = datetime.utcnow()

    if progress == 100:
        reading_record.status = "completed"
        #send event to queue
    else:
        reading_record.status = "reading"
        #send event to queue

    db.add(reading_record)
    db.commit()
    db.refresh(reading_record)
    return reading_record

@router.get("/progress/{book_id}", response_model=readingProgress)
async def get_reading_progress(
    book_id: str,
    db: SessionDep = Depends(),
    current_user: Annotated[BaseProfile, Depends(get_current_user)]
):
    reading_record = db.exec(
        select(readingProgress).where(
            (readingProgress.profile_id == current_user.id) & 
            (readingProgress.book_id == book_id)
        )
    ).first()

    if not reading_record:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reading record not found")

    return reading_record

