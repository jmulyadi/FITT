from pydantic import BaseModel, EmailStr, Field
from typing import Optional


# ============================================================================
# USER SCHEMAS
# ============================================================================

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    username: str = Field(min_length=3, max_length=30)
    age: int = Field(ge=13, le=120)
    gender: str = Field(pattern="^(male|female|other)$")
    weight: float = Field(gt=0, le=700)
    height: float = Field(gt=0, le=300)
    experience_level: str = Field(pattern="^(beginner|intermediate|advanced)$")
    bmi: float = Field(gt=0, le=100)


class UpdateProfileRequest(BaseModel):
    age: Optional[int] = Field(default=None, ge=13, le=120)
    gender: Optional[str] = Field(default=None, pattern="^(male|female|other)$")
    weight: Optional[float] = Field(default=None, gt=0, le=700)
    height: Optional[float] = Field(default=None, gt=0, le=300)
    experience_level: Optional[str] = Field(default=None, pattern="^(beginner|intermediate|advanced)$")
    bmi: Optional[float] = Field(default=None, gt=0, le=100)


# ============================================================================
# WORKOUT SCHEMAS
# ============================================================================

class WorkoutCreate(BaseModel):
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$", description="YYYY-MM-DD")
    duration: int = Field(gt=0, le=1440, description="Duration in minutes")
    calories_burned: int = Field(ge=0, le=10000)
    type: str = Field(pattern="^(cardio|strength)$", description="'cardio' or 'strength'")
    cardio_type: Optional[str] = Field(default=None, min_length=2, max_length=50,
                                        description="Required if type is cardio. e.g. running, cycling")
    distance: Optional[float] = Field(default=None, gt=0, le=1000,
                                       description="Required if type is cardio. Distance in km")


class WorkoutUpdate(BaseModel):
    date: Optional[str] = Field(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    duration: Optional[int] = Field(default=None, gt=0, le=1440)
    calories_burned: Optional[int] = Field(default=None, ge=0, le=10000)
    cardio_type: Optional[str] = Field(default=None, min_length=2, max_length=50)
    distance: Optional[float] = Field(default=None, gt=0, le=1000)


# ============================================================================
# EXERCISE SCHEMAS
# ============================================================================

class ExerciseCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100, description="e.g. Bench Press, Squat")
    muscle_group: str = Field(min_length=2, max_length=50, description="e.g. Chest, Legs")


class ExerciseUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    muscle_group: Optional[str] = Field(default=None, min_length=2, max_length=50)


# ============================================================================
# SET SCHEMAS
# ============================================================================

class SetCreate(BaseModel):
    set_num: int = Field(ge=1, le=100)
    reps: int = Field(ge=1, le=1000)
    weight: float = Field(ge=0, le=2000, description="Weight in kg")
    intensity: int = Field(ge=1, le=10, description="1=very light, 10=max effort")


class SetUpdate(BaseModel):
    set_num: Optional[int] = Field(default=None, ge=1, le=100)
    reps: Optional[int] = Field(default=None, ge=1, le=1000)
    weight: Optional[float] = Field(default=None, ge=0, le=2000)
    intensity: Optional[int] = Field(default=None, ge=1, le=10)


# ============================================================================
# MEAL SCHEMAS
# ============================================================================

class MealCreate(BaseModel):
    date: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}$", description="YYYY-MM-DD")
    meal_num: int = Field(ge=1, le=10, description="1=Breakfast, 2=Lunch, 3=Dinner, etc.")
    calories_in: int = Field(ge=0, le=10000)


class MealUpdate(BaseModel):
    meal_num: Optional[int] = Field(default=None, ge=1, le=10)
    calories_in: Optional[int] = Field(default=None, ge=0, le=10000)


# ============================================================================
# FOOD SCHEMAS
# ============================================================================

class FoodCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100, description="e.g. Chicken Breast")
    food_type: str = Field(min_length=1, max_length=50, description="e.g. Protein, Carbs, Vegetable")
    calories: int = Field(ge=0, le=5000)


class FoodUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    food_type: Optional[str] = Field(default=None, min_length=1, max_length=50)
    calories: Optional[int] = Field(default=None, ge=0, le=5000)