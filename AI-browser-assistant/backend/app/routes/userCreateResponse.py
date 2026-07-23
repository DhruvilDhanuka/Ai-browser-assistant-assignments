from fastapi import Depends, FastAPI, Body, Header, HTTPException, WebSocketDisconnect, status, APIRouter, BackgroundTasks, WebSocket
from app.database import Base, SessionLocal, get_db
from app.schemasPydantic.schemas import UserProfileCreate, UserProfileResponse
from sqlalchemy.orm import sessionmaker, Session
from app.models_db.UserProfile import UserProfile


router = APIRouter(prefix="/users", tags=["commands"])


@router.post("/", response_model=UserProfileResponse)
def create_user(userProfile: UserProfileCreate, db: Session = Depends(get_db)):
    db_user = UserProfile(**userProfile.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
