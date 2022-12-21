import os
from typing import Any, Type

import sqlalchemy
from sqlalchemy.engine.base import Engine
from sqlalchemy.sql.schema import MetaData

from databases import Database
from settings import Settings


settings: Settings = Settings()


TESTING = os.getenv("TEST")

TEST_DATABASE_URL: str = str(settings.database_test)
DATABASE_URL: str = str(settings.database_sqlite)

if TESTING == "test":
    print("TEST")
    database: Any = Database(TEST_DATABASE_URL)
    sqlalchemy_engine: Engine = sqlalchemy.create_engine(
        TEST_DATABASE_URL,
    )  # connect_args={"check_same_thread": False}
else:
    database: Any = Database(DATABASE_URL)
    sqlalchemy_engine: Engine = sqlalchemy.create_engine(
        DATABASE_URL
    )  # connect_args={"check_same_thread": False}


metadata: MetaData = sqlalchemy.MetaData()
metadata.create_all(sqlalchemy_engine)


# Dependency
def get_database() -> Database:
    return database
