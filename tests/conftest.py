import os
import random
import sqlite3

import pytest
import requests

from password import password_hash, verify_password
from authentication import authenticate, create_access_token
from settings import Settings


settings = Settings()


TESTING = os.getenv("TEST")
if TESTING == "test":
    database_path = "test_users.db"
else:
    database_path = "users.db"



@pytest.fixture(scope="session")
def backend():
    return "http://0.0.0.0:8000"


@pytest.fixture(scope="session")
def database():
    # con = sqlite3.connect(database_path)
    con = sqlite3.connect("test_users.db")
    yield con
    con.close()


@pytest.fixture(scope="session")
def user_info(database):
    data = {
        "email": "pytest@yahoo.com",
        "password": "test_P@55",
        "username": "Pytest",
    }
    yield data
    cur = database.cursor()
    cur.execute("DELETE FROM users WHERE email = ?", (data["email"],))
    database.commit()


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
    cur = database.cursor()
    cur.execute(
        """
        INSERT INTO users(username, email, password, verified, verification_code, is_admin)
        VALUES (?, ?, ?, ?, ?, ?)
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
    database.commit()
    yield data
    cur.execute("DELETE FROM users WHERE email = ?", (data["email"],))
    database.commit()


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
    cur = database.cursor()
    cur.execute(
        """
        INSERT INTO users(username, email, password, verified, verification_code, is_admin)
        VALUES (?, ?, ?, ?, ?, ?)
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
    database.commit()
    yield data
    user_id = cur.execute("SELECT id FROM users WHERE email = ?", (data["email"],)).fetchone()
    cur.execute("DELETE FROM access_tokens WHERE user_id = ?", (user_id[0],))
    cur.execute("DELETE FROM users WHERE email = ?", (data["email"],))
    database.commit()


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
    cur = database.cursor()
    cur.execute(
        """
        INSERT INTO users(username, email, password, verified, verification_code, is_admin)
        VALUES (?, ?, ?, ?, ?, ?)
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
    database.commit()
    raw_token = requests.post(
        f"{settings.BACKEND}/users/login",
        json={"email": data["email"],"password": "password"},
    )
    yield {"token": raw_token.json()["access_token"], "data": data}
    user_id = cur.execute("SELECT id FROM users WHERE email = ?", (data["email"],)).fetchone()
    try:
        cur.execute("DELETE FROM access_tokens WHERE user_id = ?", (user_id[0],))
        cur.execute("DELETE FROM users WHERE email = ?", (data["email"],))
        database.commit()
    except:
        pass


# @pytest.mark.parametrize(
#     "username,  email, password",
#     [
#         ("test_user_1", "test_1@gmail.com", "user_1@pa55"),
#         ("test_user_2", "test_2@gmail.com", "user_2@pa55"),
#         ("test_user_3", "test_3@gmail.com", "user_3@pa55"),
#         ("test_user_4", "test_4@gmail.com", "user_4@pa55"),
#         ("test_user_5", "test_5@gmail.com", "user_5@pa55"),
#     ],
# )
# @pytest.fixture(scope="function")
# def clear_database(database, username, email, password,):
#     payload = {"username": username, "email": email, "password": password}
#     r = requests.post(f"{settings.BACKEND}/users/registration", json=payload, timeout=5)
#     yield True
#     cur = database.curosr()
#     cur.execute("DELETE FROM access_tokens")
#     cur.execute("DELETE FROM users")
#     database.commit()
