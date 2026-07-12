import asyncio

from sqlalchemy import create_engine, Column, Integer, String, Enum
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Depends, FastAPI, Body, Header, HTTPException, WebSocketDisconnect, status, APIRouter, BackgroundTasks, WebSocket
from app.schemas import UserCommandCreate, StatusTask
from app.database import Base, SessionLocal, get_db
from app.langchain_agent import BrowserAgent

router = APIRouter(prefix="/commands", tags=["commands"])

langchain_agent = BrowserAgent()


class Command(Base):

    __tablename__ = "commandsAndStatuses"

    task_id = Column(Integer, primary_key=True, index=True)
    command = Column(String, index=True)
    status = Column(Enum(StatusTask), index=True)


@router.websocket("/ws/{task_id}")
async def websocket_status(websocket: WebSocket, task_id: int):
    await websocket.accept()
    db = SessionLocal()
    try:
        while True:
            db.expire_all()
            task = db.query(Command).filter(Command.task_id == task_id).first()
            if not task:
                await websocket.send_text("Task not found")
                break

            await websocket.send_text(task.status.value)

            if task.status in (StatusTask.COMPLETED, StatusTask.FAILED):
                break  # nothing more will change, close the loop

            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    finally:
        db.close()


def run_agent_task(task_id: int, command_text: str):
    db = SessionLocal()

    try:
        db.query(Command).filter(Command.task_id == task_id).update(
            {"status": StatusTask.IN_PROGRESS})
        db.commit()

        result = langchain_agent.run(command_text)

        db.query(Command).filter(Command.task_id == task_id).update(
            {"status": StatusTask.COMPLETED})
        db.commit()

    except:
        db.query(Command).filter(Command.task_id == task_id).update(
            {"status": StatusTask.FAILED})
        db.commit()
    finally:
        db.close()


@router.post("/")
def create_command(command: UserCommandCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_command = Command(
        command=command.command,
        status=StatusTask.PENDING
    )

    db.add(db_command)
    db.commit()
    db.refresh(db_command)
    background_tasks.add_task(
        run_agent_task, db_command.task_id, command.command)

    return {"task_id": db_command.task_id}
