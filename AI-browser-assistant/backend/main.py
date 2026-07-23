from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routes.CommandsCreate import router as CommandsCreate
from app.routes.resumeUpload import router as ResumeUpload
from app.routes.userCreateResponse import router as UserCreateResponse
from app.database import Base, engine
# ensures they register with Base
from app.models_db.gmail_creds import GmailCredentials, ContactGroup


app = FastAPI()


app.add_middleware(
    CORSMiddleware,

    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(CommandsCreate)
app.include_router(ResumeUpload)
app.include_router(UserCreateResponse)


Base.metadata.create_all(bind=engine)
