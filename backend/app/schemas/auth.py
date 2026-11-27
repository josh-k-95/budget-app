import uuid
from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.security import MAX_PASSWORD_LENGTH

Username = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True, min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_.-]+$"
    ),
]
# Minimum length is configurable, so it is checked in the endpoint, not here.
Password = Annotated[str, StringConstraints(max_length=MAX_PASSWORD_LENGTH)]


class RegisterRequest(BaseModel):
    username: Username
    password: Password


class LoginRequest(BaseModel):
    username: Annotated[str, StringConstraints(strip_whitespace=True, max_length=64)]
    password: Password


class BudgetMembershipResponse(BaseModel):
    id: uuid.UUID
    name: str
    role: str


class UserResponse(BaseModel):
    id: uuid.UUID
    username: str
    budgets: list[BudgetMembershipResponse]
