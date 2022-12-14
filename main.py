from fastapi import FastAPI

from routers.users import users_router
from db import get_database, metadata, sqlalchemy_engine, database


app = FastAPI()


@app.on_event("startup")
async def startup():
    # await database.connect()
    await get_database().connect()


@app.on_event("shutdown")
async def shutdown():
    # await database.disconnect()
    await get_database().disconnect()


app.include_router(users_router, prefix="/users", tags=["users"])
