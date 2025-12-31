from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import EmailStr
from ..db import  SessionDep
from ..schemas.schemas import ProfileCreate, ProfileOut, ProfileSQL, Token, BaseProfile, CurrentUser
from uuid import UUID, uuid4
from typing import Annotated
from sqlmodel import select
from pwdlib import PasswordHash
import jwt
from jwt.exceptions import InvalidTokenError
from datetime import datetime, timedelta, timezone


SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

password_hash = PasswordHash.recommended()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/profiles/token")


router = APIRouter(
    tags=["profiles"],
    prefix="/profiles"
)


#Get profile by username
@router.get("/username/{username}", response_model=ProfileOut)
async def get_profile(username: str, db : SessionDep): 
    profile = db.exec(select(ProfileSQL).where(ProfileSQL.username == username)).first()
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile

#Get ALL profiles
@router.get("/", response_model=list[ProfileOut])
async def get_profiles(db : SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100): 
    profiles = db.exec(select(ProfileSQL).offset(offset).limit(limit)).all()
    if profiles is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No profiles found")
    return profiles

#Create new profile
@router.post("/create", response_model=ProfileOut, status_code=status.HTTP_201_CREATED) 
async def create_profile(profile: ProfileCreate, db : SessionDep) :
    profile_sql = ProfileSQL(
        username=profile.username,
        email=profile.email,
        password=profile.password,
        avatar_url=str(profile.avatar_url) if profile.avatar_url else None,
        fav_genre=profile.fav_genre
    )
    hashed_password = get_password_hash(profile_sql.password)
    profile_sql.password = hashed_password

    db.add(profile_sql)
    db.commit()
    db.refresh(profile_sql)
    return profile_sql

#Update existing profile
@router.put("/update/{profile_id}", response_model=ProfileOut)
async def update_profile(profile_id: UUID, profile_update: ProfileCreate, db : SessionDep):
    profile = db.get(ProfileSQL, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile.username = profile_update.username
    profile.email = profile_update.email
    profile.password = profile_update.password
    profile.avatar_url = str(profile_update.avatar_url) if profile_update.avatar_url else None
    profile.fav_genre = profile_update.fav_genre

    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile

#Delete profile by ID
@router.delete("/delete/{profile_id}")
async def delete_profile(profile_id: UUID, db : SessionDep):    
    profile = db.get(ProfileSQL, profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    db.delete(profile)
    db.commit()
    return {"detail": "Profile deleted successfully"}

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def get_password_hash(password):
    return password_hash.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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

@router.post("/token")
async def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: SessionDep) -> Token:
    user = db.exec(select(ProfileSQL).where(ProfileSQL.username == form_data.username)).first()
    print(user)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    print(verify_password(form_data.password, user.password))
    if not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect password")
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    print(access_token)
    return Token(access_token=access_token, token_type="bearer")

@router.get("/own_profile")
async def get_own_profile(db: SessionDep, current_user: Annotated[BaseProfile, Depends(get_current_user)]):
    user = db.exec(select(ProfileSQL).where(ProfileSQL.username == current_user.username)).first()
    return user


#Get profile by ID
@router.get("/{profile_id}", response_model=ProfileOut)
async def get_profile(profile_id: UUID, db : SessionDep): 
    profile = db.get(ProfileSQL, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    return profile