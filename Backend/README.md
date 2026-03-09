# FITT Backend API

**FITT** is a fitness tracking backend that manages workouts, meals, nutrition, and analytics.

**Local URL:** `http://localhost:8000`  
**Interactive Docs:** `http://localhost:8000/docs`  
**Run command:** `uvicorn FastAPImain:app --reload` (from the `Backend/` folder)

---

## Table of Contents

- [Setup](#setup)
- [Authentication](#authentication)
- [Users](#users)
- [Workouts](#workouts)
- [Exercises](#exercises)
- [Sets](#sets)
- [Meals](#meals)
- [Food](#food)
- [Exercise Search (ExerciseDB)](#exercise-search-exercisedb)
- [Food Search (OpenFoodFacts)](#food-search-openfoodfacts)
- [Groq Chat (FITT AI Assistant)](#groq-chat-fitt-ai-assistant)
- [Analytics](#analytics)
- [Error Handling](#error-handling)
- [Database Schema](#database-schema)

---

## Setup

### Prerequisites
- Python 3.8+
- A Supabase project ([supabase.com](https://supabase.com))
- An ExerciseDB API key ([rapidapi.com](https://rapidapi.com/justin-WFnsXH_t6/api/exercisedb))

### Installation

```bash
cd Backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn FastAPImain:app --reload
```

### Environment Variables

Create a `.env` file inside `Backend/`:

```env
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

EXERCISEDB_API_KEY=your_rapidapi_key
EXERCISEDB_API_HOST=exercisedb.p.rapidapi.com
EXERCISEDB_BASE_URL=https://exercisedb.p.rapidapi.com

GROQ_API_KEY=your_groq_api_key
```
Get a free Groq API key at **https://console.groq.com**

Get Supabase keys from: **Supabase Dashboard → Settings → API**

---

## Authentication

Authentication is handled by **Supabase Auth** directly on the frontend — the backend never issues tokens itself.

### Flow

1. **Sign up** via `POST /users/` (this API)
2. **Sign in** directly with the [Supabase client SDK](https://supabase.com/docs/reference/javascript/auth-signin) on the frontend
3. Supabase returns an `access_token` (JWT)
4. **Include that token** on every protected request:

```
Authorization: Bearer <access_token>
```

All endpoints except `POST /users/` require a valid Bearer token.

### Token Refresh

Handle token refresh with the Supabase client SDK on the frontend — it manages this automatically.

---

## Users

### Create User
```
POST /users/
```
No auth required. Creates both the Supabase auth account and the user profile.

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "securepass123",
  "username": "fituser",
  "age": 25,
  "gender": "male",
  "weight": 75.5,
  "height": 180.0,
  "experience_level": "intermediate",
  "bmi": 23.3
}
```

**Field rules:**
- `password` — min 8 characters
- `username` — 3–30 characters
- `age` — 13–120
- `gender` — `"male"`, `"female"`, or `"other"`
- `weight` — kg, max 700
- `height` — cm, max 300
- `experience_level` — `"beginner"`, `"intermediate"`, or `"advanced"`

**Response `201`:**
```json
{
  "user_id": "uuid-string",
  "username": "fituser",
  "email": "user@example.com"
}
```

---

### Get User Profile
```
GET /users/{user_id}
```
**Response `200`:**
```json
{
  "id": "uuid-string",
  "username": "fituser",
  "age": 25,
  "gender": "male",
  "weight": 75.5,
  "height": 180.0,
  "experience_level": "intermediate",
  "bmi": 23.3
}
```

---

### Update User Profile
```
PATCH /users/{user_id}
```
Only include fields you want to change.

**Request body (all optional):**
```json
{
  "age": 26,
  "weight": 74.0,
  "bmi": 22.8
}
```

---

### Delete User
```
DELETE /users/{user_id}
```
Permanently deletes the account and all associated data. Returns `204 No Content`.

---

## Workouts

A workout has a `type` of either `"cardio"` or `"strength"`. If cardio, `cardio_type` and `distance` are also required.

### Create Workout
```
POST /workouts/
```

**Strength workout:**
```json
{
  "date": "2026-03-01",
  "duration": 60,
  "calories_burned": 400,
  "type": "strength"
}
```

**Cardio workout:**
```json
{
  "date": "2026-03-01",
  "duration": 35,
  "calories_burned": 300,
  "type": "cardio",
  "cardio_type": "running",
  "distance": 5.2
}
```

**Response `201`:**
```json
{ "workout_id": 42 }
```

---

### Get All Workouts
```
GET /workouts/
```
Returns all workouts for the authenticated user, most recent first.

---

### Get Workout by Date
```
GET /workouts/date/{date_string}
```
`date_string` format: `YYYY-MM-DD`

Returns workouts with fully nested exercises and sets.

---

### Get Workouts in Range
```
GET /workouts/range?start_date=2026-01-01&end_date=2026-03-01
```

---

### Get Single Workout
```
GET /workouts/{workout_id}
```
Returns the workout with all nested exercises and sets:
```json
{
  "workout_id": 42,
  "date": "2026-03-01",
  "type": "strength",
  "duration": 60,
  "calories_burned": 400,
  "exercise": [
    {
      "exercise_id": 7,
      "name": "Bench Press",
      "muscle_group": "Chest",
      "SET": [
        { "set_id": 1, "set_num": 1, "reps": 10, "weight": 80.0, "intensity": 7 },
        { "set_id": 2, "set_num": 2, "reps": 8,  "weight": 85.0, "intensity": 8 }
      ]
    }
  ]
}
```

---

### Update Workout
```
PATCH /workouts/{workout_id}
```
**Request body (all optional):**
```json
{
  "duration": 75,
  "calories_burned": 450,
  "cardio_type": "cycling",
  "distance": 18.0
}
```

---

### Delete Workout
```
DELETE /workouts/{workout_id}
```
Cascade deletes all exercises and sets. Returns `204 No Content`.

---

## Exercises

Exercises belong to a strength workout. Each exercise has an array of sets.

### Add Exercise to Workout
```
POST /workouts/{workout_id}/exercises
```
**Request body:**
```json
{
  "name": "Bench Press",
  "muscle_group": "Chest"
}
```
**Response `201`:**
```json
{ "exercise_id": 7 }
```

---

### Get All Exercises for a Workout
```
GET /workouts/{workout_id}/exercises
```

---

### Get Single Exercise
```
GET /workouts/{workout_id}/exercises/{exercise_id}
```
Returns the exercise with its sets array.

---

### Update Exercise
```
PATCH /workouts/{workout_id}/exercises/{exercise_id}
```
```json
{
  "name": "Incline Bench Press",
  "muscle_group": "Upper Chest"
}
```

---

### Delete Exercise
```
DELETE /workouts/{workout_id}/exercises/{exercise_id}
```
Cascade deletes all sets. Returns `204 No Content`.

---

## Sets

Sets belong to an exercise.

### Add Set
```
POST /workouts/{workout_id}/exercises/{exercise_id}/sets
```
**Request body:**
```json
{
  "set_num": 1,
  "reps": 10,
  "weight": 80.0,
  "intensity": 7
}
```
`intensity` is 1–10 (1 = very light, 10 = max effort).

---

### Get All Sets for an Exercise
```
GET /workouts/{workout_id}/exercises/{exercise_id}/sets
```

---

### Get Single Set
```
GET /workouts/{workout_id}/exercises/{exercise_id}/sets/{set_id}
```

---

### Update Set
```
PATCH /workouts/{workout_id}/exercises/{exercise_id}/sets/{set_id}
```
```json
{
  "reps": 12,
  "weight": 82.5,
  "intensity": 8
}
```

---

### Delete Set
```
DELETE /workouts/{workout_id}/exercises/{exercise_id}/sets/{set_id}
```
Returns `204 No Content`.

---

## Meals

### Create Meal
```
POST /meals/
```
**Request body:**
```json
{
  "date": "2026-03-01",
  "meal_num": 1,
  "calories_in": 600
}
```
`meal_num`: 1 = Breakfast, 2 = Lunch, 3 = Dinner, 4+ = Snacks etc.

**Response `201`:**
```json
{ "meal_id": 15 }
```

---

### Get All Meals
```
GET /meals/
GET /meals/?start_date=2026-01-01&end_date=2026-03-01
```

---

### Get Meals by Date
```
GET /meals/date/{date_string}
```
Returns meals with all food items nested inside.

---

### Get Single Meal
```
GET /meals/{meal_id}
```
Returns meal with its food array.

---

### Update Meal
```
PATCH /meals/{meal_id}
```
```json
{
  "calories_in": 750
}
```

---

### Delete Meal
```
DELETE /meals/{meal_id}
```
Cascade deletes all food items. Returns `204 No Content`.

---

## Food

Food items belong to a meal.

### Add Food to Meal
```
POST /meals/{meal_id}/food
```
**Request body:**
```json
{
  "name": "Chicken Breast",
  "food_type": "Protein",
  "calories": 250
}
```

---

### Get All Food for a Meal
```
GET /meals/{meal_id}/food
```

---

### Get Single Food Item
```
GET /meals/{meal_id}/food/{food_id}
```

---

### Update Food Item
```
PATCH /meals/{meal_id}/food/{food_id}
```
```json
{
  "calories": 280
}
```

---

### Delete Food Item
```
DELETE /meals/{meal_id}/food/{food_id}
```
Returns `204 No Content`.

---

## Exercise Search (ExerciseDB)

Search a database of 1300+ exercises. Results include instructions, target muscles, and animated GIF demos. Requires `EXERCISEDB_API_KEY` in `.env`.

### Search by Name
```
GET /workouts/exercise-search?name=bench&limit=10
```

### Browse by Body Part
```
GET /workouts/exercise-search/body-part/chest
```
Valid body parts: `back`, `cardio`, `chest`, `lower arms`, `lower legs`, `neck`, `shoulders`, `upper arms`, `upper legs`, `waist`

### Browse by Target Muscle
```
GET /workouts/exercise-search/muscle/pectorals
```

### Browse by Equipment
```
GET /workouts/exercise-search/equipment/barbell
```

**Example response:**
```json
{
  "count": 3,
  "exercises": [
    {
      "id": "0025",
      "name": "Barbell Bench Press",
      "bodyPart": "chest",
      "target": "pectorals",
      "equipment": "barbell",
      "gifUrl": "https://...",
      "secondaryMuscles": ["triceps", "delts"],
      "instructions": ["Lie on a flat bench...", "..."]
    }
  ]
}
```

### Save Exercise from Search to a Workout
```
POST /workouts/{workout_id}/exercise-search/save
```
Takes an ExerciseDB `id` and saves that exercise directly to the workout.

**Typical flow:**
1. `GET /workouts/exercise-search?name=squat` — user picks a result
2. Copy the `id` field from that result
3. `POST /workouts/{workout_id}/exercise-search/save` with the id

**Request body:**
```json
{ "exercise_db_id": "0025" }
```

**Response `201`:**
```json
{
  "exercise_id": 9,
  "name": "Barbell Bench Press",
  "muscle_group": "Pectorals",
  "equipment": "Barbell",
  "gif_url": "https://...",
  "instructions": ["..."]
}
```

---

## Food Search (OpenFoodFacts)

Search a database of millions of food products. No API key required.

### Search by Name
```
GET /meals/food-search?query=chicken breast&page=1&page_size=10
```

**Example response:**
```json
{
  "count": 150,
  "page": 1,
  "page_size": 10,
  "products": [
    {
      "barcode": "1234567890",
      "name": "Chicken Breast",
      "brand": "Some Brand",
      "serving_size": "100g",
      "nutriscore": "A",
      "calories_per_100g": 165,
      "calories_per_serving": 165,
      "protein_g": 31.0,
      "carbs_g": 0.0,
      "fat_g": 3.6,
      "image_url": "https://..."
    }
  ]
}
```

### Look Up by Barcode
```
GET /meals/food-search/barcode/3017624010701
```
Useful for camera/scanner features.

### Save Food by Barcode to a Meal
```
POST /meals/{meal_id}/food-search/save-by-barcode
```
Fetches the product, auto-calculates calories, and saves to the meal in one call.

**Request body:**
```json
{
  "barcode": "3017624010701",
  "food_type": "Snack",
  "servings": 1.5
}
```

### Save Food by Name to a Meal
```
POST /meals/{meal_id}/food-search/save-by-name
```
Use after searching — user picks a result, you pass the name and calories directly.

**Request body:**
```json
{
  "name": "Chicken Breast",
  "calories": 250,
  "food_type": "Protein"
}
```

---

## Groq Chat (FITT AI Assistant)

AI-powered fitness assistant powered by Groq. Maintains conversation history for multi-turn chat. Requires `GROQ_API_KEY` in `.env` — get a free key at [console.groq.com](https://console.groq.com).

### Send a Message
```
POST /groq/chat
```
**Request body:**
```json
{
  "messages": [
    { "role": "user", "content": "What's a good chest workout?" },
    { "role": "assistant", "content": "Try bench press, push-ups..." },
    { "role": "user", "content": "How many sets should I do?" }
  ]
}
```
Pass the full conversation history each request to maintain context. Each message needs a `role` (`"user"` or `"assistant"`) and `content`.

**Response `200`:**
```json
{
  "response": "For a beginner, 3 sets per exercise is a great starting point..."
}
```



## Analytics

### Net Calories for a Date
```
GET /workouts/analytics/net-calories/2026-03-01
```
**Response:**
```json
{
  "calories_in": 2100,
  "calories_burned": 400,
  "net_calories": 1700
}
```

### Workout Summary
```
GET /workouts/analytics/summary?start_date=2026-02-01&end_date=2026-03-01
```
**Response:**
```json
{
  "total_workouts": 12,
  "total_calories_burned": 4800,
  "total_duration": 720,
  "average_duration": 60.0,
  "cardio_sessions": 4,
  "strength_sessions": 8
}
```

### Total Calories Burned
```
GET /workouts/analytics/calories-burned?start_date=2026-02-01&end_date=2026-03-01
```

### Average Workout Duration
```
GET /workouts/analytics/average-duration?start_date=2026-02-01&end_date=2026-03-01
```

### Exercise Progress Over Time
```
GET /workouts/analytics/progress/Bench Press?start_date=2026-01-01&end_date=2026-03-01
```
Tracks max weight and total volume per session for a specific exercise.

**Response:**
```json
[
  {
    "date": "2026-01-10",
    "workout_id": 5,
    "exercise_id": 3,
    "max_weight": 80.0,
    "total_volume": 2400.0,
    "num_sets": 3
  },
  {
    "date": "2026-01-17",
    "workout_id": 9,
    "exercise_id": 7,
    "max_weight": 85.0,
    "total_volume": 2550.0,
    "num_sets": 3
  }
]
```

### Nutrition Summary
```
GET /meals/analytics/summary?start_date=2026-02-01&end_date=2026-03-01
```
**Response:**
```json
{
  "total_meals": 84,
  "total_calories": 58800,
  "average_calories_per_day": 1960.0,
  "average_calories_per_meal": 700.0
}
```

### Total Calories Consumed
```
GET /meals/analytics/calories-consumed?start_date=2026-02-01&end_date=2026-03-01
```

---

## Error Handling

All errors return JSON with a `detail` field:

```json
{ "detail": "Workout 999 not found." }
```

| Status | Meaning |
|--------|---------|
| `200` | OK |
| `201` | Created |
| `204` | Deleted (no body returned) |
| `400` | Bad request / validation error |
| `401` | Missing or invalid auth token |
| `404` | Resource not found |
| `502` | External API (ExerciseDB / OpenFoodFacts) failed |
| `503` | ExerciseDB API key not configured |

---

## Database Schema

```
USER ||--o{ WORKOUT : performs
USER ||--o{ MEAL    : eats

WORKOUT  ||--o{ EXERCISE : includes
EXERCISE ||--o{ SET      : records

MEAL ||--o{ FOOD : consists_of
```

| Table | Key Fields |
|-------|-----------|
| `USER` | `id` (UUID), `username`, `age`, `gender`, `weight`, `height`, `experience_level`, `bmi` |
| `WORKOUT` | `workout_id`, `username` (FK), `date`, `duration`, `calories_burned`, `type`, `cardio_type`*, `distance`* |
| `EXERCISE` | `exercise_id`, `workout_id` (FK), `name`, `muscle_group` |
| `SET` | `set_id`, `exercise_id` (FK), `set_num`, `reps`, `weight`, `intensity` |
| `MEAL` | `meal_id`, `username` (FK), `date`, `meal_num`, `calories_in` |
| `FOOD` | `food_id`, `meal_id` (FK), `name`, `type`, `calories` |

*`cardio_type` and `distance` are only populated when `workout.type = 'cardio'`