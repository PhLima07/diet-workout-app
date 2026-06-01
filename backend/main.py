import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine, Base
from routers import profile as profile_router
from routers import diet as diet_router
from routers import workout as workout_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Diet & Workout Planner")

origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(profile_router.router)
app.include_router(diet_router.router)
app.include_router(workout_router.router)

_FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=_FRONTEND, html=True), name="frontend")
