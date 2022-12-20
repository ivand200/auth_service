import logging
import random
from datetime import datetime
from typing import Any, Coroutine, Type, Union, List

from sqlalchemy.sql.schema import MetaData
from fastapi import APIRouter, HTTPException, status, Depends, Body
from fastapi.security import APIKeyHeader
from databases import Database

from models.users import (
    AccessToken,
    users,
    metadata,
    UserBase,
    UserCreate,
    UserDB,
    UserLogin,
    UserUpdate,
    EmailConfirm,
    PasswordConfirm,
)
from db import get_database
from password import password_hash, verify_password
from authentication import authenticate, create_access_token
from email_service import email_service

users_router: Any = APIRouter()
api_key_header: Any = APIKeyHeader(name="Authorization")


async def get_current_user(
    token: str = Depends(api_key_header),
    database: Database = Depends(get_database),
) -> UserDB:
    """
    Get current user by verification  'Authorization' header token and time
    """
    raw_token = token[7:]
    query = """
        SELECT access_tokens.expiration_date, access_tokens.access_token, users.id, users.email, users.username
        FROM access_tokens
        JOIN users ON access_tokens.user_id = users.id
        WHERE access_token = :access_token
        """
    user_db = await database.fetch_one(query=query, values={"access_token": raw_token})
    if not user_db:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    date_check = datetime.strptime(str(user_db.expiration_date), "%Y-%m-%d %H:%M:%S.%f")
    if date_check < datetime.now():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return user_db


async def get_user_by_email(
    email: str, database: Database = Depends(get_database)
) -> UserDB:
    """
    Search user by email or return 404
    """
    query = """SELECT * FROM users WHERE email = :email"""
    user_db = await database.fetch_one(query=query, values={"email": email})
    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Can't find the email"
        )
    return user_db


@users_router.post(
    "/registration", response_model=UserDB, status_code=status.HTTP_201_CREATED
)
async def register(
    user: UserCreate, database: Database = Depends(get_database)
) -> UserDB:
    """
    Register a new user
    email, pasword, username
    """
    query = "SELECT * FROM users WHERE email = :email"
    result = await database.fetch_one(query=query, values={"email": user.email})
    if result:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already exists."
        )
    query = """
        INSERT INTO users(username, email, password, verified, verification_code, is_admin)
        VALUES (:username, :email, :password, :verified, :verification_code, :is_admin)
        """
    verification_code = random.randint(1000, 9999)
    hashed_password = password_hash(user.password)
    values = {
        "username": user.username,
        "email": user.email,
        "password": hashed_password,
        "verified": 0,
        "verification_code": verification_code,
        "is_admin": 0,
    }
    await database.execute(query=query, values=values)
    email_service(str(verification_code), user.email)
    refresh_query = """SELECT id, username, email FROM users WHERE email = :email"""
    refresh_user = await database.fetch_one(
        query=refresh_query, values={"email": user.email}
    )
    return refresh_user


@users_router.post("/confirm", status_code=status.HTTP_200_OK)
async def registration_confirmation(
    email_confirm: EmailConfirm, database: Database = Depends(get_database)
) -> dict:
    """
    Email confirmation with verification code, email
    """
    query = """SELECT * FROM users WHERE email = :email"""
    user_db = await database.fetch_one(
        query=query, values={"email": email_confirm.email}
    )
    if not user_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Can't find email."
        )
    if user_db.verification_code == email_confirm.code and user_db.verified == 0:
        query = """UPDATE users SET verified = :verified WHERE email = :email"""
        await database.execute(
            query=query, values={"verified": 1, "email": email_confirm.email}
        )
        return {"email": email_confirm.email, "status": "verified"}
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT, detail="Wrong email or verification code."
    )


@users_router.post("/login")
async def create_token(
    user: UserLogin,
) -> dict:
    """
    User login
    returns access_token, token_type
    """
    email = user.email
    password = user.password
    user_db = await authenticate(email, password)
    if not user_db:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    token = await create_access_token(user_db)
    return {"access_token": token.access_token, "token_type": "Bearer"}


@users_router.get("/user", response_model=UserBase, status_code=status.HTTP_200_OK)
async def user_self_info(user: UserDB = Depends(get_current_user)) -> dict:
    """
    Get current user info
    """
    return user


