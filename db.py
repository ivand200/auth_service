from typing import Any, Type

import sqlalchemy
from sqlalchemy.engine.base import Engine
from sqlalchemy.sql.schema import MetaData

from databases import Database
from settings import Settings


settings: Settings = Settings()

DATABASE_URL: str = str(settings.database_sqlite)
database: Any = Database(DATABASE_URL)
sqlalchemy_engine: Engine = sqlalchemy.create_engine(
    DATABASE_URL
)  # connect_args={"check_same_thread": False}

metadata: MetaData = sqlalchemy.MetaData()
metadata.create_all(sqlalchemy_engine)

# Dependency
def get_database() -> Database:
    return database
