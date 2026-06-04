import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text as sql_text
from database import engine, Base, SessionLocal
from routers import profile as profile_router
from routers import diet as diet_router
from routers import workout as workout_router

try:
    Base.metadata.create_all(bind=engine)
except Exception:
    pass

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

@app.get("/health")
def health():
    db = SessionLocal()
    try:
        db.execute(sql_text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": str(e)[:400]}
    finally:
        db.close()

_FRONTEND = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", StaticFiles(directory=_FRONTEND, html=True), name="frontend")
