from enum import Enum
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class UserProfileCreate(BaseModel):
    email: str = Field(..., description="The email address of the user")
    name: str = Field(..., description="The full name of the user")
    phone_number: str = Field(..., description="The phone number of the user")
    resume_text: str = Field(..., description="The resume text of the user")


class UserProfileResponse(BaseModel):
    id: int = Field(..., description="The unique identifier of the user profile")
    email: str = Field(..., description="The email address of the user")
    name: str = Field(..., description="The full name of the user")
    phone_number: str = Field(..., description="The phone number of the user")
    resume_text: str = Field(..., description="The resume text of the user")

    model_config = ConfigDict(from_attributes=True)


class UserCommandCreate(BaseModel):

    command: str = Field(...,
                         description="The command to be executed by the user")

    parameters: Optional[dict] = Field(
        None, description="Optional parameters for the command")


class StatusTask(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class Task(BaseModel):

    task_Id: str = Field(..., description="Task ID of the task")

    task_command: str = Field(..., description="command statement of the task")

    task_status: StatusTask = Field(..., description="Status of the task ")


class AgentAction(BaseModel):

    actions: list[str] = Field(...,
                               description="Required actions to complete the task")
    target_urls: Optional[str] = None
    data: dict = {}
