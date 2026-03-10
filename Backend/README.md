# FITT API — Developer Guide
**v2.0.0 · FastAPI + Supabase**

FITT is a fitness-tracking REST API built with FastAPI and backed by Supabase (PostgreSQL + Auth). It lets clients log workouts, track strength exercises and sets, record meals and food items, and pull analytics — all secured by JWT bearer tokens issued by Supabase.

- **Base URL (local):** `http://localhost:8000`
- **Interactive docs:** `http://localhost:8000/docs`

---

## Table of Contents

1. [Project Setup](#1-project-setup)
2. [Authentication](#2-authentication)
3. [Users](#3-users--users)
4. [Workouts](#4-workouts--workouts)
5. [Meals](#5-meals--meals)
6. [Error Reference](#6-error-reference)
7. [Database Schema](#7-database-schema)
8. [Quick-Start Workflow](#8-quick-start-workflow)

---

## 1. Project Setup

### Prerequisites

- Python 3.11 or higher
- pip (comes with Python)
- A Supabase project (free tier works fine)
- An ExerciseDB API key from RapidAPI (optional — only needed for exercise search)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root (same folder as `FastAPImain.py`). Get the Supabase values from your project's **Settings > API** page.

```env
# Supabase
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here

# ExerciseDB (RapidAPI) — optional
EXERCISEDB_API_KEY=your-rapidapi-key-here
EXERCISEDB_API_HOST=exercisedb.p.rapidapi.com
EXERCISEDB_BASE_URL=https://exercisedb.p.rapidapi.com

GROQ_API_KEY=your_groq_api_key
```

Get a free Groq API key at **https://console.groq.com**

> ⚠️ **Never commit `.env` to version control.** Add it to your `.gitignore`.

### Database Migration

Run the following SQL in the **Supabase SQL Editor** (Dashboard > SQL Editor > New query). This sets up the schema the API expects.

```sql
-- Add workout type + cardio fields
ALTER TABLE workout
  ADD COLUMN type text NOT NULL DEFAULT 'strength'
    CHECK (type IN ('cardio', 'strength')),
  ADD COLUMN cardio_type text,
  ADD COLUMN distance float;

-- Re-point exercises directly to workout
ALTER TABLE exercise DROP CONSTRAINT exercise_workout_id_fkey;
ALTER TABLE exercise ADD CONSTRAINT exercise_workout_id_fkey
  FOREIGN KEY (workout_id) REFERENCES workout(workout_id) ON DELETE CASCADE;

-- Drop old separate tables (CASCADE removes RLS policies too)
DROP TABLE IF EXISTS cardio CASCADE;
DROP TABLE IF EXISTS strength CASCADE;
```

> ℹ️ If your database is brand new with no data, you can skip the migration and create the tables fresh using the schema in [Section 7](#7-database-schema).

### Run the Server

```bash
uvicorn FastAPImain:app --reload
```

The `--reload` flag restarts the server automatically when you edit files. Remove it in production.

Visit `http://localhost:8000/docs` to open the interactive Swagger UI where you can test every endpoint in the browser.

### Project Structure

```
project/
├── FastAPImain.py             ← App entry point, router registration
├── dependencies.py            ← JWT auth, Supabase client factory
├── DBhelpermethods.py         ← All database operations (FitnessBackend class)
├── schemas.py                 ← Pydantic request/response models
├── ExerciseDBAPImethods.py    ← ExerciseDB (RapidAPI) client
├── OpenFoodFactsAPImethods.py ← Open Food Facts client
├── requirements.txt
├── .env                       ← Your secrets (never commit this)
└── Routers/
    ├── __init__.py
    ├── users.py
    ├── workouts.py
    └── meals.py
```

---

## 2. Authentication

The API uses Supabase Auth. The frontend signs users in directly with Supabase and receives a JWT access token. That token is then sent to FITT on every request as a Bearer token.

**Flow:** Frontend signs in with Supabase → gets JWT → sends JWT in `Authorization` header → FITT validates it → request proceeds.

### Register a New User

`POST /users/` — no token required.

```json
{
  "email": "alex@example.com",
  "password": "MySecret99!",
  "username": "alex",
  "age": 25,
  "gender": "male",
  "weight": 80.5,
  "height": 178.0,
  "experience_level": "intermediate",
  "bmi": 25.4
}
```

**Returns:**
```json
{ "user_id": "...", "username": "alex", "email": "alex@example.com" }
```

### Sign In (get your token)

Sign in via the Supabase client library on the frontend. In JavaScript:

```javascript
const { data } = await supabase.auth.signInWithPassword({
  email: "alex@example.com",
  password: "MySecret99!"
});

const token = data.session.access_token;  // use this as Bearer token
```

### Making Authenticated Requests

Include the token in every request header (except `POST /users/`):

```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

In JavaScript (fetch):

```javascript
const res = await fetch("http://localhost:8000/workouts/", {
  headers: { "Authorization": `Bearer ${token}` }
});
```

> 🔒 Tokens expire. When a request returns `401`, refresh the token using Supabase's session refresh method and retry.

---

## 3. Users — `/users`

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/users/` | Register a new user (no auth required) |
| `GET` | `/users/{user_id}` | Get a user's profile |
| `PATCH` | `/users/{user_id}` | Update profile fields |
| `DELETE` | `/users/{user_id}` | Permanently delete account and all data |

### PATCH /users/{user_id} — Update Profile

Send only the fields you want to change. All fields are optional.

```json
{
  "weight": 82.0,
  "bmi": 25.9,
  "experience_level": "advanced"
}
```

Updatable fields: `age`, `gender`, `weight`, `height`, `experience_level`, `bmi`

---

## 4. Workouts — `/workouts`

Workouts are either `cardio` or `strength`. A cardio workout stores distance and cardio type. A strength workout stores exercises and sets.

### 4.1 Workout CRUD

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/workouts/` | Log a new workout |
| `GET` | `/workouts/` | List workouts (optional date filters) |
| `GET` | `/workouts/{id}` | Get one workout with all exercises & sets |
| `PATCH` | `/workouts/{id}` | Update workout fields |
| `DELETE` | `/workouts/{id}` | Delete workout and all child data |

#### POST /workouts/ — Log a Cardio Workout

```json
{
  "date": "2026-03-09",
  "duration": 45,
  "calories_burned": 420,
  "type": "cardio",
  "cardio_type": "running",
  "distance": 8.5
}
```

**Returns:** `{ "workout_id": 101 }`

#### POST /workouts/ — Log a Strength Workout

```json
{
  "date": "2026-03-09",
  "duration": 60,
  "calories_burned": 350,
  "type": "strength"
}
```

`cardio_type` and `distance` are not needed for strength.

#### GET /workouts/ — List with Optional Date Filters

```
GET /workouts/                                                # all workouts
GET /workouts/?start_date=2026-01-01                          # from Jan 1 onwards
GET /workouts/?end_date=2026-03-09                            # up to today
GET /workouts/?start_date=2026-01-01&end_date=2026-03-09      # specific range
```

### 4.2 Exercises

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/workouts/{id}/exercises` | Add an exercise to a strength workout |
| `GET` | `/workouts/{id}/exercises` | List all exercises for a workout |
| `GET` | `/workouts/{id}/exercises/{ex_id}` | Get one exercise with its sets |
| `PATCH` | `/workouts/{id}/exercises/{ex_id}` | Update exercise name or muscle group |
| `DELETE` | `/workouts/{id}/exercises/{ex_id}` | Delete exercise and all its sets |

#### POST /workouts/{id}/exercises

```json
{
  "name": "Bench Press",
  "muscle_group": "Chest"
}
```

**Returns:** `{ "exercise_id": 55 }`

### 4.3 Sets

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/workouts/{id}/exercises/{ex_id}/sets` | Add a set to an exercise |
| `GET` | `/workouts/{id}/exercises/{ex_id}/sets` | List all sets for an exercise |
| `GET` | `/workouts/{id}/exercises/{ex_id}/sets/{set_id}` | Get one set |
| `PATCH` | `/workouts/{id}/exercises/{ex_id}/sets/{set_id}` | Update set fields |
| `DELETE` | `/workouts/{id}/exercises/{ex_id}/sets/{set_id}` | Delete a set |

#### POST /workouts/{id}/exercises/{ex_id}/sets

```json
{
  "set_num": 1,
  "reps": 10,
  "weight": 80.0,
  "intensity": 7
}
```

Intensity scale: `1` = very light, `10` = max effort.

### 4.4 Workout Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/workouts/{id}/analytics/summary` | Stats for this workout |
| `GET` | `/workouts/{id}/analytics/net-calories` | Calories burned vs consumed on that day |
| `GET` | `/workouts/{id}/analytics/progress/{exercise_name}` | Progress for a named exercise over time |

#### GET /workouts/{id}/analytics/summary — Strength example response

```json
{
  "workout_id": 101,
  "date": "2026-03-09",
  "type": "strength",
  "duration_minutes": 60,
  "calories_burned": 350,
  "total_exercises": 4,
  "total_sets": 16,
  "total_volume_kg": 4800
}
```

#### GET /workouts/{id}/analytics/progress/Bench Press

Returns max weight and total volume per session from the beginning of time up to this workout's date:

```json
[
  { "date": "2026-02-01", "max_weight": 70, "total_volume": 2100, "num_sets": 3 },
  { "date": "2026-03-09", "max_weight": 80, "total_volume": 2400, "num_sets": 3 }
]
```

### 4.5 Exercise Search (ExerciseDB)

These endpoints query the ExerciseDB API on RapidAPI. Requires `EXERCISEDB_API_KEY` in `.env`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/workouts/exercise-search?name=bench` | Search by exercise name |
| `GET` | `/workouts/exercise-search/body-part/{bp}` | Browse by body part |
| `GET` | `/workouts/exercise-search/muscle/{m}` | Browse by target muscle |
| `GET` | `/workouts/exercise-search/equipment/{eq}` | Browse by equipment |
| `POST` | `/workouts/{id}/exercise-search/save` | Save ExerciseDB exercise to workout |

To save an exercise from ExerciseDB into a workout, pass its ExerciseDB ID:

```json
POST /workouts/101/exercise-search/save

{ "exercise_db_id": "0042" }
```

---

## 5. Meals — `/meals`

### 5.1 Meal CRUD

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/meals/` | Log a meal |
| `GET` | `/meals/` | List meals (optional date filters) |
| `GET` | `/meals/{id}` | Get one meal with all food items |
| `PATCH` | `/meals/{id}` | Update meal_num or calories_in |
| `DELETE` | `/meals/{id}` | Delete meal and all food items |

#### POST /meals/ — Log a Meal

```json
{
  "date": "2026-03-09",
  "meal_num": 1,
  "calories_in": 650
}
```

`meal_num` convention: `1` = Breakfast, `2` = Lunch, `3` = Dinner, `4+` = Snacks/Other

**Returns:** `{ "meal_id": 42 }`

#### GET /meals/ — List with Optional Date Filters

```
GET /meals/                                                  # all meals
GET /meals/?start_date=2026-03-01                            # from March 1
GET /meals/?start_date=2026-03-01&end_date=2026-03-09        # specific range
```

### 5.2 Food Items

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/meals/{id}/food` | Add a food item to a meal |
| `GET` | `/meals/{id}/food` | List all food items in a meal |
| `GET` | `/meals/{id}/food/{food_id}` | Get one food item |
| `PATCH` | `/meals/{id}/food/{food_id}` | Update food name, type, or calories |
| `DELETE` | `/meals/{id}/food/{food_id}` | Remove a food item |

#### POST /meals/{id}/food

```json
{
  "name": "Chicken Breast",
  "food_type": "Protein",
  "calories": 280
}
```

### 5.3 Meal Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/meals/{id}/analytics/summary` | Calories total and breakdown by food type |

```json
{
  "meal_id": 42,
  "date": "2026-03-09",
  "meal_num": 1,
  "total_calories": 650,
  "total_food_items": 3,
  "calories_by_type": {
    "Protein": 280,
    "Carbs": 320,
    "Vegetable": 50
  }
}
```

### 5.4 Food Search (Open Food Facts)

These endpoints query the Open Food Facts API — no API key required.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/meals/food-search?query=oats` | Search by food name |
| `GET` | `/meals/food-search/barcode/{barcode}` | Look up product by barcode |
| `POST` | `/meals/{id}/food-search/save-by-barcode` | Scan & log in one call |
| `POST` | `/meals/{id}/food-search/save-by-name` | Log food from search results |

#### POST /meals/{id}/food-search/save-by-barcode

```json
{
  "barcode": "3017624010701",
  "food_type": "Snack",
  "servings": 1.5
}
```

Calories are auto-calculated from Open Food Facts nutrition data and multiplied by `servings`.

#### POST /meals/{id}/food-search/save-by-name

Use this after a search — copy the name and calories directly from a search result:

```json
{
  "name": "Quaker Oats",
  "calories": 370,
  "food_type": "Carbs"
}
```

---

## 6. Error Reference

| Status | Meaning & Fix |
|--------|---------------|
| `401` | Invalid or expired token. Refresh the Supabase session and retry. |
| `400` | Validation error or bad request (e.g. cardio workout missing `distance`). Check the `detail` field in the response body. |
| `404` | Resource not found. The ID does not exist or does not belong to you. |
| `422` | Pydantic validation failed. A required field is missing or the format is wrong (e.g. date not `YYYY-MM-DD`). |
| `502` | Upstream API error (ExerciseDB or Open Food Facts). Check the external service status. |
| `503` | ExerciseDB could not be initialised — `EXERCISEDB_API_KEY` is missing from `.env`. |

---

## 7. Database Schema

```
USER       (id PK uuid, username UK, age, gender, weight, height, experience_level, bmi)

workout    (workout_id PK, username FK→USER, date, duration int,
            calories_burned int, type text CHECK('cardio'|'strength'),
            cardio_type text?, distance float?)

exercise   (exercise_id PK, workout_id FK→workout CASCADE,
            name text, muscle_group text)

SET        (set_id PK, exercise_id FK→exercise CASCADE,
            set_num int, reps int, weight float, intensity int)

meal       (meal_id PK, username FK→USER, date, meal_num int, calories_in int)

food       (food_id PK, meal_id FK→meal CASCADE,
            name text, type text, calories int)
```

All foreign keys use `ON DELETE CASCADE`, so deleting a workout removes its exercises and sets automatically.

---

## 8. Quick-Start Workflow

Here is the typical sequence to log a complete strength workout session from scratch:

1. **Register** — `POST /users/`
2. **Sign in** with Supabase to get your JWT
3. **Log workout** — `POST /workouts/` with `type: strength` → save `workout_id`
4. **Add exercise** — `POST /workouts/{workout_id}/exercises` → save `exercise_id`
5. **Add sets** — `POST /workouts/{workout_id}/exercises/{exercise_id}/sets` (repeat per set)
6. **Log meal** — `POST /meals/` → save `meal_id`
7. **Add food** — `POST /meals/{meal_id}/food` (or use food-search endpoints)
8. **Check analytics** — `GET /workouts/{workout_id}/analytics/summary`

> ✅ Open `http://localhost:8000/docs` and use the Swagger UI to run all of the above interactively without writing any code.
