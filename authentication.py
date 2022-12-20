from typing import Optional, Union

from fastapi import HTTPException, status

from models.users import AccessToken, access_tokens, users, UserDB
from password import verify_password
from db import database


async def authenticate(email: str, password: str) -> Union[UserDB, bool]:
    try:
        query = "SELECT * FROM users WHERE email = :email"
        user = await database.fetch_one(query=query, values={"email": email})
    except:
        return False
    if not user.verified:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Unverified account."
        )
    if not verify_password(password, user.password):
        return False
    return UserDB(**user)


async def create_access_token(user: UserDB) -> AccessToken:
    token = AccessToken(user_id=user.id)
    query = """INSERT INTO access_tokens(access_token, user_id, expiration_date)
           VALUES (:access_token, :user_id, :expiration_date)
           ON CONFLICT (user_id)
           DO UPDATE SET access_token = :access_token, expiration_date = :expiration_date"""
    values = {
        "access_token": token.access_token,
        "user_id": token.user_id,
        "expiration_date": token.expiration_date,
    }
    await database.execute(query=query, values=values)
    refresh_query = "SELECT * FROM access_tokens WHERE access_token = :access_token"
    refresh_token_db = await database.fetch_one(
        query=refresh_query, values={"access_token": token.access_token}
    )
    return AccessToken(**refresh_token_db)
