from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class StatusTask(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class UserProfileCreate(BaseModel):

    Name: str = Field(..., description="The full name of the user")
    Email: str = Field(..., description="The email address of the user")
    Contact_number: str = Field(...,
                                description="The phone number of the user")
    College: str = Field(..., description="College name of the user")
    Skills: str = Field(..., description="Skill set of the user")
    extra_info: dict = Field(..., description="Extra info of the user")


class UserProfileResponse(BaseModel):

    id: int = Field(..., description="Unique id of the user")
    Name: str = Field(..., description="The full name of the user")
    Email: str = Field(..., description="The email address of the user")
    Contact_number: str = Field(...,
                                description="The phone number of the user")
    College: str = Field(..., description="College name of the user")
    Skills: str = Field(..., description="Skill set of the user")
    extra_info: dict = Field(..., description="Extra info of the user")
    model_config = ConfigDict(from_attributes=True)


class DocumentEntry(BaseModel):
    doc_type: str  # "resume", "aadhar", etc.
    path: str
    filename: str


class DocumentCreate(BaseModel):
    user_id: int = Field(...,
                         description="The id of the user who uploaded the document")
    docs: list[DocumentEntry] = Field(...,
                                      description="All documents uploaded by the user")


class UserCommandCreate(BaseModel):
    user_id: int = Field(...,
                         description="The id of user which gave the command ")
    command: str = Field(..., description="The command given by the user ")
    status: StatusTask = Field(
        default=StatusTask.PENDING, description="Status of the task given by user")


class DocumentResponse(BaseModel):
    user_id: int
    docs: list[DocumentEntry]

    model_config = ConfigDict(from_attributes=True)
