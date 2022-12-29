import requests
import pytest

from settings import Settings
from password import verify_password

settings: Settings = Settings()


def test_create_a_new_user(user_info, database) -> None:
    """
    GIVEN registration a new user, email, password, username
    WHEN POST "/users/registration"
    THEN check status_code == (201, created), user in database, user email in response
    """
    r = requests.post(
        f"{settings.BACKEND}/users/registration", json=user_info, timeout=10
    )
    r_body = r.json()
    cur = database.cursor()
    user_db = cur.execute(
        "SELECT email FROM users WHERE email = ?", (user_info["email"],)
    ).fetchone()
    assert user_db
    assert r.status_code == 201
    assert r_body["email"] == user_info["email"]


def test_reg_user_existing_email(new_user) -> None:
    """
    GIVEN registration a new user with existing email
    WHEN POST "/users/registration"
    THEN check status_code == 409, "Email already exists." in response
    """

    r = requests.post(
        f"{settings.BACKEND}/users/registration", json=new_user, timeout=5
    )
    r_body = r.json()
    assert "Email already exists." == r_body["detail"]
    assert r.status_code == 409


def test_reg_confirm(database, new_user) -> None:
    """
    GIVEN registration confirmation, with email and verification_code from email
    WHEN POST "/users/confirm"
    THEN check status_code, email in response, "verified" in response, user verified field in db == 1
    """
    r = requests.post(
        f"{settings.BACKEND}/users/confirm",
        json={"email": new_user["email"], "code": new_user["verification_code"]},
        timeout=5,
    )
    r_body = r.json()
    cur = database.cursor()
    user_db = cur.execute(
        "SELECT verified FROM users WHERE email = ?", (new_user["email"],)
    ).fetchone()
    assert user_db[0] == 1
    assert r.status_code == 200
    assert r_body["email"] == new_user["email"]
    assert r_body["status"] == "verified"


def test_reg_confirm_wrong_code(database, new_user) -> None:
    """
    GIVEN registration confirmation with wrong verification code
    WHEN POST "users/confirm"
    THEN check status_code, user verified field in db == 0, "Wrong email or verification code." in response
    """
    r = requests.post(
        f"{settings.BACKEND}/users/confirm",
        json={"email": new_user["email"], "code": 6666},
        timeout=5,
    )
    r_body = r.json()
    cur = database.cursor()
    user_db = cur.execute(
        "SELECT verified FROM users WHERE email = ?", (new_user["email"],)
    ).fetchone()
    assert user_db[0] == 0
    assert "Wrong email or verification code." in r_body["detail"]
    assert r.status_code == 409


def test_user_login(confirmed_user) -> None:
    """
    GIVEN confirmed user login with email and password
    WHEN POST "/users/login"
    THEN check status_code, token and type in response
    """
    r = requests.post(
        f"{settings.BACKEND}/users/login",
        json={"email": confirmed_user["email"], "password": "password"},
        timeout=5,
    )
    r_body = r.json()
    assert r_body["access_token"]
    assert r_body["token_type"] == "Bearer"


def test_user_login_wrong_pass(confirmed_user) -> None:
    """
    GIVEN confirmed user try login with wrong password
    WHEN POST "/users/login"
    THEN check status_code = 401
    """
    r = requests.post(
        f"{settings.BACKEND}/users/login",
        json={"email": confirmed_user["email"], "password": "wrong_pass"},
        timeout=5,
    )
    assert r.status_code == 401


def test_get_current_user_info(user_token) -> None:
    """
    GIVEN get current_user info by token
    WHEN GET "/users/user"
    THEN check status_code == 200, user email in response
    """
    r = requests.get(
        f"{settings.BACKEND}/users/user",
        headers={"Authorization": "Bearer " + user_token["token"]},
        timeout=5,
    )
    r_body = r.json()
    assert r.status_code == 200
    assert r_body["email"] == user_token["data"]["email"]


def test_user_patch(user_token) -> None:
    """
    GIVEN update current_user username
    WHEN PATCH "/users/user"
    THEN check status_code == 200, username in response
    """
    payload = {"username": "update"}
    r = requests.patch(
        f"{settings.BACKEND}/users/user",
        json=payload,
        headers={"Authorization": "Bearer " + user_token["token"]},
        timeout=5,
    )
    r_body = r.json()
    assert r.status_code == 200
    assert r_body["username"] == payload["username"]


