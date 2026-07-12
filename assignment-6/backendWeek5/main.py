from fastapi import FastAPI, HTTPException, Depends
from app.routes.commands import router as commands_router
from fastapi.middleware.cors import CORSMiddleware
from app.routes.userprofile import router as user_profile_router
from app.routes.Status import router as status_router
from app.database import Base, engine


app = FastAPI()


app.add_middleware(
    CORSMiddleware,

    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(commands_router)
app.include_router(user_profile_router)
app.include_router(status_router)

Base.metadata.create_all(bind=engine)
