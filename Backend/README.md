# FITT Backend API Documentation

**FITT** is a comprehensive fitness tracking backend that manages workouts, meals, nutrition, strength training, cardio, and analytics for fitness enthusiasts.

TO RUN: PYTHONPATH=Backend python3 -m uvicorn Backend.FastAPImain:app --reload
TO VIEW: http://127.0.0.1:8000/docs
---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Setup Instructions](#setup-instructions)
- [Environment Variables](#environment-variables)
- [API Endpoints](#api-endpoints)
- [Authentication](#authentication)
- [Request/Response Examples](#requestresponse-examples)
- [Database Schema](#database-schema)
- [Error Handling](#error-handling)


---

## Overview

The FITT backend is a **FastAPI** application that provides RESTful endpoints for managing:
- **User authentication** and profile management
- **Workout tracking** (strength training, cardio)
- **Exercise data** (custom and external database)
- **Meal tracking** and nutrition logging
- **Analytics** on fitness progress
- **Integration with external APIs** (ExerciseDB, OpenFoodFacts)

**API Base URL:** 
- Local: `http://localhost:8000`
- Production: (set via `ALLOWED_ORIGINS` env variable)

**API Documentation:** `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc` (ReDoc)

---

## Tech Stack

| Component | Version |
|-----------|---------|
| **Framework** | FastAPI 0.115.0 |
| **Server** | Uvicorn 0.30.6 |
| **Database** | Supabase (PostgreSQL) |
| **Authentication** | Supabase Auth (JWT) |
| **Validation** | Pydantic 2.8.2 |
| **HTTP Client** | Requests 2.32.3 |

---

## Setup Instructions

### Prerequisites
- Python 3.8+
- Supabase account and project created

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the `Backend/` directory (see [Environment Variables](#environment-variables))

5. **Run the server:**
   ```bash
   uvicorn FastAPImain:app --reload --host 0.0.0.0 --port 8000
   ```

The API will be available at `http://localhost:8000`

---

## Environment Variables

Create a `.env` file in the `Backend/` directory with the following variables:

```env
# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

EXERCISEDB_API_KEY
EXERCISEDB_API_HOST=exercisedb.p.rapidapi.com
EXERCISEDB_BASE_URL=https://exercisedb.p.rapidapi.com

```

**Getting Supabase Keys:**
1. Go to [supabase.com](https://supabase.com) and create a project
2. Navigate to **Settings → API**
3. Copy the URL and keys into your `.env` file

---

## API Endpoints

### Authentication Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/signup` | Register a new user |
| `POST` | `/auth/signin` | Login with email & password |
| `POST` | `/auth/refresh` | Refresh JWT token |
| `POST` | `/auth/reset-password` | Request password reset |
| `POST` | `/auth/update-password` | Update user password |

### User Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/users/{user_id}` | Get user profile |
| `PUT` | `/users/{user_id}` | Update user profile |
| `DELETE` | `/users/{user_id}` | Delete user account |

### Workout Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/workouts` | Get all workouts for user |
| `GET` | `/workouts/{workout_id}` | Get specific workout |
| `POST` | `/workouts` | Create a new workout |
| `PUT` | `/workouts/{workout_id}` | Update workout |
| `DELETE` | `/workouts/{workout_id}` | Delete workout |

### Strength Training Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/strength` | Get all strength workouts |
| `POST` | `/strength` | Create strength workout |
| `PUT` | `/strength/{strength_id}` | Update strength workout |
| `DELETE` | `/strength/{strength_id}` | Delete strength workout |

### Cardio Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/cardio` | Get all cardio workouts |
| `POST` | `/cardio` | Create cardio workout |
| `PUT` | `/cardio/{cardio_id}` | Update cardio workout |
| `DELETE` | `/cardio/{cardio_id}` | Delete cardio workout |

### Exercise Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/exercises` | Get all exercises |
| `GET` | `/exercises/{exercise_id}` | Get specific exercise |
| `POST` | `/exercises` | Create custom exercise |
| `PUT` | `/exercises/{exercise_id}` | Update exercise |
| `DELETE` | `/exercises/{exercise_id}` | Delete exercise |

### Sets Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/sets` | Get all sets |
| `POST` | `/sets` | Create a new set |
| `PUT` | `/sets/{set_id}` | Update set |
| `DELETE` | `/sets/{set_id}` | Delete set |

### Meals Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/meals` | Get all meals |
| `GET` | `/meals/{meal_id}` | Get specific meal |
| `POST` | `/meals` | Create a new meal |
| `PUT` | `/meals/{meal_id}` | Update meal |
| `DELETE` | `/meals/{meal_id}` | Delete meal |

### Food Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/food` | Get all food items |
| `GET` | `/food/{food_id}` | Get specific food |
| `POST` | `/food` | Add custom food item |
| `PUT` | `/food/{food_id}` | Update food item |
| `DELETE` | `/food/{food_id}` | Delete food item |

### Search Endpoints (External APIs)
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/exercise-search?q={query}` | Search ExerciseDB for exercises |
| `GET` | `/food-search?q={query}` | Search OpenFoodFacts for food items |

### Analytics Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/analytics/workout-summary` | Get workout statistics |
| `GET` | `/analytics/nutrition-summary` | Get nutrition statistics |
| `GET` | `/analytics/progress` | Get user progress metrics |

---

## Authentication

The API uses **JWT (JSON Web Token)** based authentication via Supabase.

### How to Authenticate

1. **Sign Up / Sign In:**
   ```bash
   POST /auth/signup
   POST /auth/signin
   ```
   Returns: `access_token`, `refresh_token`, `user_id`

2. **Include Token in Requests:**
   Add the `access_token` to the `Authorization` header:
   ```
   Authorization: Bearer <access_token>
   ```

3. **Refresh Token:**
   When token expires, use the `refresh_token`:
   ```bash
   POST /auth/refresh
   ```

### Protected Routes

All endpoints except `/auth/signup`, `/auth/signin`, `/exercise-search`, and `/food-search` require authentication.

---

## Request/Response Examples

### Sign Up

**Request:**
```bash
curl -X POST "http://localhost:8000/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "securepass123",
    "username": "fituser",
    "age": 25,
    "gender": "male",
    "weight": 75.5,
    "height": 180,
    "experience_level": "intermediate",
    "bmi": 23.3
  }'
```

**Response:**
```json
{
  "user_id": "abc123xyz",
  "username": "fituser",
  "email": "user@example.com",
  "access_token": "eyJhbGc...",
  "refresh_token": "refresh_...",
  "expires_in": 3600
}
```

### Create Workout

**Request:**
```bash
curl -X POST "http://localhost:8000/workouts" \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Leg Day",
    "date": "2024-02-19",
    "duration_minutes": 60,
    "notes": "Great workout!"
  }'
```

**Response:**
```json
{
  "id": "workout_123",
  "user_id": "abc123xyz",
  "name": "Leg Day",
  "date": "2024-02-19",
  "duration_minutes": 60,
  "notes": "Great workout!"
}
```

### Search Exercises

**Request:**
```bash
curl -X GET "http://localhost:8000/exercise-search?q=squat"
```

**Response:**
```json
{
  "exercises": [
    {
      "id": "ex_001",
      "name": "Barbell Back Squat",
      "muscle_group": "Legs",
      "difficulty": "Intermediate",
      "instructions": "...",
      "equipment": "Barbell"
    },
  ]
}
```

### Get User Analytics

**Request:**
```bash
curl -X GET "http://localhost:8000/analytics/workout-summary" \
  -H "Authorization: Bearer <access_token>"
```

**Response:**
```json
{
  "total_workouts": 24,
  "total_duration_minutes": 1440,
  "average_workout_duration": 60,
  "workouts_this_week": 5,
  "last_workout": "2024-02-19"
}
```

---

## Database Schema

### Main Tables

| Table | Description |
|-------|-------------|
| `USER` | User profiles with fitness metrics |
| `WORKOUT` | Workout sessions |
| `STRENGTH` | Strength training sessions |
| `CARDIO` | Cardio sessions |
| `EXERCISE` | Exercise definitions |
| `SETS` | Sets within strength workouts |
| `MEAL` | Meal records |
| `FOOD` | Food/nutrition items |

For detailed schema, see `ER Diagram.txt`

### User Profile Fields
- `id` (UUID) - User ID from Supabase Auth
- `username` (string) - Unique username
- `email` (string) - User email
- `age` (integer)
- `gender` (male|female|other)
- `weight` (float) - in kg
- `height` (float) - in cm
- `experience_level` (beginner|intermediate|advanced)
- `bmi` (float)
- `created_at` (timestamp)
- `updated_at` (timestamp)

---

## Error Handling

The API returns standard HTTP status codes and error messages:

| Status Code | Meaning |
|-------------|---------|
| `200` | OK - Successful request |
| `201` | Created - Resource created successfully |
| `400` | Bad Request - Invalid input |
| `401` | Unauthorized - Missing or invalid token |
| `403` | Forbidden - Insufficient permissions |
| `404` | Not Found - Resource doesn't exist |
| `500` | Internal Server Error |

### Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Errors

**Missing Authentication Token:**
```json
{
  "detail": "Not authenticated"
}
```

**Invalid Email Format:**
```json
{
  "detail": "Invalid email format"
}
```

**Weak Password:**
```json
{
  "detail": "Password must be at least 8 characters"
}
```

---

