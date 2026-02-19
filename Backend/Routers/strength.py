from fastapi import APIRouter, Depends, HTTPException, status
from dependencies import get_backend
from DBhelpermethods import FitnessBackend

router = APIRouter()


@router.post("/{workout_id}", status_code=status.HTTP_201_CREATED)
def add_strength_session(workout_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Creates a strength training record for an existing workout."""
    try:
        username = backend.get_username_from_session()
        backend.verify_workout_ownership(username, workout_id)
        return backend.add_strength_session(workout_id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/workout/{workout_id}")
def get_strength_by_workout(workout_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Returns the strength session for a workout, including all exercises and sets."""
    try:
        return backend.get_strength_by_workout(workout_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/date/{date_string}")
def get_strength_by_date(date_string: str, backend: FitnessBackend = Depends(get_backend)):
    """Returns all strength workouts on a specific date (YYYY-MM-DD) with exercises and sets."""
    username = backend.get_username_from_session()
    return backend.get_strength_workouts_by_date(username, date_string)


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_strength_session(workout_id: int, backend: FitnessBackend = Depends(get_backend)):
    """Removes a strength session and all its exercises and sets."""
    try:
        username = backend.get_username_from_session()
        backend.verify_workout_ownership(username, workout_id)
        backend.delete_strength_session(workout_id)
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))