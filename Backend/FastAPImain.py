from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os

from Routers import (
    auth, users, workouts, cardio, strength,
    exercises, sets, meals, food, analytics,
    exercise_search, food_search
)

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_ANON_KEY or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError("SUPABASE_URL, SUPABASE_ANON_KEY, and SUPABASE_SERVICE_ROLE_KEY must be set in .env")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("FITT API starting up...")
    yield
    print("FITT API shutting down...")


app = FastAPI(
    title="FITT API",
    description="Fitness tracking backend – workouts, meals, nutrition and analytics.",
    version="1.0.0",
    lifespan=lifespan,
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Core CRUD routes
app.include_router(auth.router,            prefix="/auth",            tags=["Auth"])
app.include_router(users.router,           prefix="/users",           tags=["Users"])
app.include_router(workouts.router,        prefix="/workouts",        tags=["Workouts"])
app.include_router(cardio.router,          prefix="/cardio",          tags=["Cardio"])
app.include_router(strength.router,        prefix="/strength",        tags=["Strength"])
app.include_router(exercises.router,       prefix="/exercises",       tags=["Exercises"])
app.include_router(sets.router,            prefix="/sets",            tags=["Sets"])
app.include_router(meals.router,           prefix="/meals",           tags=["Meals"])
app.include_router(food.router,            prefix="/food",            tags=["Food"])
app.include_router(analytics.router,       prefix="/analytics",       tags=["Analytics"])

# External API bridge routes
app.include_router(exercise_search.router, prefix="/exercise-search", tags=["Exercise Search (ExerciseDB)"])
app.include_router(food_search.router,     prefix="/food-search",     tags=["Food Search (OpenFoodFacts)"])


@app.get("/", tags=["Health"])
def root():
    return {"status": "ok", "message": "FITT API is running"}