def test_delete_user(user_token, database) -> None:
    """
    GIVEN delete current_user
    WHEN DELETE "/users/user"
    THEN check status_code == 200, email in db is None
    """
    r = requests.delete(
        f"{settings.BACKEND}/users/user",
        headers={"Authorization": "Bearer " + user_token["token"]},
        timeout=5,
    )
    r_body = r.json()
    cur = database.cursor()
    user_db = cur.execute(
        "SELECT email FROM users WHERE email = ?", (user_token["data"]["email"],)
    ).fetchone()
    assert user_db is None
    assert r_body["deleted"]
    assert r.status_code == 200


@pytest.mark.parametrize(
    "username,  email, password",
    [
        ("test_user_1", "test_1@gmail.com", "user_1@pa55"),
        ("test_user_2", "test_2@gmail.com", "user_2@pa55"),
        ("test_user_3", "test_3@gmail.com", "user_3@pa55"),
        ("test_user_4", "test_4@gmail.com", "user_4@pa55"),
        ("test_user_5", "test_5@gmail.com", "user_5@pa55"),
    ],
)
def test_users_create(username, email, password, database) -> None:
    """
    GIVEN user registration
    WHEN POST "/users/registration"
    THEN check status_code == 201, user in database and with not verified status
    """
    payload = {"username": username, "email": email, "password": password}
    r = requests.post(
        f"{settings.BACKEND}/users/registration", json=payload, timeout=10
    )
    cur = database.cursor()
    user_db = cur.execute(
        "SELECT email, verified FROM users WHERE email = ?", (email,)
    ).fetchone()
    assert user_db[1] == 0
    assert r.status_code == 201
    cur.execute("DELETE FROM users WHERE email = ?", (email,))
    database.commit()


# def test_many_user_in_db(clear_database, database):
#     """
#     GIVEN registration 5 users
#     WHEN POST "/users/registration"
#     THEN check status_code == 201, 5 users in database
#     """
#     cur = database.cursor()
#     users = cur.execute("SELECT * FROM users").fetchall()
#     print(users)


def test_user_password_reset(confirmed_user, database) -> None:
    """
    GIVEN password reset by email with sending new verification code to the email
    WHEN POST "/server/password-reset"
    THEN check status_code == 200, changing verification_code
    """
    cur = database.cursor()
    user_db = cur.execute(
        "SELECT email, verification_code FROM users WHERE email = ?",
        (confirmed_user["email"],),
    ).fetchone()
    r = requests.post(
        f"{settings.BACKEND}/users/password-reset",
        json={"email": confirmed_user["email"]},
        timeout=5,
    )
    r_body = r.json()
    user_refresh = cur.execute(
        "SELECT email, verification_code FROM users WHERE email = ?",
        (confirmed_user["email"],),
    ).fetchone()
    assert user_db[1] != user_refresh[1]
    assert r.status_code == 200
    assert confirmed_user["email"] in r_body


def test_user_password_reset_wrong_email(confirmed_user) -> None:
    """
    GIVEN password reset with unreg email
    WHEN POST "/users/password-reset"
    THEN check status_code == 404
    """
    r = requests.post(
        f"{settings.BACKEND}/users/password-reset",
        json={"email": "fake_pytest_email@yahoo.com"},
        timeout=5,
    )
    assert r.status_code == 404


def test_password_reset_confirm(confirmed_user, database) -> None:
    """
    GIVEN password reset confirmation by email, verification code, new_password
    WHEN POST "/users/password-confirm"
    THEN check status_code == 200, check pass verification with new password
    """
    payload = {
        "email": confirmed_user["email"],
        "code": confirmed_user["verification_code"],
        "password": "new_password",
    }
    r = requests.post(
        f"{settings.BACKEND}/users/password-confirm",
        json=payload,
        timeout=5,
    )
    r_body = r.json()
    password = database.execute(
        "SELECT password FROM users WHERE email = ?", (payload["email"],)
    ).fetchone()
    password_check = verify_password(payload["password"], password[0])
    assert password_check is True
    assert r_body["password"] == "updated"
    assert r.status_code == 200


def test_user_logout(user_token) -> None:
    """
    GIVEN current_user logout
    WHEN POST "/users/logout"
    THEN check status_code, access rejected by new request
    """
    r = requests.post(
        f"{settings.BACKEND}/users/logout",
        headers={"Authorization": "Bearer " + user_token["token"]},
        timeout=5,
    )
    try_access = requests.get(
        f"{settings.BACKEND}/users/user",
        headers={"Authorization": "Bearer " + user_token["token"]},
        timeout=5,
    )
    r_body = r.json()
    # try_access_body = try_access.json()
    assert r.status_code == 200
    assert r_body[user_token["data"]["email"]] == "logout"
    assert try_access.status_code == 401
