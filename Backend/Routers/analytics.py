from fastapi import APIRouter, Depends, HTTPException, Query, status
from dependencies import get_backend
from DBhelpermethods import FitnessBackend

router = APIRouter()


def _validate_date_range(start_date: str, end_date: str) -> None:
    """Raises 422 if start_date is after end_date."""
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date must be less than or equal to end_date."
        )


@router.get("/calories/net/{date_string}")
def get_net_calories(date_string: str, backend: FitnessBackend = Depends(get_backend)):
    """
    Returns calories consumed vs burned for a specific date.
    Response: { calories_in, calories_burned, net_calories }
    """
    username = backend.get_username_from_session()
    return backend.get_net_calories(username, date_string)


@router.get("/calories/burned")
def get_total_calories_burned(
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """Returns total calories burned across all workouts in a date range."""
    _validate_date_range(start_date, end_date)
    username = backend.get_username_from_session()
    total = backend.get_total_calories_burned(username, start_date, end_date)
    return {"total_calories_burned": total, "start_date": start_date, "end_date": end_date}


@router.get("/calories/consumed")
def get_total_calories_consumed(
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """Returns total calories consumed across all meals in a date range."""
    _validate_date_range(start_date, end_date)
    username = backend.get_username_from_session()
    total = backend.get_total_calories_consumed(username, start_date, end_date)
    return {"total_calories_consumed": total, "start_date": start_date, "end_date": end_date}


@router.get("/workouts/summary")
def get_workout_summary(
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """
    Returns a workout summary for a date range.
    Includes total workouts, calories burned, duration, and cardio/strength counts.
    """
    _validate_date_range(start_date, end_date)
    username = backend.get_username_from_session()
    return backend.get_workout_summary(username, start_date, end_date)


@router.get("/workouts/average-duration")
def get_average_workout_duration(
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """Returns the average workout duration (minutes) across a date range."""
    _validate_date_range(start_date, end_date)
    username = backend.get_username_from_session()
    avg = backend.get_average_workout_duration(username, start_date, end_date)
    return {"average_duration_minutes": avg, "start_date": start_date, "end_date": end_date}


@router.get("/exercises/progress/{exercise_name}")
def get_exercise_progress(
    exercise_name: str,
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """
    Tracks progress for a specific exercise over time.
    Returns max weight and total volume per session, sorted by date.
    """
    _validate_date_range(start_date, end_date)
    username = backend.get_username_from_session()
    return backend.get_exercise_progress(username, exercise_name, start_date, end_date)


@router.get("/nutrition/summary")
def get_nutrition_summary(
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """
    Returns a nutrition summary for a date range.
    Includes total meals, total calories, average per day and per meal.
    """
    _validate_date_range(start_date, end_date)
    username = backend.get_username_from_session()
    return backend.get_nutrition_summary(username, start_date, end_date)