from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, JSON
from app.database import Base, SessionLocal, get_db


class UserProfile(Base):
    __tablename__ = "UsersInfo"

    id = Column(Integer, primary_key=True, index=True)
    Name = Column(String, unique=True, index=True)
    Email = Column(String, index=True)
    Contact_number = Column(String, index=True)
    College = Column(String, index=True)
    Skills = Column(String, index=True)
    extra_info = Column(JSON)


class Documents(Base):
    __tablename__ = "documents"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer,  ForeignKey("UsersInfo.id"), unique=True,
                     index=True, nullable=False)
    # "resume", "aadhar", "birth_certificate"
    docs = Column(JSON)
