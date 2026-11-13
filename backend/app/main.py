from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routes import (
    auth, profile, dashboard, activities, activity_session,
    exercises, form, diet, challenges, leaderboard, assistant, journey, menu,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="FitCampus AI", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
for r in (auth, profile, dashboard, activities, activity_session, exercises,
          form, diet, challenges, leaderboard, assistant, journey, menu):
    app.include_router(r.router)


@app.get("/")
async def root():
    return {"app": "FitCampus AI", "version": "2.0.0", "status": "ok", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}