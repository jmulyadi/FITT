from fastapi import APIRouter, Depends, HTTPException, status, Query
from dependencies import get_backend
from schemas import WorkoutCreate, WorkoutUpdate
from DBhelpermethods import FitnessBackend

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
def add_workout(body: WorkoutCreate, backend: FitnessBackend = Depends(get_backend)):
    """Logs a new workout session. Returns the new workout_id."""
    username = backend.get_username_from_session()
    workout_id = backend.add_workout(username, body.date, body.duration, body.calories_burned)
    return {"workout_id": workout_id}


@router.get("/")
def get_all_workouts(backend: FitnessBackend = Depends(get_backend)):
    """Returns all workouts for the current user, most recent first."""
    username = backend.get_username_from_session()
    return backend.get_all_workouts(username)


@router.get("/date/{date_string}")
def get_workouts_by_date(date_string: str, backend: FitnessBackend = Depends(get_backend)):
    """Returns all workouts on a specific date (YYYY-MM-DD) with full cardio/strength details."""
    username = backend.get_username_from_session()
    return backend.get_workouts_by_date(username, date_string)


@router.get("/range")
def get_workouts_in_range(
    start_date: str = Query(description="Start date YYYY-MM-DD"),
    end_date: str = Query(description="End date YYYY-MM-DD"),
    backend: FitnessBackend = Depends(get_backend)
):
    """Returns all workouts between two dates (inclusive), most recent first."""
    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_date must be less than or equal to end_date."
        )
    username = backend.get_username_from_session()
    return backend.get_workouts_in_range(username, start_date, end_date)


@router.get("/{workout_id}")
def get_workout(workout_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Returns a single workout with all associated cardio and strength data."""
    try:
        return backend.get_workout_by_id(workout_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch("/{workout_id}")
def update_workout(
    workout_id: int,
    body: WorkoutUpdate,
    backend: FitnessBackend = Depends(get_backend)
):
    """Updates date, duration, or calories_burned on a workout."""
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields provided for update."
        )
    try:
        username = backend.get_username_from_session()
        backend.verify_workout_ownership(username, workout_id)
        return backend.update_workout(workout_id, **updates)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(workout_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Deletes a workout and all its associated cardio, strength, exercises, and sets."""
    try:
        username = backend.get_username_from_session()
        backend.verify_workout_ownership(username, workout_id)
        backend.delete_workout(workout_id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))