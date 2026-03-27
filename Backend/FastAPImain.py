from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

from Routers import users, workouts, meals, groq

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL, SUPABASE_ANON_KEY, and SUPABASE_SERVICE_ROLE_KEY must be set in .env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY must be set in .env")


def get_cors_config():
    raw_origins = os.getenv("CORS_ORIGINS", "")
    if not raw_origins.strip():
        return {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "https://localhost:5173",
            ],
            "allow_credentials": True,
        }

    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    if origins == ["*"]:
        return {"origins": ["*"], "allow_credentials": False}

    return {"origins": origins, "allow_credentials": True}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("FITT API starting up...")
    yield
    print("FITT API shutting down...")


app = FastAPI(
    title="FITT API",
    description="Fitness tracking backend — workouts, meals, nutrition and analytics.",
    version="2.0.0",
    lifespan=lifespan,
)

cors = get_cors_config()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors["origins"],
    allow_credentials=cors["allow_credentials"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router,    prefix="/users",    tags=["Users"])
app.include_router(workouts.router, prefix="/workouts", tags=["Workouts"])
app.include_router(meals.router,    prefix="/meals",    tags=["Meals"])
app.include_router(groq.router,     prefix="/groq",     tags=["Groq"])

@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "FITT API is running"}
