import secrets
from passlib.context import CryptContext

import passlib.context
import secrets
from typing import Type


CryptContext: Type[passlib.context.CryptContext]
pwd_context: passlib.context.CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def generate_token() -> str:
    return secrets.token_urlsafe(32)