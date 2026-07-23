from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, func, JSON
from app.database import Base, SessionLocal, get_db
from app.models_db.UserProfile import UserProfile


class GmailCredentials(Base):
    __tablename__ = "gmail_credentials"

    id = Column(Integer, unique=True, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("UsersInfo.id"),
                     unique=True, index=True, nullable=False)
    # the full token.json contents, as a string
    token_json = Column(String, nullable=False)
    updated_at = Column(DateTime(timezone=True),
                        server_default=func.now(), onupdate=func.now())


class ContactGroup(Base):
    __tablename__ = "contact_groups"

    id = Column(Integer, unique=True, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("UsersInfo.id"),
                     index=True, nullable=False)
    group_name_with_number = Column(
        JSON, nullable=False)  # ["a@x.com", "b@x.com"]