@users_router.patch("/user", response_model=UserBase, status_code=status.HTTP_200_OK)
async def user_update(
    user_info: UserUpdate,
    user: UserDB = Depends(get_current_user),
    database: Database = Depends(get_database),
) -> UserBase:
    """
    Update current_user username
    """
    query = """UPDATE users SET username = :username WHERE users.id = :id"""
    await database.execute(
        query=query, values={"username": user_info.username, "id": user.id}
    )
    query_refresh = """SELECT email, username FROM users WHERE id = :id"""
    refresh_user = await database.fetch_one(query=query_refresh, values={"id": user.id})
    return refresh_user


@users_router.delete("/user", status_code=status.HTTP_200_OK)
async def user_delete(
    user: UserDB = Depends(get_current_user), database: Database = Depends(get_database)
) -> dict:
    """
    Delete current_user
    """
    query = """DELETE FROM access_tokens WHERE user_id = :id"""
    await database.execute(query=query, values={"id": user.id})
    query = """DELETE FROM users WHERE id = :id"""
    await database.execute(query=query, values={"id": user.id})
    return {"deleted": user.id}


@users_router.post("/password-reset", status_code=status.HTTP_200_OK)
async def password_reset(
    email: str = Body(embed=True),
    database: Database = Depends(get_database),
) -> str:
    """
    Password reset by email
    with sending new verification code to the email
    """
    user_db: UserDB
    user_db = await get_user_by_email(email, database)
    code = random.randint(1000, 9999)
    query = """UPDATE users SET verification_code = :code WHERE id = :id"""
    await database.execute(query=query, values={"code": code, "id": user_db.id})
    email_service(str(code), user_db.email)
    return f"Confirmation code was sended to {user_db.email}"


@users_router.post("/password-confirm", status_code=status.HTTP_200_OK)
async def password_confirm(
    email: str = Body(),
    code: int = Body(),
    password: str = Body(),
    database: Database = Depends(get_database),
) -> dict:
    """
    Password reset confirmation
    """
    user_db = await get_user_by_email(email, database)
    if code != user_db.verification_code:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Wrong verification code."
        )
    hashed_password = password_hash(password)
    query = """UPDATE users SET password = :password WHERE id = :id"""
    await database.execute(
        query=query, values={"password": hashed_password, "id": user_db.id}
    )
    return {"password": "updated"}


@users_router.post("/email-reset")
async def email_reset(
    user: UserDB = Depends(get_current_user),
    new_email: str = Body(embed=True),
    database: Database = Depends(get_database),
) -> str:
    """
    Email reset for users
    """
    new_code = random.randint(1000, 9999)
    query = """UPDATE users SET verification_code = :code WHERE id = :id"""
    await database.execute(query=query, values={"code": new_code, "id": user.id})
    email_service(str(new_code), new_email)
    return f"Verification code was sended to {new_email}"


@users_router.post("/email-confirm")
async def user_email_conf(
    user: UserDB = Depends(get_current_user),
    new_email: str = Body(embed=True),
    code: str = Body(embed=True),
    database: Database = Depends(get_database),
) -> dict:
    """
    Email reset confirmation
    """
    query = """SELECT verification_code FROM users WHERE id = :id"""
    user_code = await database.fetch_one(query=query, values={"id": user.id})
    if code != user_code:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Wrong code.")
    query = """UPDATE users SET email = :email WHERE id = :id"""
    await database.execute(query=query, values={"email": new_email, "id": user.id})
    return {"new_email": new_email}


@users_router.post("/logout")
async def user_logout(
    user: UserDB = Depends(get_current_user),
    database: Database = Depends(get_database),
) -> dict:
    """
    User logout
    """
    query = """DELETE FROM access_tokens WHERE access_token = :token"""
    await database.execute(query=query, values={"token": user.access_token})
    return {user.email: "logout"}


@users_router.post("/check-token")
async def check_token(
    user: UserDB = Depends(get_current_user),
    database: Database = Depends(get_database),
):
    """
    Check user token for others services
    """
    return user


"""Admin service"""


@users_router.post("/user/{id}")
async def user_get_info(id: int, database: Database = Depends(get_database)):
    """
    TODO: Get user info by id, for admin service
    """
    query = "SELECT id, username, email FROM users WHERE id = :id"
    user_db = await database.fetch_one(query=query, values={"id": id})
    return user_db


@users_router.get("/list")
async def list_users(
    user: UserDB = Depends(get_current_user), database: Database = Depends(get_database)
) -> List[UserDB]:
    """
    List of all users
    """
    users_db = users.select()
    rows = await database.fetch_all(users_db)
    result = [UserDB(**row) for row in rows]
    return result
