import random
import asyncio

import pytest
import requests
import psycopg2

from password import password_hash, verify_password
from authentication import authenticate, create_access_token
from settings import Settings

settings = Settings()


@pytest.fixture(scope="session")
def backend():
    return "http://0.0.0.0:8000"


# "dbname=postgresDB user=postgresUser host=localhost port=5455 password=postgresPW"
@pytest.fixture(scope="session")
def database():
    conn = psycopg2.connect("dbname=postgresDB user=postgresUser host=0.0.0.0 port=5432 password=postgresPW")
    conn.autocommit=True
    cur = conn.cursor()
    yield cur
    conn.close()


@pytest.fixture(scope="session")
def user_info(database):
    data = {
        "email": "pytest@yahoo.com",
        "password": "test_P@55",
        "username": "Pytest",
    }
    yield data
    database.execute("DELETE FROM users WHERE email = %s", (data["email"],))


@pytest.fixture(scope="function")
def new_user(database):
    password = password_hash("password")
    code = random.randint(1000, 9999)
    data = {
        "username": "user_test",
        "email": "user_test123@gmail.com",
        "password": password,
        "verified": 0,
        "verification_code": code,
        "is_admin": 0,
    }
    database.execute(
        """
        INSERT INTO users(username, email, password, verified, verification_code, is_admin)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            data["username"],
            data["email"],
            data["password"],
            data["verified"],
            data["verification_code"],
            data["is_admin"],
        ),
    )
    yield data
    database.execute("DELETE FROM users WHERE email = %s", (data["email"],))


@pytest.fixture(scope="function")
def confirmed_user(database):
    password = password_hash("password")
    code = random.randint(1000, 9999)
    data = {
        "username": "user_test",
        "email": "user_test123@gmail.com",
        "password": password,
        "verified": 1,
        "verification_code": code,
        "is_admin": 0,
    }
    database.execute(
        """
        INSERT INTO users(username, email, password, verified, verification_code, is_admin)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            data["username"],
            data["email"],
            data["password"],
            data["verified"],
            data["verification_code"],
            data["is_admin"],
        )
    )
    yield data
    database.execute("SELECT id FROM users WHERE email = %s", (data["email"],))
    user_id = database.fetchone()
    database.execute("DELETE FROM access_tokens WHERE user_id = %s", (user_id[0],))
    database.execute("DELETE FROM users WHERE email = %s", (data["email"],))


@pytest.fixture(scope="function")
def user_token(database):
    password = password_hash("password")
    code = random.randint(1000, 9999)
    data = {
        "email": "pytest123@gmail.com",
        "password": password,
        "username": "Pytest",
        "verified": 1,
        "verification_code": code,
        "is_admin": 0,
    }
    database.execute(
        """
        INSERT INTO users(username, email, password, verified, verification_code, is_admin)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            data["username"],
            data["email"],
            data["password"],
            data["verified"],
            data["verification_code"],
            data["is_admin"],
        ),
    )
    raw_token = requests.post(
        f"{settings.BACKEND}/users/login",
        json={"email": data["email"],"password": "password"},
    )
    yield {"token": raw_token.json()["access_token"], "data": data}
    database.execute("SELECT id FROM users WHERE email = %s", (data["email"],))
    user_id = database.fetchone()
    try:
        database.execute("DELETE FROM access_tokens WHERE user_id = %s", (user_id[0],))
        database.execute("DELETE FROM users WHERE email = %s", (data["email"],))
    except:
        pass


