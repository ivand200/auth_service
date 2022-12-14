from pydantic import BaseSettings


class Settings(BaseSettings):
    debug = True
    database_url: str
    database_sqlite: str
    SECRET_KEY: str
    email_code: str
    BACKEND: str

    class Config:
        env_file = ".env"