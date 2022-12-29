from pydantic import BaseSettings


class Settings(BaseSettings):
    debug = True
    database_sqlite: str
    database_test: str
    SECRET_KEY: str
    email_code: str
    BACKEND: str
    TEST: str
    Rabbit_host: str
    Rabbit_chanel: str

    class Config:
        env_file = ".env"