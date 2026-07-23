from app.AgentsForModules.pendingAnswers import submit_answer
from fastapi import Depends, FastAPI, Body, Header, Form, UploadFile, File, HTTPException, WebSocketDisconnect, status, APIRouter, BackgroundTasks, WebSocket
from app.database import Base, SessionLocal, get_db
from app.schemasPydantic.schemas import UserCommandCreate
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.orm.attributes import flag_modified
from app.models_db.Commands import Commands
from app.schemasPydantic.schemas import StatusTask
from app.AgentsForModules.topLevelModuleClassifier import load_modules as langchain_agent
from app.routes.resumeUpload import save_file_docs
import asyncio


router = APIRouter(prefix="/commands")


@router.websocket("/ws/{task_id}")
async def websocket_status(websocket: WebSocket, task_id: int):
    await websocket.accept()
    db = SessionLocal()
    last_sent_index = 0
    try:
        while True:
            db.expire_all()
            task = db.query(Commands).filter(
                Commands.task_id == task_id).first()
            if not task:
                await websocket.send_text("Task not found")
                break

            log = task.status or []
            for entry in log[last_sent_index:]:
                await websocket.send_text(entry)
            last_sent_index = len(log)

            if log and ("Task Completed" in log[-1] or "Task Failed" in log[-1]):
                break

            await asyncio.sleep(1)
    except WebSocketDisconnect:
        pass
    finally:
        db.close()


@router.post("/{task_id}/answer/file")
def answer_file_command(
    task_id: int,
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    task = db.query(Commands).filter(Commands.task_id == task_id).first()
    if task is None:
        raise HTTPException(404, "Task not found")

    doc_row = save_file_docs(db, task.user_id, doc_type, file)

    saved_entry = doc_row.docs[-1]  # the entry just appended by save_file_docs
    submit_answer(task_id, saved_entry["path"])

    return {"status": "file received", "path": saved_entry["path"]}


@router.post("/{task_id}/answer")
def answer_command(task_id: int, payload: dict = Body(...)):
    answer = payload.get("answer", "")
    success = submit_answer(task_id, answer)
    if not success:
        raise HTTPException(404, "No pending question for this task")
    return {"status": "answer received"}


def run_agent_task(task_id: int, command_text: str):
    db = SessionLocal()

    try:
        task = db.query(Commands).filter(
            Commands.task_id == task_id).first()
        current = task.status or []
        current.append("Task under processing ")
        task.status = current
        flag_modified(task, "status")
        db.commit()

        user_id = task.user_id

        result = langchain_agent(command_text, user_id, task_id)
        print(f"[DEBUG] langchain_agent returned: {result}")

        db.expire_all()
        task = db.query(Commands).filter(
            Commands.task_id == task_id).first()
        statusComplete = task.status or []
        statusComplete.append("Task Completed")
        task.status = statusComplete
        flag_modified(task, "status")
        db.commit()

    except Exception as e:

        db.expire_all()
        task = db.query(Commands).filter(
            Commands.task_id == task_id).first()
        statusFailed = task.status or []
        statusFailed.append("Task Failed")
        task.status = statusFailed
        flag_modified(task, "status")

        print(f"Task {task_id} failed: {e}")
        db.commit()

    finally:
        db.close()


@router.post("/")
def create_command(command: UserCommandCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    db_command = Commands(
        command=command.command,
        user_id=command.user_id,
        status=["Task pending "]
    )

    db.add(db_command)
    db.commit()
    db.refresh(db_command)
    background_tasks.add_task(
        run_agent_task, db_command.task_id, command.command)

    return {"task_id": db_command.task_id}
