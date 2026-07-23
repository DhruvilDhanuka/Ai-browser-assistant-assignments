from fastapi import Depends, FastAPI, UploadFile, Body, Form, File, Header, HTTPException, WebSocketDisconnect, status, APIRouter, BackgroundTasks, WebSocket
from app.database import Base, SessionLocal, get_db
from app.schemasPydantic.schemas import UserProfileCreate, UserProfileResponse
from sqlalchemy.orm import sessionmaker, Session
from app.models_db.UserProfile import Documents
import os
import shutil


UPLOAD_DIR = "uploadedResumes"


router = APIRouter(prefix="/documents", tags=["commands"])


ALLOWED_CONTENT_TYPE = {"application/pdf"}
ALLOWED_EXTENSIONS = {".pdf"}


def save_file_docs(db, user_id, doc_type: str = Form(...), file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Invalid file extension: {ext}")

    if file.content_type not in ALLOWED_CONTENT_TYPE:
        raise HTTPException(400, f"Invalid file type: {file.content_type}")

    user_dir = os.path.join(UPLOAD_DIR, str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    file_path = os.path.join(user_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    doc_row = db.query(Documents).filter(Documents.user_id == user_id).first()
    if doc_row is None:
        doc_row = Documents(user_id=user_id, docs=[])
        db.add(doc_row)

    existing_docs = doc_row.docs or []
    existing_docs.append({
        "doc_type": doc_type,
        "path": file_path,
        "filename": file.filename,
    })
    doc_row.docs = existing_docs

    db.commit()
    db.refresh(doc_row)
    return doc_row


@router.post("/{user_id}")
def resumeUpload(user_id: int,
                 doc_type: str = Form(...),
                 file: UploadFile = File(...),
                 db: Session = Depends(get_db)):

    doc_row = save_file_docs(db, user_id, doc_type, file)

    return {"user_id": user_id, "docs": doc_row.docs}
