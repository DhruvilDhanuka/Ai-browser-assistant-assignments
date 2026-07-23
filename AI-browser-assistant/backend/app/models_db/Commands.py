from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, JSON, Enum as SQLEnum
from app.database import Base, SessionLocal, get_db
from enum import Enum
from app.models_db.UserProfile import UserProfile
from app.schemasPydantic.schemas import StatusTask


class Commands(Base):

    __tablename__ = "commandsAndStatuses"

    user_id = Column(Integer, ForeignKey("UsersInfo.id"), index=True)
    task_id = Column(Integer, primary_key=True, index=True)
    command = Column(String, index=True)
    status = Column(JSON, default=list)
