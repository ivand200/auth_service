# import time
# pylint: disable = C0115, R0903
from datetime import datetime, timedelta

from pydantic import BaseModel, Field, EmailStr
import sqlalchemy

from db import metadata
from password import generate_token
from sqlalchemy.sql.schema import MetaData
from typing import Any, Type


def get_expiration_date(duration_seconds: int = 86400) -> datetime:
    """Calculate expiration time for token"""
    return datetime.now() + timedelta(seconds=duration_seconds)


class UserBase(BaseModel):
    email: EmailStr
    username: str

    class Config:
        orm_mode: bool = True


class UserCreate(UserBase):
    password: str


class UserDB(UserBase):
    id: int

    class Config:
        orm_mode: bool = True


class UserLogin(BaseModel):
    email: str
    password: str

    class Config:
        orm_mode: bool = True


class UserUpdate(BaseModel):
    username: str

    class Config:
        orm_mode: bool = True


class PasswordConfirm(BaseModel):
    code: int
    password: str
    new_password: str


class AccessToken(BaseModel):
    user_id: int
    access_token: str = Field(default_factory=generate_token)
    expiration_date: datetime = Field(default_factory=get_expiration_date)

    class Config:
        orm_mode: bool = True


class EmailConfirm(BaseModel):
    email: str
    code: int


# metadata = sqlalchemy.MetaData()


users: Any = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True, autoincrement=True),
    sqlalchemy.Column("username", sqlalchemy.String, nullable=False),
    sqlalchemy.Column(
        "email", sqlalchemy.String, nullable=False, index=True, unique=True
    ),
    sqlalchemy.Column("password", sqlalchemy.String, nullable=False),
    sqlalchemy.Column("verified", sqlalchemy.Integer, nullable=False),
    sqlalchemy.Column("verification_code", sqlalchemy.Integer),
    sqlalchemy.Column("is_admin", sqlalchemy.Integer, default=0, nullable=False),
)

access_tokens: Any = sqlalchemy.Table(
    "access_tokens",
    metadata,
    sqlalchemy.Column("access_token", sqlalchemy.String, primary_key=True),
    sqlalchemy.Column(
        "user_id", sqlalchemy.ForeignKey("users.id"), nullable=False, unique=True
    ),
    sqlalchemy.Column("expiration_date", sqlalchemy.DateTime(), nullable=False),
)
