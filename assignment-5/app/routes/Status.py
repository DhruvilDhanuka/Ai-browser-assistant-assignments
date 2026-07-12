from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Depends, FastAPI, Body, Header, HTTPException, status, APIRouter
from app.schemas import StatusTask
from app.database import Base, SessionLocal, get_db
from app.routes.commands import Command

router = APIRouter(prefix="/status", tags=["task_statuses"])


@router.get("/{task_id}")
def get_task_status(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Command).filter(Command.task_id == task_id).first()

    if not task:
        raise HTTPException(status_code=404, detail="TASK NOT FOUND")
    return task.status
