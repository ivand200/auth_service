from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
import uvicorn

from routers.users import users_router
from db import get_database, metadata, sqlalchemy_engine, database


app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8888"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    # await database.connect()
    await get_database().connect()


@app.on_event("shutdown")
async def shutdown():
    # await database.disconnect()
    await get_database().disconnect()


app.include_router(users_router, prefix="/users", tags=["users"])


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
