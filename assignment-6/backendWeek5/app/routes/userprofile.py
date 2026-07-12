from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Depends, FastAPI, Body, Header, HTTPException, status, APIRouter
from app.schemas import UserProfileCreate, UserProfileResponse
from app.database import Base, SessionLocal, get_db


router = APIRouter(prefix="/user/profile", tags=["user_profile"])


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String, index=True)
    phone_number = Column(String, index=True)
    resume_text = Column(String, index=True)


@router.post("/", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
def create_user_profile(user_profile: UserProfileCreate, db: Session = Depends(get_db)):

    if db.query(UserProfile).filter(UserProfile.email == user_profile.email).first():
        raise HTTPException(status_code=400, detail="EMAIL ALREADY EXISTS")

    new_user = UserProfile(**user_profile.dict())

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.get("/{user_id}", response_model=UserProfileResponse)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    user_profile = db.query(UserProfile).filter(
        UserProfile.id == user_id).first()

    if not user_profile:
        raise HTTPException(status_code=404, detail="USER NOT FOUND")
    return user_profile
